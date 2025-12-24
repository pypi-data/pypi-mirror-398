class PersonalDataError(Exception):
    """Exception raised for errors in Personal Data operations."""

    def __init__(
        self,
        message: str = "An error occurred in Personal Data operation"
    ):
        """
        Initialize PersonalDataError.

        Args:
            message: Error message describing what went wrong
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"PersonalDataError: {self.message}"
