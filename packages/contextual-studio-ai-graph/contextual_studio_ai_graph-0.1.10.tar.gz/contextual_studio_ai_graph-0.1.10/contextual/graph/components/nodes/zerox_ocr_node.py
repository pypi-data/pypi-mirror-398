from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field

from ...models import State
from ..observability.tracer_interface import BaseExecutionTracer
from ..ocr import ZeroxOCR
from .base import BaseNode


class ZeroxOCRNode(BaseNode):
    """Node that extracts text from a file using ZeroxOCR."""

    ocr_service: ZeroxOCR = Field(..., description="The OCR service to use.")

    async def process(
        self, state: State, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extracts text from the file in the state.

        Args:
            state: The input State object, expected to contain `file_path`.
            config: Optional runtime configuration passed by the graph.

        Returns:
            A dictionary containing the `text` field.
        """

        if not state.file_path:
            return {}

        tracer: Optional[BaseExecutionTracer] = None
        # Try to get tracer from the wrapper if it exists (injected dynamically) or from config
        if hasattr(self, "_tracer"):
            tracer = getattr(self, "_tracer")

        async def on_page_completed(
            page_num: int, status: str, message: Optional[str], stats: Dict[str, Any]
        ) -> None:
            if not tracer or not state.execution_id:
                return

            log_key = f"OCR_PAGE_{page_num}"

            await tracer.log_step(
                execution_id=state.execution_id,
                step_name=log_key,
                status=status,
                error=message,  # Pass warning/error message here
                metadata=stats,
            )

        try:
            # Run OCR
            output = await self.ocr_service.extract(
                file_path=Path(state.file_path),
                ocr_custom_prompt=state.ocr_custom_prompt,
                maintain_format=state.maintain_format,
                on_page_completed=on_page_completed,
            )

            # Concatenate content from all pages
            extracted_text = "\n".join([page.content for page in output.pages])

            return {"text": extracted_text}
        except Exception as e:
            print(f"CRITICAL OCR ERROR: {e}")
            import traceback

            traceback.print_exc()
            raise
