class SignatureError(Exception):
    """
    Raised by BDK's type checkers when there is a mismatch between the english signature and the
    python signature of a procedure
    """

    def __init__(self, msg: str):
        super().__init__(msg)
