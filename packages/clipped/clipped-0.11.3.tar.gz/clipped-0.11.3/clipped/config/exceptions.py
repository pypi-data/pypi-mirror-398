from click import ClickException


class ClippedException(ClickException):
    def __init__(self, message=None):
        super().__init__(message)

    def __repr__(self):
        if hasattr(self, "message"):
            return self.message
        return super().__repr__()

    def __str__(self):
        if hasattr(self, "message"):
            return self.message
        return super().__str__()


class SchemaError(ClippedException):
    pass
