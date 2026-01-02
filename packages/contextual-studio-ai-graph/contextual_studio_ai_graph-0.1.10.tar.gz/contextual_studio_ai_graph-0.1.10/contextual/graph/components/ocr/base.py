from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import Field

from ...exceptions.components.ocr import OCRException
from ...models import OCRConfig, OCROutput
from ..base import BaseComponent

T = TypeVar("T")


class OCR(BaseComponent, ABC, Generic[T]):
    """Abstract base class for components that extract text from files."""

    config: OCRConfig = Field(..., description="Extractor text configuration")

    async def extract(
        self,
        *,
        file_path: Path,
        ocr_custom_prompt: str | None = None,
        output_dir: Path | None = None,
        maintain_format: bool = False,
        **kwargs: Any,
    ) -> OCROutput:
        """Run the extraction template method and convert the result to public output.

        Public template method.

        Args:
            file_path: Path to the input file.
            ocr_custom_prompt: Optional prompt that overrides the configured prompt.
            output_dir: Directory where intermediate or output artifacts are written.
            maintain_format: Whether to maintain the format from the previous page, defaults to False.

        Returns:
            OCROutput: Structured result returned to consumers.

        Raises:
            OCRException: Raised when the underlying extractor fails.
        """
        try:
            result: T = await self._extract(
                file_path=file_path,
                ocr_custom_prompt=ocr_custom_prompt,
                output_dir=output_dir,
                maintain_format=maintain_format,
                **kwargs,
            )
            self._process(result)
            output: OCROutput = self._to_extracted_output(result)
        except Exception as e:
            error_message: str = (
                f"{str(self.__class__)} error. Possibly invalid API key or other error."
            )
            raise OCRException(message=error_message, cause=e)
        return output

    @abstractmethod
    async def _extract(
        self,
        *,
        file_path: Path,
        ocr_custom_prompt: str | None = None,
        output_dir: Path | None = None,
        maintain_format: bool = False,
        **kwargs: Any,
    ) -> T:
        """Extract text using a prompt and return the raw extractor-specific result.

        Private abstract method that should be implmented in the sub classes.


        Args:
            file_path: Path to the input file.
            ocr_custom_prompt: Optional prompt that overrides the configured prompt.
            output_dir: Directory where intermediate or output artifacts are written.
            maintain_format: Whether to maintain the format from the previous page, defaults to False.

        Returns:
            T: Raw extraction payload produced by the backend.
        """
        pass

    def _process(self, result: T) -> None:
        """Hook invoked after `_extract` to mutate or enrich the raw result.

        Args:
            result: Raw extraction payload produced by `_extract`.
        """
        pass

    @abstractmethod
    def _to_extracted_output(self, result: T) -> OCROutput:
        """Convert the processed result into the shared `OCROutput` extractor_schema.

        Args:
            result: Processed extraction payload ready for serialization.

        Returns:
            OCROutput: Canonical representation used throughout the graph.
        """
        pass
