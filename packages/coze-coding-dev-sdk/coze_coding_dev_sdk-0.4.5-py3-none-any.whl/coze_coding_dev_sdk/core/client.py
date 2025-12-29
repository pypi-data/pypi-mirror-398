import json
import time
from typing import Dict, Optional

import requests
from coze_coding_utils.runtime_ctx.context import Context, default_headers
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .config import Config
from .exceptions import APIError, NetworkError

console = Console()


class BaseClient:
    def __init__(
        self,
        config: Optional[Config] = None,
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        if config is None:
            config = Config()
        self.config = config
        self.ctx = ctx
        self.custom_headers = custom_headers or {}
        self.verbose = verbose

    def _request(
        self, method: str, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> dict:
        request_headers = {}

        if self.ctx is not None:
            ctx_headers = default_headers(self.ctx)
            request_headers.update(ctx_headers)

        if self.custom_headers:
            request_headers.update(self.custom_headers)

        config_headers = self.config.get_headers(headers)
        request_headers.update(config_headers)

        response = self._make_request(
            method=method, url=url, headers=request_headers, **kwargs
        )
        return self._handle_response(response)

    def _request_stream(
        self, method: str, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> requests.Response:
        request_headers = {}

        if self.ctx is not None:
            ctx_headers = default_headers(self.ctx)
            request_headers.update(ctx_headers)

        if self.custom_headers:
            request_headers.update(self.custom_headers)

        config_headers = self.config.get_headers(headers)
        request_headers.update(config_headers)

        kwargs["stream"] = True
        return self._make_request(
            method=method, url=url, headers=request_headers, **kwargs
        )

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        sanitized = headers.copy()
        if "Authorization" in sanitized:
            token = sanitized["Authorization"]
            if token.startswith("Bearer "):
                token = token[7:]
                if len(token) > 16:
                    sanitized["Authorization"] = f"Bearer {token[:8]}...{token[-4:]}"
                else:
                    sanitized["Authorization"] = "Bearer ****"
        return sanitized

    def _log_request(self, method: str, url: str, **kwargs):
        if not self.verbose:
            return

        parts = []
        parts.append(f"[bold cyan]{method}[/bold cyan] {url}\n")

        headers = kwargs.get("headers", {})
        sanitized_headers = self._sanitize_headers(headers)
        if sanitized_headers:
            parts.append("[bold]Headers:[/bold]")
            for key, value in sanitized_headers.items():
                parts.append(f"  {key}: {value}")
            parts.append("")

        if "json" in kwargs and kwargs["json"]:
            parts.append("[bold]Body:[/bold]")
            try:
                json_str = json.dumps(kwargs["json"], ensure_ascii=False, indent=2)
                parts.append("")
            except Exception:
                json_str = str(kwargs["json"])
                parts.append("")

        content = "\n".join(parts)
        console.print(
            Panel(
                content,
                title="[bold green]HTTP Request[/bold green]",
                border_style="green",
            )
        )

        if "json" in kwargs and kwargs["json"]:
            try:
                json_str = json.dumps(kwargs["json"], ensure_ascii=False, indent=2)
                console.print(
                    Syntax(json_str, "json", theme="monokai", line_numbers=False)
                )
                console.print()
            except Exception:
                pass

    def _log_response(self, response: requests.Response, is_stream: bool = False):
        if not self.verbose:
            return

        parts = []
        parts.append(f"[bold]Status:[/bold] {response.status_code} {response.reason}\n")

        if is_stream:
            parts.append("[yellow]⚡ Streaming response - body not shown[/yellow]")
            content = "\n".join(parts)
            console.print(
                Panel(
                    content,
                    title="[bold blue]HTTP Response[/bold blue]",
                    border_style="blue",
                )
            )
            console.print()
            return

        parts.append("[bold]Body:[/bold]")

        content = "\n".join(parts)
        console.print(
            Panel(
                content,
                title="[bold blue]HTTP Response[/bold blue]",
                border_style="blue",
            )
        )

        try:
            response_data = response.json()
            json_str = json.dumps(response_data, ensure_ascii=False, indent=2)
            if len(json_str) > 2000:
                json_str = json_str[:2000] + "\n... (truncated)"
            console.print(Syntax(json_str, "json", theme="monokai", line_numbers=False))
        except Exception:
            body_text = response.text[:500]
            if len(response.text) > 500:
                body_text += "... (truncated)"
            console.print(f"  {body_text}")

        console.print()

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_error = None
        is_stream = kwargs.get("stream", False)

        for attempt in range(self.config.retry_times):
            try:
                if attempt == 0:
                    self._log_request(method, url, **kwargs)

                response = requests.request(
                    method=method, url=url, timeout=self.config.timeout, **kwargs
                )

                if attempt == 0:
                    self._log_response(response, is_stream=is_stream)

                return response

            except requests.exceptions.RequestException as e:
                last_error = NetworkError(str(e), e)
                if attempt < self.config.retry_times - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue

        raise last_error

    def _handle_response(self, response: requests.Response) -> dict:
        try:
            data = response.json()
        except Exception as e:
            raise APIError(
                f"响应解析失败: {str(e)}, 响应内容: {response.text[:200]}",
                status_code=response.status_code,
            )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP 错误: {str(e)}"
            if data:
                error_msg += f", 响应数据: {data}"
            raise APIError(
                error_msg, status_code=response.status_code, response_data=data
            )

        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
