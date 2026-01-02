"""Utility for constructing MongoDB client instances."""

from typing import Any, Optional

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from ...models import DataSchemaConfig


class MongoDBClientFactory:
    """Factory class for building a MongoClient instance for MongoDB."""

    @staticmethod
    def create(
        config: DataSchemaConfig,
        server_api: Optional[ServerApi] = None,
        **kwargs: Any,
    ) -> MongoClient:
        """Builds and returns a configured instance of the MongoClient.

        Args:
            config (DataSchemaConfig): Application configuration that carries MongoDB credentials.
            server_api (Optional[ServerApi]): The ServerApi to use (defaults to ServerApi('1')).
            **kwargs: Additional keyword arguments passed directly to pymongo.MongoClient.

        Returns:
            MongoClient: Configured MongoDB client.

        Raises:
            ValueError: If the required MongoDB URI is missing.
        """
        # 1. Get URI from config, falling back to environment variable
        uri = str(config.mongodb.uri.get_secret_value())

        if not uri:
            raise ValueError(
                "MongoDB URI not defined in application configuration or 'MONGODB_URI' environment variable."
            )

        # 2. Set default server API if not explicitly provided
        if server_api is None:
            # Setting ServerApi('1') is recommended for modern MongoDB deployments
            server_api = ServerApi("1")
        (uri)
        # 3. Create and return the MongoClient instance
        return MongoClient(uri, server_api=server_api, **kwargs)
