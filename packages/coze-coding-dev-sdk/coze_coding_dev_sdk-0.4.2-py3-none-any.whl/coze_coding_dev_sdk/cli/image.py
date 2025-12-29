import base64
import os
import time
from typing import Optional

import click
from coze_coding_utils.runtime_ctx.context import Context
from rich.console import Console

from ..core.config import Config
from ..image import ImageGenerationClient
from .constants import RUN_MODE_HEADER, RUN_MODE_TEST

console = Console()


def validate_and_normalize_size(size: str) -> str:
    if size in ["2K", "4K"]:
        return size

    try:
        width, height = size.split("x")
        w, h = int(width), int(height)

        if 2560 <= w <= 4096 and 1440 <= h <= 4096:
            return size
        else:
            console.print(
                f"[yellow]Warning: Size {size} is out of range [2560x1440, 4096x4096], using default 2K[/yellow]"
            )
            return "2K"
    except (ValueError, AttributeError):
        console.print(
            f"[yellow]Warning: Invalid size format {size}, using default 2K[/yellow]"
        )
        return "2K"


@click.command()
@click.option("--prompt", "-p", required=True, help="Text description of the image")
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output file path"
)
@click.option(
    "--size",
    "-s",
    default="2K",
    help="Image size (2K, 4K, or WIDTHxHEIGHT in range [2560x1440, 4096x4096])",
)
@click.option(
    "--image", "-i", help="Reference image URL or path (for image-to-image generation)"
)
@click.option(
    "--images",
    multiple=True,
    help="Multiple reference image URLs or paths (can be used multiple times)",
)
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
def image(
    prompt: str, output: str, size: str, image: Optional[str], images: tuple, mock: bool
):
    """Generate image using AI."""
    try:
        config = Config()

        ctx = None
        if mock:
            ctx = Context(
                request_id=f"mock-req-{int(time.time())}",
                headers={RUN_MODE_HEADER: RUN_MODE_TEST},
            )
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = ImageGenerationClient(config, ctx=ctx)

        reference_images = None
        if image:
            reference_images = image
        elif images:
            reference_images = list(images)

        validated_size = validate_and_normalize_size(size)

        console.print(f"[bold cyan]Generating image...[/bold cyan]")
        console.print(f"Prompt: [yellow]{prompt}[/yellow]")
        console.print(f"Size: [yellow]{validated_size}[/yellow]")
        if reference_images:
            if isinstance(reference_images, str):
                console.print(f"Reference image: [blue]{reference_images}[/blue]")
            else:
                console.print(
                    f"Reference images: [blue]{len(reference_images)} images[/blue]"
                )

        response = client.generate(
            prompt=prompt,
            size=validated_size,
            image=reference_images,
            response_format="b64_json",
        )

        if not response.data or len(response.data) == 0:
            raise ValueError("No image data returned")

        image_data = response.data[0]

        if image_data.error:
            error_msg = image_data.error.get("message", "Unknown error")
            raise Exception(f"Image generation failed: {error_msg}")

        if image_data.b64_json:
            image_bytes = base64.b64decode(image_data.b64_json)

            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

            with open(output, "wb") as f:
                f.write(image_bytes)

            console.print(f"[green]✓[/green] Image saved to: [bold]{output}[/bold]")
        elif image_data.url:
            import requests

            img_response = requests.get(image_data.url)
            img_response.raise_for_status()

            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

            with open(output, "wb") as f:
                f.write(img_response.content)

            console.print(f"[green]✓[/green] Image saved to: [bold]{output}[/bold]")
            console.print(f"Original URL: [blue]{image_data.url}[/blue]")
        else:
            raise ValueError("No image data (b64_json or url) in response")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
