from typing import Optional, Literal, Dict, Any, List, Union
from pydantic import BaseModel, Field


class ThinkingConfig(BaseModel):
    type: Literal["enabled", "disabled"] = Field("disabled", description="是否开启深度思考能力")


class CachingConfig(BaseModel):
    type: Literal["enabled", "disabled"] = Field("disabled", description="是否开启模型缓存")


class LLMConfig(BaseModel):
    model: str = Field("doubao-seed-1-6-251015", description="模型ID")
    thinking: Optional[Literal["enabled", "disabled"]] = Field("disabled", description="是否开启深度思考能力")
    caching: Optional[Literal["enabled", "disabled"]] = Field("disabled", description="是否开启模型缓存")
    temperature: Optional[float] = Field(1.0, ge=0, le=2, description="控制模型输出的随机性")
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2, description="重复语句惩罚")
    top_p: Optional[float] = Field(0, ge=0, le=1, description="控制模型输出的多样性")
    max_tokens: Optional[int] = Field(None, description="控制模型输出的最大 tokens 数")
    max_completion_tokens: Optional[int] = Field(None, description="控制模型输出的最大 completion tokens 数")
    streaming: bool = Field(True, description="是否使用流式输出")


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageURLDetail(BaseModel):
    url: str


class ImageURLContent(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: ImageURLDetail


class VideoURLDetail(BaseModel):
    url: str


class VideoURLContent(BaseModel):
    type: Literal["video_url"] = "video_url"
    video_url: VideoURLDetail


MessageContent = Union[str, List[Union[TextContent, ImageURLContent, VideoURLContent]]]
