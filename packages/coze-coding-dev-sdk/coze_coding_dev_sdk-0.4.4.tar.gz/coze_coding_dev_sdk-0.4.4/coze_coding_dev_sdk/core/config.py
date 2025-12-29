import os
from typing import Optional
from .exceptions import ConfigurationError


class Config:
    DEFAULT_RETRY_TIMES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 60
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        base_model_url: Optional[str] = None,
        retry_times: int = DEFAULT_RETRY_TIMES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self.api_key = api_key or self._get_env_var("COZE_WORKLOAD_IDENTITY_API_KEY")
        self.base_url = base_url or self._get_env_var("COZE_INTEGRATION_BASE_URL")
        self.base_model_url = base_model_url or self._get_env_var("COZE_INTEGRATION_MODEL_BASE_URL")
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        self._validate()
    
    def _get_env_var(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ConfigurationError(
                f"环境变量 {key} 未设置，请确保已正确配置",
                missing_key=key
            )
        return value
    
    def _validate(self):
        if not self.api_key:
            raise ConfigurationError("API Key 未配置")
        if not self.base_url and not self.base_model_url:
            raise ConfigurationError("Base URL 未配置")
    
    def get_headers(self, ctx_headers: Optional[dict] = None) -> dict:
        try:
            from .. import __version__
        except ImportError:
            __version__ = "0.0.0"
        
        headers = {}
        if ctx_headers:
            headers.update(ctx_headers)
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Authorization", f"Bearer {self.api_key}")
        headers.setdefault("X-Client-Sdk", f"coze-coding-dev-sdk-python/{__version__}")
        return headers
