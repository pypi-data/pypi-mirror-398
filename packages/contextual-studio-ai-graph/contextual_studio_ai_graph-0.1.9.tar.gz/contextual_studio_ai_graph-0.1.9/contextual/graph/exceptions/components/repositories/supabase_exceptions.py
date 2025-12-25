"""Exception types used by the contextual graph package."""


class SupabaseException(Exception):
    """Base exception for Supabase-related errors."""

    pass


class SupabaseConnectionException(SupabaseException):
    """Custom exception raised when there is an issue connecting to Supabase.

    Triggers when dealing with invalid service and/ or anon keys.

    Attributes:
        message (str): A detailed error message describing the connection issue.
    """

    def __init__(self, message: str):
        """Initialize the exception with a message.

        Args:
            message (str): Details regarding the connection failure.
        """
        super().__init__(f"Supabase connection error: {message}")


class SupabaseCRUDException(SupabaseException):
    """Custom exception raised when a CRUD operation with Supabase fails.

    Attributes:
        operation (str): The type of CRUD operation (e.g. 'create', 'read', 'update', 'delete').
        message (str): A detailed error message.
    """

    def __init__(self, operation: str, message: str):
        """Initialize the exception for a specific CRUD operation.

        Args:
            operation (str): CRUD operation name.
            message (str): Details regarding the failure.
        """
        super().__init__(f"[SupabaseCRUD:{operation.upper()}] {message}")
        self.operation = operation
        self.message = message
