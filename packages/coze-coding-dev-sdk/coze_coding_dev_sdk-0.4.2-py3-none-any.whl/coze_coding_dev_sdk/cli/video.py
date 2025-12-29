import json
import os
import time
from typing import Optional

import click
from coze_coding_utils.runtime_ctx.context import Context
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core.config import Config
from ..core.exceptions import APIError
from ..video import VideoConfig, VideoGenerationClient
from .constants import RUN_MODE_HEADER, RUN_MODE_TEST

console = Console()


def parse_resolution(size: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not size:
        return None, None

    width, height = size.split("x")
    w, h = int(width), int(height)

    if w == h:
        return "1:1", "720p" if w <= 1024 else "1080p"
    elif w > h:
        return "16:9", "720p" if w <= 1440 else "1080p"
    else:
        return "9:16", "720p" if h <= 1440 else "1080p"


@click.command()
@click.option("--prompt", "-p", help="Text description of the video")
@click.option("--image-url", "-i", help="Image URL (single or comma-separated pair)")
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["speed", "quality"]),
    default="speed",
    help="Output mode",
)
@click.option("--with-audio", is_flag=True, help="Generate AI audio effects")
@click.option("--size", "-s", help="Video resolution (e.g., 1920x1080)")
@click.option("--fps", type=int, help="Frame rate (30 or 60)")
@click.option("--duration", "-d", type=int, help="Duration in seconds (5 or 10)")
@click.option("--model", "-m", help="Model name to use")
@click.option("--poll", is_flag=True, help="Auto-poll until task completes")
@click.option(
    "--poll-interval", type=int, default=5, help="Polling interval in seconds"
)
@click.option("--max-polls", type=int, default=60, help="Maximum poll attempts")
@click.option("--output", "-o", type=click.Path(), help="Output file path (JSON)")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
def video(
    prompt: Optional[str],
    image_url: Optional[str],
    quality: str,
    with_audio: bool,
    size: Optional[str],
    fps: Optional[int],
    duration: Optional[int],
    model: Optional[str],
    poll: bool,
    poll_interval: int,
    max_polls: int,
    output: Optional[str],
    mock: bool,
):
    """Generate video using AI."""
    try:
        config = Config()

        ctx = None
        if mock:
            ctx = Context(
                request_id=f"mock-req-{int(time.time())}",
                headers={RUN_MODE_HEADER: RUN_MODE_TEST},
            )
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoGenerationClient(config, ctx=ctx)

        image_urls = None
        if image_url:
            image_urls = [url.strip() for url in image_url.split(",")]

        ratio, resolution = parse_resolution(size)

        video_config = VideoConfig(
            resolution=resolution or "720p",
            ratio=ratio or "16:9",
            duration=duration or 5,
        )

        console.print("[bold cyan]Creating video generation task...[/bold cyan]")

        model_name = model or "doubao-seedance-1-0-pro-250528"

        if image_urls:
            if len(image_urls) == 1:
                task_id = client._create_task(
                    model=model_name,
                    content=[
                        {"type": "text", "text": prompt or ""},
                        {"type": "image_url", "image_url": {"url": image_urls[0]}},
                    ],
                    config=video_config,
                )
            elif len(image_urls) == 2:
                task_id = client._create_task(
                    model=model_name,
                    content=[
                        {"type": "text", "text": prompt or ""},
                        {"type": "image_url", "image_url": {"url": image_urls[0]}},
                        {"type": "image_url", "image_url": {"url": image_urls[1]}},
                    ],
                    config=video_config,
                )
            else:
                raise ValueError("Only 1 or 2 images are supported")
        else:
            if not prompt:
                raise ValueError("Either --prompt or --image-url must be provided")

            task_id = client._create_task(
                model=model_name,
                content=[{"type": "text", "text": prompt}],
                config=video_config,
            )

        console.print(f"[green]✓[/green] Task created: [bold]{task_id}[/bold]")

        result = {"id": task_id, "status": "processing"}

        if poll:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Generating video (Task ID: {task_id})...", total=None
                )

                max_wait_time = poll_interval * max_polls
                start_time = time.time()

                while time.time() - start_time < max_wait_time:
                    task_result = client._get_task_status(task_id)

                    if task_result.status == "completed":
                        progress.update(
                            task, description="[green]✓ Video generation completed!"
                        )
                        result = task_result.model_dump()
                        break
                    elif task_result.status == "failed":
                        progress.update(
                            task, description=f"[red]✗ Video generation failed"
                        )
                        result = task_result.model_dump()
                        break

                    time.sleep(poll_interval)
                else:
                    raise TimeoutError(
                        f"Task did not complete within {max_wait_time} seconds"
                    )

            table = Table(title="Video Generation Result")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Task ID", result.get("id", ""))
            table.add_row("Status", result.get("status", ""))

            if result.get("video_url"):
                table.add_row("Video URL", result.get("video_url"))
            if result.get("error_message"):
                table.add_row("Error", result.get("error_message"))

            console.print(table)
        else:
            console.print(
                f"\n[yellow]Use the following command to check status:[/yellow]"
            )
            console.print(f"coze-coding-ai video-status {task_id}")

        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"\n[green]✓[/green] Result saved to: {output}")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()


@click.command()
@click.argument("task_id")
@click.option("--output", "-o", type=click.Path(), help="Output file path (JSON)")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
def video_status(task_id: str, output: Optional[str], mock: bool):
    """Check video generation task status."""
    try:
        config = Config()

        ctx = None
        if mock:
            ctx = Context(
                request_id=f"mock-req-{int(time.time())}",
                headers={RUN_MODE_HEADER: RUN_MODE_TEST},
            )
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = VideoGenerationClient(config, ctx=ctx)

        task_result = client._get_task_status(task_id)
        result = task_result.model_dump()

        table = Table(title=f"Task Status: {task_id}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Task ID", result.get("id", ""))
        table.add_row("Status", result.get("status", ""))

        if result.get("video_url"):
            table.add_row("Video URL", result.get("video_url"))
        if result.get("error_message"):
            table.add_row("Error", result.get("error_message"))

        console.print(table)

        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"\n[green]✓[/green] Result saved to: {output}")

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
