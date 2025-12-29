import re
from typing import Optional, Union, List, Literal
from pydantic import BaseModel, Field, field_validator

from ..core.exceptions import ValidationError


class ImageConfig:
    DEFAULT_MODEL = "doubao-seedream-4-5-251128"
    DEFAULT_SIZE = "2K"
    DEFAULT_WATERMARK = True
    DEFAULT_RESPONSE_FORMAT = "url"
    DEFAULT_OPTIMIZE_PROMPT_MODE = "standard"
    DEFAULT_SEQUENTIAL_IMAGE_GENERATION = "disabled"
    DEFAULT_SEQUENTIAL_IMAGE_GENERATION_MAX_IMAGES = 15
    
    MIN_WIDTH = 2560
    MAX_WIDTH = 4096
    MIN_HEIGHT = 1440
    MAX_HEIGHT = 4096


class ImageSize:
    @staticmethod
    def validate(size: str) -> str:
        if size in ["2K", "4K"]:
            return size
        
        match = re.match(r'^(\d+)x(\d+)$', size)
        if not match:
            raise ValidationError(
                "尺寸格式必须是 '2K'、'4K' 或 'WIDTHxHEIGHT' 格式",
                field="size",
                value=size
            )
        
        width, height = int(match.group(1)), int(match.group(2))
        
        if not (ImageConfig.MIN_WIDTH <= width <= ImageConfig.MAX_WIDTH):
            raise ValidationError(
                f"宽度必须在 [{ImageConfig.MIN_WIDTH}, {ImageConfig.MAX_WIDTH}] 范围内，当前值: {width}",
                field="size",
                value=size
            )
        
        if not (ImageConfig.MIN_HEIGHT <= height <= ImageConfig.MAX_HEIGHT):
            raise ValidationError(
                f"高度必须在 [{ImageConfig.MIN_HEIGHT}, {ImageConfig.MAX_HEIGHT}] 范围内，当前值: {height}",
                field="size",
                value=size
            )
        
        return size
    
    @staticmethod
    def validate_or_default(size: str) -> str:
        try:
            return ImageSize.validate(size)
        except ValidationError:
            return ImageConfig.DEFAULT_SIZE


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="用于生成图像的提示词")
    size: str = Field(default=ImageConfig.DEFAULT_SIZE, description="生成图片的尺寸")
    watermark: bool = Field(default=ImageConfig.DEFAULT_WATERMARK, description="是否添加水印")
    image: Optional[Union[str, List[str]]] = Field(default=None, description="参考图片")
    response_format: Literal["url", "b64_json"] = Field(
        default=ImageConfig.DEFAULT_RESPONSE_FORMAT,
        description="返回格式"
    )
    optimize_prompt_mode: str = Field(
        default=ImageConfig.DEFAULT_OPTIMIZE_PROMPT_MODE,
        description="提示词优化模式"
    )
    sequential_image_generation: Literal["auto", "disabled"] = Field(
        default=ImageConfig.DEFAULT_SEQUENTIAL_IMAGE_GENERATION,
        description="组图功能"
    )
    sequential_image_generation_max_images: int = Field(
        default=ImageConfig.DEFAULT_SEQUENTIAL_IMAGE_GENERATION_MAX_IMAGES,
        ge=1,
        le=15,
        description="最大图片数量"
    )
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v: str) -> str:
        return ImageSize.validate_or_default(v)
    
    def to_api_request(self, model: str) -> dict:
        return {
            "model": model,
            "prompt": self.prompt,
            "size": self.size,
            "watermark": self.watermark,
            "image": self.image,
            "response_format": self.response_format,
            "optimize_prompt_options": {
                "mode": self.optimize_prompt_mode,
            },
            "sequential_image_generation": self.sequential_image_generation,
            "sequential_image_generation_options": {
                "max_images": self.sequential_image_generation_max_images,
            },
        }


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    size: Optional[str] = None
    error: Optional[dict] = None


class UsageInfo(BaseModel):
    generated_images: int = 0
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ImageGenerationResponse(BaseModel):
    model: str
    created: int
    data: List[ImageData]
    usage: Optional[UsageInfo] = None
    error: Optional[dict] = None
    
    @property
    def success(self) -> bool:
        return self.error is None and all(item.error is None for item in self.data)
    
    @property
    def image_urls(self) -> List[str]:
        return [item.url for item in self.data if item.url]
    
    @property
    def image_b64_list(self) -> List[str]:
        return [item.b64_json for item in self.data if item.b64_json]
    
    @property
    def error_messages(self) -> List[str]:
        messages = []
        if self.error:
            messages.append(f"API错误: {self.error.get('message', 'Unknown error')}")
        for item in self.data:
            if item.error:
                messages.append(f"图片生成错误: {item.error.get('message', 'Unknown error')}")
        return messages
