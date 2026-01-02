"""Exception types used by the contextual graph package."""


class LLMServiceException(Exception):
    """Base exception for LLMs-related errors."""

    pass


class LLMServiceConnectionException(LLMServiceException):
    """Custom exception raised when there is an issue connecting to LLMService.

    Triggers when dealing with invalid keys.

    Attributes:
        message (str): A detailed error message describing the connection issue.
    """

    def __init__(self, message: str):
        """Initialize the exception with a message.

        Args:
            message (str): Details regarding the connection failure.
        """
        super().__init__(f"LLM service connection error: {message}")
