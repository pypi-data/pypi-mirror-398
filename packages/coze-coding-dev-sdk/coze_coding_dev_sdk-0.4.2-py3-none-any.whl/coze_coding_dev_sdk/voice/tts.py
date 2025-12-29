import json
import base64
from typing import Optional, Tuple, Dict
from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from .models import TTSConfig, TTSRequest


class TTSClient(BaseClient):
    def __init__(
        self, 
        config: Optional[Config] = None, 
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(config, ctx, custom_headers)
        self.base_url = self.config.base_url
    @observe
    def synthesize(
        self,
        uid: str,
        text: Optional[str] = None,
        ssml: Optional[str] = None,
        speaker: str = TTSConfig.DEFAULT_SPEAKER,
        audio_format: str = TTSConfig.DEFAULT_AUDIO_FORMAT,
        sample_rate: int = TTSConfig.DEFAULT_SAMPLE_RATE,
        speech_rate: int = TTSConfig.DEFAULT_SPEECH_RATE,
        loudness_rate: int = TTSConfig.DEFAULT_LOUDNESS_RATE,
    ) -> Tuple[str, int]:
        if not (text or ssml):
            raise ValidationError("必须提供 text 或 ssml 其中之一", field="text/ssml")
        
        request = TTSRequest(
            uid=uid,
            text=text,
            ssml=ssml,
            speaker=speaker,
            audio_format=audio_format,
            sample_rate=sample_rate,
            speech_rate=speech_rate,
            loudness_rate=loudness_rate
        )
        
        headers = self.config.get_headers({"Connection": "keep-alive"})
        response = self._make_request(
            method="POST",
            url=f"{self.base_url}/api/v3/tts/unidirectional",
            json=request.to_api_request(),
            headers=headers,
            stream=True
        )
        
        try:
            audio_uri = None
            audio_data = bytearray()
            total_audio_size = 0
            
            for chunk in response.iter_lines(decode_unicode=False):
                if not chunk:
                    continue
                
                chunk_str = chunk.decode("utf-8").replace("data:", "")
                data = json.loads(chunk_str)
                
                if data.get("code", 0) == 0 and "data" in data and data["data"]:
                    chunk_audio = base64.b64decode(data["data"])
                    audio_size = len(chunk_audio)
                    total_audio_size += audio_size
                    audio_data.extend(chunk_audio)
                
                elif data.get("code", 0) == 20000000:
                    if 'url' in data and data['url']:
                        audio_uri = data['url']
                    break
                
                elif data.get("code", 0) > 0:
                    raise APIError(
                        f"合成音频失败: {data.get('message', '')}",
                        code=str(data.get('code', 0))
                    )
            
            return audio_uri or "", total_audio_size
            
        except json.JSONDecodeError as e:
            raise APIError(f"响应解析失败: {str(e)}")
        except Exception as e:
            raise APIError(f"合成异常: {str(e)}")
        finally:
            response.close()
