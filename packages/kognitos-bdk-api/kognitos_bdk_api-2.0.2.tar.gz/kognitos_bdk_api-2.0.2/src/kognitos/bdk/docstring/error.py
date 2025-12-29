class DocstringParseError(RuntimeError):

    def __init__(self, message="Cannot parse docstring", original_exception=None):
        """Initialize the exception with an optional error message."""
        self.message = message
        self.original_exception = original_exception

        if self.original_exception:
            super().__init__(f"{self.message}: {str(self.original_exception)}")
        else:
            super().__init__(self.message)
