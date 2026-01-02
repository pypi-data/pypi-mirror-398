from typing import Any, Dict

from bson import ObjectId
from pydantic import Field

from contextual.graph.components.repositories import MongoDBRepository
from contextual.graph.exceptions.components.repositories.mongodb_exceptions import (
    MongoDBCollectionNotFoundException,
)
from contextual.graph.models import FilterSchema, ModelSchemaExtractor

from .base_schema import SchemaExtractor


class SchemaExtractorMongoDB(SchemaExtractor):
    """Schema extractor implementation that retrieves extractor_schema definitions from a MongoDB repository.

    This class uses a CRUDRepository to fetch and construct structured extractor_schema objects
    for downstream data extraction tasks.
    """

    repository: MongoDBRepository = Field(
        ..., description="Repository for accessing extractor_schema definitions."
    )

    async def extract(
        self, filters: FilterSchema, **kwargs: Dict[str, Any]
    ) -> ModelSchemaExtractor:
        """Asynchronously extracts an extractor_schema object based on an extractor_schema identifier.

        Uses the repository to retrieve extractor_schema data and builds a `ModelSchemaExtractor` instance.

        Args:
            filters (FilterSchema): Filters to get data.
            **kwargs (Dict[str, Any]): Additional parameters for extractor_schema extraction (currently unused).

        Returns:
            ModelSchemaExtractor: The structured extractor_schema extractor instance.

        Raises:
            MongoDBCollectionNotFound: The collection was not found in the database.
        """
        filter_dict = filters.model_dump()

        # Convert _id to ObjectId if it's a string
        if "_id" in filter_dict and isinstance(filter_dict["_id"], str):
            try:
                filter_dict["_id"] = ObjectId(filter_dict["_id"])
            except Exception:
                # If conversion fails, leave it as is (might be intended)
                pass

        collection_filtered = await self.repository.async_read(filters=filter_dict)
        if collection_filtered is None or len(collection_filtered) == 0:
            raise MongoDBCollectionNotFoundException(
                "The collection was not found as the result list is empty."
            )
        result: Dict[str, Any] = collection_filtered[0]
        return ModelSchemaExtractor.create(id_schema=filters.id, raw_data=result)
