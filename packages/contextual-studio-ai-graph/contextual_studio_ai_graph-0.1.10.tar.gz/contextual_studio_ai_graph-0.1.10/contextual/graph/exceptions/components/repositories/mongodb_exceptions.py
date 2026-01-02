"""Exception types used by the contextual graph package."""


class MongoDBException(Exception):
    """Base exception for Supabase-related errors."""

    pass


class MongoDBConnectionException(MongoDBException):
    """Custom exception raised when there is an issue connecting to MongoDB.

    Triggers when dealing with invalid service and/ or anon keys.

    Attributes:
        message (str): A detailed error message describing the connection issue.
    """

    def __init__(self, message: str):
        """Initialize the exception with a message.

        Args:
            message (str): Details regarding the connection failure.
        """
        super().__init__(f"MongoDB connection error: {message}")


class MongoDBDatabaseException(MongoDBException):
    """Raised when a required database name is missing or invalid."""

    def __init__(self, message: str):
        """Initialize the exception with a message.

        Args:
            message (str): Details regarding the database access failure.
        """
        super().__init__(f"MongoDB database error: {message}")


class MongoDBCollectionException(MongoDBException):
    """Raised when a required collection name is missing or invalid."""

    def __init__(self, message: str):
        """Initialize the exception with a message.

        Args:
            message (str): Details regarding the collection access failure.
        """
        super().__init__(f"MongoDB collection error: {message}")


class MongoDBCollectionNotFoundException(MongoDBException):
    """Raised when a required collection name is missing from the database."""

    def __init__(self, message: str):
        """Initialize the exception with a message.

        Args:
            message (str): Details regarding the collection access failure.
        """
        super().__init__(f"MongoDB collection was not found in the database: {message}")
