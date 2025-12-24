class CLSPError(Exception):
    """
    Exception class for CLSP-related errors.

    Represents internal failures in Convex Least Squares Programming
    routines. Supports structured messaging and optional diagnostic
    augmentation.

    Parameters
    ----------
    message : str, optional
        Description of the error. Defaults to a generic CLSP message.

    code : int or str, optional
        Optional error code or identifier for downstream handling.

    Usage
    -----
    raise CLSPError("Matrix A and b are incompatible", code=101)
    """
    def __init__(self, message: str              = "An error occurred in CLSP",
                 code:          int | str | None = None):
        self.message = message
        self.code    = code
        full_message = f"{message} (Code: {code})" if code is not None         \
                                                   else message
        super().__init__(full_message)

    def __str__(self) -> str:
        return self.message if self.code is None                               \
                            else f"{self.message} [Code: {self.code}]"

    def as_dict(self) -> dict:
        return {"error": self.message, "code": self.code}
