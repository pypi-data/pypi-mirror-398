import asyncio
from typing import Any, Dict, List, Optional, Union

from coze_coding_utils.runtime_ctx.context import Context
from cozeloop.decorator import observe

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError
from .models import ImageConfig, ImageGenerationRequest, ImageGenerationResponse


class ImageGenerationClient(BaseClient):
    def __init__(
        self,
        config: Optional[Config] = None,
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        super().__init__(config, ctx, custom_headers, verbose)
        self.base_url = self.config.base_url
        self.model = ImageConfig.DEFAULT_MODEL

    def extract_urls(self, response: ImageGenerationResponse) -> List[str]:
        urls = []
        for item in response.data:
            if item.error:
                raise APIError(
                    f"图片生成失败: {item.error.get('message', 'Unknown error')}",
                    code=item.error.get("code"),
                )
            if item.url:
                urls.append(item.url)
            elif item.b64_json:
                urls.append(f"data:image/png;base64,{item.b64_json}")
        return urls

    @observe
    def generate(
        self,
        prompt: str,
        size: Optional[str] = None,
        watermark: Optional[bool] = None,
        image: Optional[Union[str, List[str]]] = None,
        response_format: Optional[str] = None,
        optimize_prompt_mode: Optional[str] = None,
        sequential_image_generation: Optional[str] = None,
        sequential_image_generation_max_images: Optional[int] = None,
    ) -> ImageGenerationResponse:
        request_params = {"prompt": prompt}
        if size is not None:
            request_params["size"] = size
        if watermark is not None:
            request_params["watermark"] = watermark
        if image is not None:
            request_params["image"] = image
        if response_format is not None:
            request_params["response_format"] = response_format
        if optimize_prompt_mode is not None:
            request_params["optimize_prompt_mode"] = optimize_prompt_mode
        if sequential_image_generation is not None:
            request_params["sequential_image_generation"] = sequential_image_generation
        if sequential_image_generation_max_images is not None:
            request_params["sequential_image_generation_max_images"] = (
                sequential_image_generation_max_images
            )

        request = ImageGenerationRequest(**request_params)

        data = self._request(
            method="POST",
            url=f"{self.base_url}/api/v3/images/generations",
            json=request.to_api_request(self.model),
        )

        if "error" in data and data["error"]:
            raise APIError(
                f"API 返回错误: {data['error'].get('message', 'Unknown error')}",
                code=data["error"].get("code"),
            )

        parsed_response = ImageGenerationResponse(**data)

        return parsed_response

    async def generate_async(
        self,
        prompt: str,
        size: Optional[str] = None,
        watermark: Optional[bool] = None,
        image: Optional[Union[str, List[str]]] = None,
        response_format: Optional[str] = None,
        optimize_prompt_mode: Optional[str] = None,
        sequential_image_generation: Optional[str] = None,
        sequential_image_generation_max_images: Optional[int] = None,
    ) -> ImageGenerationResponse:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate,
            prompt,
            size,
            watermark,
            image,
            response_format,
            optimize_prompt_mode,
            sequential_image_generation,
            sequential_image_generation_max_images,
        )
