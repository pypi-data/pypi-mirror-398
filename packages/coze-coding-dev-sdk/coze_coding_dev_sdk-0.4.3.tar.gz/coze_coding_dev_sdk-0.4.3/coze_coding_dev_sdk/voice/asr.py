from typing import Optional, Tuple, Dict
from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from .models import ASRRequest, ASRResponse


class ASRClient(BaseClient):
    def __init__(
        self, 
        config: Optional[Config] = None, 
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(config, ctx, custom_headers)
        self.base_url = self.config.base_url
    @observe
    def recognize(
        self,
        uid: Optional[str] = None,
        url: Optional[str] = None,
        base64_data: Optional[str] = None
    ) -> Tuple[str, dict]:
        if not (url or base64_data):
            raise ValidationError("必须提供 url 或 base64_data 其中之一", field="url/base64_data")
        
        request = ASRRequest(
            uid=uid,
            url=url,
            base64_data=base64_data
        )
        
        headers = self.config.get_headers()
        response = self._make_request(
            method="POST",
            url=f"{self.base_url}/api/v3/auc/bigmodel/recognize/flash",
            json=request.to_api_request(),
            headers=headers
        )
        
        status_code = response.headers.get('X-Api-Status-Code', '0')
        message = response.headers.get('X-Api-Message', '')
        
        if status_code != '20000000':
            raise APIError(
                f"识别失败: {message}",
                code=status_code,
                status_code=response.status_code
            )
        
        data = self._handle_response(response)
        
        result = data.get("result", {})
        text = result.get("text", "")
        
        return text, data
