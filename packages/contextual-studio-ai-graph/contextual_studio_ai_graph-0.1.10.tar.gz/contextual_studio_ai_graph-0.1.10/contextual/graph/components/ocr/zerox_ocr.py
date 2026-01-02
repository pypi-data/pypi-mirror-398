from pathlib import Path
from typing import Any

from pyzerox import zerox
from pyzerox.core.types import ZeroxOutput

from ...models import OCROutput, Page
from .base import OCR


class ZeroxOCR(OCR[ZeroxOutput]):

    async def _extract(
        self,
        file_path: Path,
        ocr_custom_prompt: str | None = None,
        output_dir: Path | None = None,
        maintain_format: bool = False,
        **kwargs: Any,
    ) -> ZeroxOutput:
        """Extract text using a prompt and return the raw extractor-specific result.

        Private abstract method that should be implmented in the sub classes.

        Args:
            file_path: Path to the input file.
            ocr_custom_prompt: Optional prompt that overrides the configured prompt.
            output_dir: Directory where intermediate or output artifacts are written.
            maintain_format: Whether to maintain the format from the previous page, defaults to False.

        Returns:
            ZeroxOutput: Raw extraction payload produced by the backend.
        """
        return await zerox(
            file_path=str(file_path.resolve()),
            model=self.config.llm.model_name,
            output_dir=output_dir,
            select_pages=None,
            custom_system_prompt=ocr_custom_prompt,
            maintain_format=maintain_format,
            concurrency=10,
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_CIVIC_INTEGRITY",
                    "threshold": "BLOCK_NONE",
                },
            ],
            **kwargs,
        )

    def _to_extracted_output(self, result: ZeroxOutput) -> OCROutput:
        """Convert the processed result into the shared `OCROutput` extractor_schema.

        Args:
            result: Processed extraction payload ready for serialization.

        Returns:
            OCROutput: Canonical representation used throughout the graph.
        """
        return OCROutput(
            completion_time=result.completion_time,
            file_name=result.file_name,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            pages=[
                Page(content=p.content, content_length=len(p.content), page=i + 1)
                for i, p in enumerate(result.pages)
            ],
        )
