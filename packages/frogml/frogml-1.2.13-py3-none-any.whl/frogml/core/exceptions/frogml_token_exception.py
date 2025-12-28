from .quiet_error import QuietError


class FrogMLTokenException(QuietError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message: str = message
