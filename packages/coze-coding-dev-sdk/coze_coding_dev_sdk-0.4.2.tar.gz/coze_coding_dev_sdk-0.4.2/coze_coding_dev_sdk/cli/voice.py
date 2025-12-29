import base64
import json
import os
import time
from typing import Optional

import click
from coze_coding_utils.runtime_ctx.context import Context
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core.config import Config
from ..voice.asr import ASRClient
from ..voice.models import TTSConfig
from ..voice.tts import TTSClient
from .constants import RUN_MODE_HEADER, RUN_MODE_TEST

console = Console()

COMMON_SPEAKERS = {
    "zh_female_xueayi_saturn_bigtts": "儿童绘本 (有声阅读)",
    "zh_female_vv_uranus_bigtts": "vivi (通用场景, 中英)",
    "zh_male_dayi_saturn_bigtts": "大壹 (视频配音)",
    "zh_female_mizai_saturn_bigtts": "黑猫侦探社咪仔 (视频配音)",
    "zh_female_jitangnv_saturn_bigtts": "鸡汤女 (视频配音)",
    "zh_female_meilinvyou_saturn_bigtts": "魅力女友 (视频配音)",
    "zh_female_santongyongns_saturn_bigtts": "流畅女声 (视频配音)",
    "zh_male_ruyayichen_saturn_bigtts": "儒雅逸辰 (视频配音)",
    "zh_female_xiaohe_uranus_bigtts": "小何 (通用场景, 默认)",
    "zh_male_m191_uranus_bigtts": "云舟 (通用场景)",
    "zh_male_taocheng_uranus_bigtts": "小天 (通用场景)",
    "saturn_zh_female_keainvsheng_tob": "可爱女生 (角色扮演)",
    "saturn_zh_female_tiaopigongzhu_tob": "调皮公主 (角色扮演)",
    "saturn_zh_male_shuanglangshaonian_tob": "爽朗少年 (角色扮演)",
    "saturn_zh_male_tiancaitongzhuo_tob": "天才同桌 (角色扮演)",
    "saturn_zh_female_cancan_tob": "知性灿灿 (角色扮演)",
}


