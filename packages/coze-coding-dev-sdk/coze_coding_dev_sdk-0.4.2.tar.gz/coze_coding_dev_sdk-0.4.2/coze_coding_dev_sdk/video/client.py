import time
from typing import Optional, List, Union, Dict
from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context
from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError
from .models import (
    VideoConfig,
    VideoGenerationRequest,
    VideoGenerationTask,
    TextContent,
    ImageURLContent,
    ImageURL
)


class VideoGenerationClient(BaseClient):
    def __init__(
        self, 
        config: Optional[Config] = None, 
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(config, ctx, custom_headers)
        self.base_url = self.config.base_url

    @observe(name="video_generation_create_task")
    def _create_task(
        self,
        model: str,
        content: List[Union[TextContent, ImageURLContent]],
        config: Optional[VideoConfig] = None
    ) -> str:
        request = VideoGenerationRequest(
            model=model,
            content=content,
            config=config or VideoConfig()
        )
        
        response = self._request(
            method="POST",
            url=f"{self.base_url}/api/v3/contents/generations/tasks",
            json=request.model_dump(exclude_none=True)
        )
        
        return response.get("id")

    @observe(name="video_generation_get_task")
    def _get_task_status(self, task_id: str) -> VideoGenerationTask:
        response = self._request(
            method="GET",
            url=f"{self.base_url}/api/v3/contents/generations/tasks/{task_id}"
        )
        
        return VideoGenerationTask(**response)

    @observe(name="video_generation_text_to_video")
    def text_to_video(
        self,
        prompt: str,
        model: str = "doubao-seedance-1-0-pro-250528",
        config: Optional[VideoConfig] = None,
        poll_interval: int = 5,
        max_wait_time: int = 300
    ) -> VideoGenerationTask:
        content = [TextContent(type="text", text=prompt)]
        task_id = self._create_task(model=model, content=content, config=config)
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            task = self._get_task_status(task_id)
            
            if task.status == "completed":
                return task
            elif task.status == "failed":
                raise APIError(f"Video generation failed: {task.error_message}")
            
            time.sleep(poll_interval)
        
        raise APIError(f"Video generation timeout after {max_wait_time} seconds")

    @observe(name="video_generation_image_to_video")
    def image_to_video(
        self,
        prompt: str,
        first_frame_url: Optional[str] = None,
        last_frame_url: Optional[str] = None,
        reference_images: Optional[List[str]] = None,
        model: str = "doubao-seedance-1-0-pro-250528",
        config: Optional[VideoConfig] = None,
        poll_interval: int = 5,
        max_wait_time: int = 300
    ) -> VideoGenerationTask:
        content: List[Union[TextContent, ImageURLContent]] = [
            TextContent(type="text", text=prompt)
        ]
        
        if first_frame_url:
            content.append(ImageURLContent(
                type="image_url",
                image_url=ImageURL(url=first_frame_url)
            ))
        
        if last_frame_url:
            content.append(ImageURLContent(
                type="image_url",
                image_url=ImageURL(url=last_frame_url)
            ))
        
        if reference_images:
            for img_url in reference_images:
                content.append(ImageURLContent(
                    type="image_url",
                    image_url=ImageURL(url=img_url)
                ))
        
        task_id = self._create_task(model=model, content=content, config=config)
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            task = self._get_task_status(task_id)
            
            if task.status == "completed":
                return task
            elif task.status == "failed":
                raise APIError(f"Video generation failed: {task.error_message}")
            
            time.sleep(poll_interval)
        
        raise APIError(f"Video generation timeout after {max_wait_time} seconds")

    @observe(name="video_generation_check_task")
    def check_task(self, task_id: str) -> VideoGenerationTask:
        return self._get_task_status(task_id)
