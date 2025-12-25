from pymongo import MongoClient
from pymongo.collection import Collection

from ..models import MongoDBConfig


def get_mongo_collection(client: MongoClient, config: MongoDBConfig) -> Collection:
    """Extracts a pymongo Collection instance using the client and configuration.

    Args:
        client: The initialized MongoClient.
        config: The MongoDBConfig object containing DB and collection names.

    Returns:
        The pymongo Collection.
    """
    db_name = config.database_name
    collection_name = config.collection

    database = client[db_name]
    collection = database[collection_name]

    return collection
