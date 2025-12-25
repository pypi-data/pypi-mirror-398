"""Pydantic model describing MongoDB configuration."""

from pydantic import BaseModel, Field, SecretStr, model_validator

from ..exceptions.components.repositories.mongodb_exceptions import (
    MongoDBCollectionException,
    MongoDBConnectionException,
    MongoDBDatabaseException,
)


class MongoDBConfig(BaseModel):
    """Configuration model for connecting to a MongoDB cluster or instance.

    Uses SecretStr for the URI to securely handle credentials.
    """

    uri: SecretStr = Field(description="The password for the MongoDB instance.")
    database_name: str | None = Field(None, description="Default database name to retrieve.")
    collection: str | None = Field(None, description="Configuration for the default collection.")

    @model_validator(mode="after")
    def validate_required_fields(self) -> "MongoDBConfig":
        """Validate that URI and database_name are provided and not empty."""

        if not self.uri.get_secret_value():
            raise MongoDBConnectionException(
                "The MongoDB URI must be provided and cannot be empty."
            )

        if not self.database_name:
            raise MongoDBDatabaseException("Database name (database_name) must be provided.")

        if not self.collection:
            raise MongoDBCollectionException(
                "The 'collection' configuration object must be provided."
            )

        return self
