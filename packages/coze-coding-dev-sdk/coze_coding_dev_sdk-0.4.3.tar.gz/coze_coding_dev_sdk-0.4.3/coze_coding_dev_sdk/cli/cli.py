import click

from .chat import chat
from .image import image
from .search import search
from .video import video, video_status
from .voice import asr, tts


@click.group()
@click.version_option(version="0.3.0", prog_name="coze-coding-ai")
def main():
    """Coze Coding CLI - AI-powered tools for video generation and more."""
    pass


main.add_command(video)
main.add_command(video_status, name="video-status")
main.add_command(image)
main.add_command(search)
main.add_command(tts)
main.add_command(asr)
main.add_command(chat)


if __name__ == "__main__":
    main()