@click.command()
@click.argument("text")
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="输出音频文件路径"
)
@click.option("--uid", "-u", default="cli_user", help="用户唯一标识")
@click.option("--speaker", "-s", default=TTSConfig.DEFAULT_SPEAKER, help="音色选择")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["mp3", "pcm", "ogg_opus"]),
    default="mp3",
    help="音频格式",
)
@click.option(
    "--sample-rate",
    type=int,
    default=24000,
    help="采样率 (8000/16000/22050/24000/32000/44100/48000)",
)
@click.option("--speech-rate", type=int, default=0, help="语速 (-50 到 100)")
@click.option("--loudness-rate", type=int, default=0, help="音量 (-50 到 100)")
@click.option("--ssml", is_flag=True, help="使用 SSML 格式")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
def tts(
    text,
    output,
    uid,
    speaker,
    format,
    sample_rate,
    speech_rate,
    loudness_rate,
    ssml,
    mock,
):
    """语音合成 (Text-to-Speech)

    将文本转换为语音音频文件。

    音色列表 (按场景分类):

    有声阅读:
      - zh_female_xueayi_saturn_bigtts (儿童绘本)

    通用场景:
      - zh_female_xiaohe_uranus_bigtts (小何, 默认)
      - zh_female_vv_uranus_bigtts (vivi, 支持中英)
      - zh_male_m191_uranus_bigtts (云舟)
      - zh_male_taocheng_uranus_bigtts (小天)

    视频配音:
      - zh_male_dayi_saturn_bigtts (大壹)
      - zh_female_mizai_saturn_bigtts (黑猫侦探社咪仔)
      - zh_female_jitangnv_saturn_bigtts (鸡汤女)
      - zh_female_meilinvyou_saturn_bigtts (魅力女友)
      - zh_female_santongyongns_saturn_bigtts (流畅女声)
      - zh_male_ruyayichen_saturn_bigtts (儒雅逸辰)

    角色扮演:
      - saturn_zh_female_keainvsheng_tob (可爱女生)
      - saturn_zh_female_tiaopigongzhu_tob (调皮公主)
      - saturn_zh_male_shuanglangshaonian_tob (爽朗少年)
      - saturn_zh_male_tiancaitongzhuo_tob (天才同桌)
      - saturn_zh_female_cancan_tob (知性灿灿)

    示例:
      coze-coding-ai tts "你好,欢迎使用" -o hello.mp3
      coze-coding-ai tts "测试视频配音" -o test.mp3 -s zh_male_dayi_saturn_bigtts
      coze-coding-ai tts "儿童故事" -o story.mp3 -s zh_female_xueayi_saturn_bigtts --speech-rate 20
    """
    try:
        config = Config()

        ctx = None
        if mock:
            ctx = Context(
                request_id=f"mock-req-{int(time.time())}",
                headers={RUN_MODE_HEADER: RUN_MODE_TEST},
            )
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = TTSClient(config, ctx=ctx)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]正在合成语音...", total=None)

            if ssml:
                audio_url, audio_size = client.synthesize(
                    uid=uid,
                    ssml=text,
                    speaker=speaker,
                    audio_format=format,
                    sample_rate=sample_rate,
                    speech_rate=speech_rate,
                    loudness_rate=loudness_rate,
                )
            else:
                audio_url, audio_size = client.synthesize(
                    uid=uid,
                    text=text,
                    speaker=speaker,
                    audio_format=format,
                    sample_rate=sample_rate,
                    speech_rate=speech_rate,
                    loudness_rate=loudness_rate,
                )

            progress.update(task, description="[green]✓ 语音合成完成")

        os.makedirs(
            (
                os.path.dirname(os.path.abspath(output))
                if os.path.dirname(output)
                else "."
            ),
            exist_ok=True,
        )

        if audio_url:
            import requests

            response = requests.get(audio_url)
            response.raise_for_status()
            with open(output, "wb") as f:
                f.write(response.content)
            file_size = len(response.content)
        else:
            file_size = audio_size

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        display_text = text[:50] + "..." if len(text) > 50 else text
        table.add_row("文本", display_text)
        table.add_row("音色", COMMON_SPEAKERS.get(speaker, speaker))
        table.add_row("格式", format.upper())
        table.add_row("采样率", f"{sample_rate} Hz")
        if speech_rate != 0:
            table.add_row("语速", f"{speech_rate:+d}")
        if loudness_rate != 0:
            table.add_row("音量", f"{loudness_rate:+d}")
        table.add_row("文件", output)
        table.add_row("大小", f"{file_size / 1024:.1f} KB")

        console.print()
        console.print(
            Panel(
                table,
                title="[bold green]语音合成完成[/bold green]",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()


@click.command()
@click.argument("audio")
@click.option("--uid", "-u", default="cli_user", help="用户唯一标识")
@click.option("--output", "-o", type=click.Path(), help="输出文本文件路径")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="输出格式",
)
@click.option("--base64", is_flag=True, help="将本地文件转为 base64 上传")
@click.option("--mock", is_flag=True, help="使用 mock 模式（测试运行）")
def asr(audio, uid, output, format, base64, mock):
    """语音识别 (Automatic Speech Recognition)

    将语音音频转换为文本。

    支持:
      - 本地音频文件
      - 音频 URL
      - Base64 编码上传

    示例:
      coze-coding-ai asr ./audio.mp3
      coze-coding-ai asr https://example.com/audio.mp3
      coze-coding-ai asr ./audio.mp3 -o result.txt
      coze-coding-ai asr ./audio.mp3 -f json
      coze-coding-ai asr ./audio.mp3 --base64
    """
    try:
        config = Config()

        ctx = None
        if mock:
            ctx = Context(
                request_id=f"mock-req-{int(time.time())}",
                headers={RUN_MODE_HEADER: RUN_MODE_TEST},
            )
            console.print("[yellow]🧪 Mock 模式已启用（测试运行）[/yellow]")

        client = ASRClient(config, ctx=ctx)

        audio_url = None
        audio_base64 = None

        if audio.startswith(("http://", "https://")):
            audio_url = audio
            console.print(f"[cyan]正在识别 URL 音频:[/cyan] {audio}")
        else:
            if not os.path.exists(audio):
                raise FileNotFoundError(f"音频文件不存在: {audio}")

            if base64:
                console.print(f"[cyan]正在读取并编码音频文件:[/cyan] {audio}")
                with open(audio, "rb") as f:
                    audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            else:
                raise ValueError(
                    "本地文件需要先上传到可访问的 URL,或使用 --base64 选项"
                )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]正在识别语音...", total=None)

            text, data = client.recognize(
                uid=uid, url=audio_url, base64_data=audio_base64
            )

            progress.update(task, description="[green]✓ 识别完成")

        console.print()

        if format == "json":
            result = {
                "text": text,
                "duration": data.get("result", {}).get("duration"),
                "utterances": data.get("result", {}).get("utterances", []),
            }

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                console.print(f"[green]✓[/green] 结果已保存到: {output}")
            else:
                console.print_json(data=result)
        else:
            console.print(
                Panel(
                    text,
                    title="[bold green]识别结果[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )

            duration = data.get("result", {}).get("duration")
            if duration:
                console.print(f"\n[dim]音频时长: {duration / 1000:.1f} 秒[/dim]")

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]✓[/green] 结果已保存到: {output}")

    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()
