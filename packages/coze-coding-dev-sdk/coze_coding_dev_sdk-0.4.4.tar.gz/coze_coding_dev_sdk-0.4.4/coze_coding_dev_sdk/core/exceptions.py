from typing import Optional


class CozeSDKError(Exception):
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConfigurationError(CozeSDKError):
    def __init__(self, message: str, missing_key: Optional[str] = None):
        self.missing_key = missing_key
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"missing_key": missing_key}
        )


class APIError(CozeSDKError):
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        response_data: Optional[dict] = None
    ):
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(
            message=message,
            code=code,
            details={"status_code": status_code, "response_data": response_data}
        )


class NetworkError(CozeSDKError):
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(
            message=f"网络请求失败: {message}",
            code="NETWORK_ERROR",
            details={"original_error": str(original_error) if original_error else None}
        )


class ValidationError(CozeSDKError):
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[any] = None):
        self.field = field
        self.value = value
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value else None}
        )
