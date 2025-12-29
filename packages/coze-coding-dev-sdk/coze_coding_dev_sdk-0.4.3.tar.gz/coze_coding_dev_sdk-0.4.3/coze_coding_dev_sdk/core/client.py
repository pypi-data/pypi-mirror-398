import time
from typing import Optional, Dict
import requests
from coze_coding_utils.runtime_ctx.context import Context, default_headers

from .config import Config
from .exceptions import APIError, NetworkError


class BaseClient:
    def __init__(
        self, 
        config: Optional[Config] = None, 
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        if config is None:
            config = Config()
        self.config = config
        self.ctx = ctx
        self.custom_headers = custom_headers or {}
    
    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> dict:
        request_headers = self.config.get_headers(headers)
        
        if self.ctx is not None:
            ctx_headers = default_headers(self.ctx)
            request_headers.update(ctx_headers)
        
        response = self._make_request(
            method=method,
            url=url,
            headers=request_headers,
            **kwargs
        )
        return self._handle_response(response)
    
    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        last_error = None
        
        for attempt in range(self.config.retry_times):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                return response
                
            except requests.exceptions.RequestException as e:
                last_error = NetworkError(str(e), e)
                if attempt < self.config.retry_times - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
        
        raise last_error
    
    def _handle_response(self, response: requests.Response) -> dict:
        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}, 响应内容: {response.text[:200]}",
                status_code=response.status_code
            )
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP 错误: {str(e)}"
            if data:
                error_msg += f", 响应数据: {data}"
            raise APIError(
                error_msg,
                status_code=response.status_code,
                response_data=data
            )
        
        return data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
