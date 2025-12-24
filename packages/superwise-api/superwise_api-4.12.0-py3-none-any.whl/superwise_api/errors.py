class SuperwiseApiException(Exception):
    """
    Base class for exceptions in the Superwise API.
    """

    def __init__(self, original_exception, message="Superwise API Error"):
        self.original_exception = original_exception
        self.message = message
        super().__init__(str(original_exception))

    def __str__(self):
        return f"{self.message}: {self.original_exception}"
