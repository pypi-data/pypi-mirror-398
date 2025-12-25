from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field

from ...models import State
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

        try:
            # Run OCR
            output = await self.ocr_service.extract(
                file_path=Path(state.file_path),
                ocr_custom_prompt=state.ocr_custom_prompt,
                maintain_format=state.maintain_format,
            )

            # Concatenate content from all pages
            extracted_text = "\n".join([page.content for page in output.pages])

            return {"text": extracted_text}
        except Exception:
            raise
