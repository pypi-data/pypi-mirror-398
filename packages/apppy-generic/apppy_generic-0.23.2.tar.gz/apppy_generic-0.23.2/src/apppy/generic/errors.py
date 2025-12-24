# NOTE: Do not use ApiError directly
# instead use ApiClientError or ApiServerError
class ApiError(BaseException):
    """Generic base class for any error raised in an API"""

    code: str
    status: int

    def __init__(self, code: str, status: int):
        self.code: str = code
        self.status: int = status


class ApiClientError(ApiError):
    """Base class for any API error raised related to bad client input"""

    def __init__(self, code: str = "generic_client_error", status: int = 400):
        super().__init__(code, status)


class ApiServerError(ApiError):
    """Base class for any API error raised related to internal server processing"""

    def __init__(self, code: str = "generic_server_error", status: int = 500):
        super().__init__(code, status)
