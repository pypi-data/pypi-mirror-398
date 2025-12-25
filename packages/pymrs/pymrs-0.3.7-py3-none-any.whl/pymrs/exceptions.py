class MRSClientError(Exception):
    """
    Exception raised for errors related to the MRSClient operations.

    Attributes:
        code (str): The error code associated with the exception.
        message (str): The error message associated with the exception.
    """

    def __init__(self, code: str, message: str):
        """
        Initializes a MRSClientError with the specified error code and message.

        Args:
            code (str): The error code associated with the exception.
            message (str): The error message associated with the exception.
        """
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
