from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field


class VideoConfig(BaseModel):
    resolution: Optional[Literal["720p", "1080p"]] = "720p"
    ratio: Optional[Literal["16:9", "9:16", "1:1"]] = "16:9"
    duration: Optional[int] = Field(default=5, ge=5, le=10)
    watermark: Optional[bool] = True
    seed: Optional[int] = None
    camerafixed: Optional[bool] = False


class ImageURL(BaseModel):
    url: str


class ImageURLContent(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: ImageURL


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class VideoGenerationRequest(BaseModel):
    model: str
    content: List[Union[TextContent, ImageURLContent]]
    config: Optional[VideoConfig] = None


class VideoGenerationTask(BaseModel):
    id: str
    status: Literal["processing", "completed", "failed"]
    video_url: Optional[str] = None
    error_message: Optional[str] = None
