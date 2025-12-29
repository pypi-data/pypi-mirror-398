class CredentialType:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return False


class CredentialScalarType:
    TEXT = CredentialType("Text")
    SENSITIVE = CredentialType("Sensitive")
