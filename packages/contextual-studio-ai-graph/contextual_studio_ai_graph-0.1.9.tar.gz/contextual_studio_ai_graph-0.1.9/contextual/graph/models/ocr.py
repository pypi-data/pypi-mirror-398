from pydantic import BaseModel, Field


class Page(BaseModel):
    content: str = Field(description="Extracted text content of the page.")
    content_length: int = Field(description="Number of characters in the extracted content.")
    page: int = Field(description="Page number in the original document.")


class OCROutput(BaseModel):
    completion_time: float = Field(description="Total processing time in seconds.")
    file_name: str = Field(description="Original name of the uploaded file.")
    input_tokens: int = Field(description="Number of tokens used in the input prompt.")
    output_tokens: int = Field(description="Number of tokens generated in the output.")
    pages: list[Page] = Field(description="List of pages containing extracted content.")
