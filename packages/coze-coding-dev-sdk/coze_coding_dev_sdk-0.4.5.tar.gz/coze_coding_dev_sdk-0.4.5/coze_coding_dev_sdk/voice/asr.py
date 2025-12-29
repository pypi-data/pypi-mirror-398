from typing import Dict, Optional, Tuple

from coze_coding_utils.runtime_ctx.context import Context
from cozeloop.decorator import observe

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from .models import ASRRequest, ASRResponse


class ASRClient(BaseClient):
    def __init__(
        self,
        config: Optional[Config] = None,
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        super().__init__(config, ctx, custom_headers, verbose)
        self.base_url = self.config.base_url

    @observe
    def recognize(
        self,
        uid: Optional[str] = None,
        url: Optional[str] = None,
        base64_data: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """
        识别音频文件中的语音内容

        音频要求:
        - 音频时长 ≤ 2小时
        - 音频大小 ≤ 100MB
        - 支持编码: PCM/WAV/MP3/OGG OPUS

        Args:
            uid: 用户唯一标识
            url: 音频文件 URL (与 base64_data 二选一)
            base64_data: Base64 编码的音频数据 (与 url 二选一)

        Returns:
            Tuple[str, dict]: 识别的文本和详细响应数据
        """
        if not (url or base64_data):
            raise ValidationError(
                "必须提供 url 或 base64_data 其中之一", field="url/base64_data"
            )

        request = ASRRequest(uid=uid, url=url, base64_data=base64_data)

        data = self._request(
            method="POST",
            url=f"{self.base_url}/api/v3/auc/bigmodel/recognize/flash",
            json=request.to_api_request(),
        )

        result = data.get("result", {})
        text = result.get("text", "")

        return text, data
