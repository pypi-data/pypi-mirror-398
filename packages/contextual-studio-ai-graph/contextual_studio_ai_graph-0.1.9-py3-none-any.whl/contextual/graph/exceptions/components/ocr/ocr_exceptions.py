class OCRException(Exception):
    """Raised when the text ocrs process fails.

    Attributes:
        message (str): Description of the error.
        cause (Exception, optional): Original exception, if any.
    """

    def __init__(self, message: str, cause: Exception | None = None):
        """Initializes the OCRException with a message and an optional cause."""
        self.message = message
        self.cause = cause
        super().__init__(f"Text ocr failed: {message}")
