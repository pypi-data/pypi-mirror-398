class AuthError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
