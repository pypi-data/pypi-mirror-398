"""Metadata payloads for document insertion."""

from pydantic import BaseModel, ConfigDict


class InsertMetaData(BaseModel):
    """Extensible metadata class for the insertion of a document."""

    content_hash: str
    document_id: str
    page: int

    # Necessary to allow extra fields for extensibility
    model_config = ConfigDict(extra="allow")
