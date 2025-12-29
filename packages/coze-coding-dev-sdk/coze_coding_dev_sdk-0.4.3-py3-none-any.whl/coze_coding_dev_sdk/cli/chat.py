import json
import os
from typing import Optional

import click
from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console

from ..core.config import Config
from ..llm import LLMClient

console = Console()


@click.command()
@click.option("--prompt", "-p", required=True, help="User message content")
@click.option("--system", "-s", help="System prompt for custom behavior")
@click.option(
    "--thinking", "-t", is_flag=True, help="Enable chain-of-thought reasoning"
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path (JSON format)"
)
@click.option("--stream", is_flag=True, help="Stream the response in real-time")
def chat(
    prompt: str,
    system: Optional[str],
    thinking: bool,
    output: Optional[str],
    stream: bool,
):
    """Chat with AI using natural language."""
    try:
        config = Config()
        client = LLMClient(config)

        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        thinking_mode = "enabled" if thinking else "disabled"

        console.print(f"[bold cyan]Chat with AI...[/bold cyan]")
        console.print(f"Prompt: [yellow]{prompt}[/yellow]")
        if system:
            console.print(f"System: [blue]{system}[/blue]")
        if thinking:
            console.print(f"Thinking: [green]enabled[/green]")
        console.print()

        if stream:
            console.print("[bold green]Response:[/bold green]")
            full_content = ""
            response_metadata = {}

            for chunk in client.stream(messages=messages, thinking=thinking_mode):
                if chunk.content:
                    console.print(chunk.content, end="")
                    full_content += chunk.content
                if chunk.response_metadata:
                    response_metadata.update(chunk.response_metadata)

            console.print("\n")

            if output:
                result = {
                    "prompt": prompt,
                    "system": system,
                    "thinking": thinking,
                    "response": full_content,
                    "metadata": response_metadata,
                }

                output_dir = os.path.dirname(os.path.abspath(output))
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                with open(output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                console.print(
                    f"[green]✓[/green] Response saved to: [bold]{output}[/bold]"
                )
        else:
            response = client.invoke(messages=messages, thinking=thinking_mode)

            console.print("[bold green]Response:[/bold green]")
            console.print(response.content)
            console.print()

            if output:
                result = {
                    "prompt": prompt,
                    "system": system,
                    "thinking": thinking,
                    "response": response.content,
                    "metadata": response.response_metadata,
                }

                output_dir = os.path.dirname(os.path.abspath(output))
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                with open(output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                console.print(
                    f"[green]✓[/green] Response saved to: [bold]{output}[/bold]"
                )

    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        raise click.Abort()
