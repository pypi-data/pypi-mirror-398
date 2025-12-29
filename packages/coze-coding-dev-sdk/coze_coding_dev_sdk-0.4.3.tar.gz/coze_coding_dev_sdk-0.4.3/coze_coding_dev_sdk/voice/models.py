from typing import Optional, Literal
from pydantic import BaseModel, Field


class TTSConfig:
    DEFAULT_SPEAKER = "zh_female_xiaohe_uranus_bigtts"
    DEFAULT_AUDIO_FORMAT = "mp3"
    DEFAULT_SAMPLE_RATE = 24000
    DEFAULT_SPEECH_RATE = 0
    DEFAULT_LOUDNESS_RATE = 0


class TTSRequest(BaseModel):
    uid: str = Field(..., description="用户唯一标识")
    text: Optional[str] = Field(default=None, description="合成文本")
    ssml: Optional[str] = Field(default=None, description="SSML格式文本")
    speaker: str = Field(default=TTSConfig.DEFAULT_SPEAKER, description="音色标识")
    audio_format: Literal["pcm", "mp3", "ogg_opus"] = Field(
        default=TTSConfig.DEFAULT_AUDIO_FORMAT,
        description="音频格式"
    )
    sample_rate: Literal[8000, 16000, 22050, 24000, 32000, 44100, 48000] = Field(
        default=TTSConfig.DEFAULT_SAMPLE_RATE,
        description="采样率"
    )
    speech_rate: int = Field(
        default=TTSConfig.DEFAULT_SPEECH_RATE,
        ge=-50,
        le=100,
        description="语速"
    )
    loudness_rate: int = Field(
        default=TTSConfig.DEFAULT_LOUDNESS_RATE,
        ge=-50,
        le=100,
        description="音量"
    )
    
    def to_api_request(self) -> dict:
        params = {
            "user": {
                "uid": self.uid,
            },
            "req_params": {
                "speaker": self.speaker,
                "audio_params": {
                    "format": self.audio_format,
                    "sample_rate": self.sample_rate,
                    "speech_rate": self.speech_rate,
                    "loudness_rate": self.loudness_rate
                }
            },
        }
        
        if self.text:
            params["req_params"]["text"] = self.text
        elif self.ssml:
            params["req_params"]["ssml"] = self.ssml
        
        return params


class ASRRequest(BaseModel):
    uid: Optional[str] = Field(default=None, description="用户唯一标识")
    url: Optional[str] = Field(default=None, description="音频文件URL")
    base64_data: Optional[str] = Field(default=None, description="音频文件Base64编码")
    
    def to_api_request(self) -> dict:
        audio_data = {}
        if self.url:
            audio_data["url"] = self.url
        elif self.base64_data:
            audio_data["data"] = self.base64_data
        
        return {
            "user": {
                "uid": self.uid,
            },
            "audio": audio_data,
        }


class ASRResponse(BaseModel):
    text: str = Field(..., description="识别结果文本")
    duration: Optional[int] = Field(default=None, description="音频时长(毫秒)")
    utterances: Optional[list] = Field(default=None, description="详细识别结果")
