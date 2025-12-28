class ReckomateAPIError(Exception):
    def __init__(self, status_code: int, message: str, payload=None):
        self.status_code = status_code
        self.message = message
        self.payload = payload
        super().__init__(f"[{status_code}] {message}")
