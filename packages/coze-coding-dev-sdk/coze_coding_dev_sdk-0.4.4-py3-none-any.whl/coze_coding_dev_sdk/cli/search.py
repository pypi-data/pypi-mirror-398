import json
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from ..search import SearchClient
from ..core.config import Config

console = Console()


def display_web_results_table(response, show_url: bool = True):
    """使用 Rich 表格显示 Web 搜索结果"""
    if not response.web_items:
        console.print("[yellow]没有找到搜索结果[/yellow]")
        return
    
    table = Table(title="Web 搜索结果", show_header=True, header_style="bold cyan")
    table.add_column("序号", style="dim", width=6)
    table.add_column("标题", style="bold")
    table.add_column("站点", style="cyan", width=15)
    table.add_column("摘要", style="white")
    if show_url:
        table.add_column("URL", style="blue", width=40)
    
    for idx, item in enumerate(response.web_items, 1):
        title = item.title[:50] + "..." if len(item.title) > 50 else item.title
        site = item.site_name or "未知"
        snippet = item.snippet[:80] + "..." if len(item.snippet) > 80 else item.snippet
        
        row = [str(idx), title, site, snippet]
        if show_url:
            url = item.url[:40] + "..." if item.url and len(item.url) > 40 else (item.url or "")
            row.append(url)
        
        table.add_row(*row)
    
    console.print(table)
    
    if response.summary:
        console.print()
        console.print(Panel(
            Markdown(response.summary),
            title="[bold green]AI 摘要[/bold green]",
            border_style="green"
        ))
    
    console.print(f"\n[green]✓[/green] 找到 {len(response.web_items)} 条结果")


def display_image_results_table(response):
    """使用 Rich 表格显示图片搜索结果"""
    if not response.image_items:
        console.print("[yellow]没有找到图片结果[/yellow]")
        return
    
    table = Table(title="图片搜索结果", show_header=True, header_style="bold magenta")
    table.add_column("序号", style="dim", width=6)
    table.add_column("标题", style="bold")
    table.add_column("站点", style="cyan", width=15)
    table.add_column("图片 URL", style="blue")
    table.add_column("尺寸", style="yellow", width=12)
    
    for idx, item in enumerate(response.image_items, 1):
        title = item.title[:40] + "..." if item.title and len(item.title) > 40 else (item.title or "无标题")
        site = item.site_name or "未知"
        image_url = item.image.url[:50] + "..." if len(item.image.url) > 50 else item.image.url
        size = f"{item.image.width}x{item.image.height}" if item.image.width and item.image.height else "未知"
        
        table.add_row(str(idx), title, site, image_url, size)
    
    console.print(table)
    console.print(f"\n[green]✓[/green] 找到 {len(response.image_items)} 张图片")


def display_simple_format(response):
    """简单文本格式输出"""
    if response.web_items:
        for idx, item in enumerate(response.web_items, 1):
            console.print(f"[{idx}] {item.title} - {item.site_name or '未知'}")
            if item.url:
                console.print(f"    {item.url}")
            console.print(f"    {item.snippet}")
            console.print()
        
        if response.summary:
            console.print("=" * 60)
            console.print("AI 摘要:")
            console.print(response.summary)
            console.print("=" * 60)
    
    if response.image_items:
        for idx, item in enumerate(response.image_items, 1):
            console.print(f"[{idx}] {item.title or '无标题'} - {item.site_name or '未知'}")
            console.print(f"    图片: {item.image.url}")
            if item.image.width and item.image.height:
                console.print(f"    尺寸: {item.image.width}x{item.image.height}")
            console.print()


def save_to_json(response, output_path: str):
    """保存结果到 JSON 文件"""
    data = response.model_dump()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓[/green] 结果已保存到: {output_path}")


@click.command()
@click.argument("query")
@click.option("--type", "-t", type=click.Choice(["web", "image", "web_summary"]), default="web", help="搜索类型: web(网页), image(图片), web_summary(网页+AI摘要)")
@click.option("--count", "-c", default=10, help="返回结果数量")
@click.option("--summary", "-s", is_flag=True, help="是否需要 AI 摘要 (仅 web 类型)")
@click.option("--need-content", is_flag=True, help="仅返回有正文的结果 (仅 web 类型)")
@click.option("--need-url", is_flag=True, help="仅返回有原文链接的结果 (仅 web 类型)")
@click.option("--sites", help="指定搜索的站点范围,逗号分隔 (仅 web 类型)")
@click.option("--block-hosts", help="屏蔽的站点,逗号分隔 (仅 web 类型)")
@click.option("--time-range", help="发文时间范围,如: 1d, 1w, 1m (仅 web 类型)")
@click.option("--output", "-o", type=click.Path(), help="输出 JSON 文件路径")
@click.option("--format", "-f", type=click.Choice(["table", "json", "simple"]), default="table", help="输出格式")
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="自定义 HTTP 请求头 (格式: 'Key: Value' 或 'Key=Value'，可多次使用)",
)
@click.option("--verbose", "-v", is_flag=True, help="显示详细的 HTTP 请求日志")
def search(query, type, count, summary, need_content, need_url, sites, block_hosts, time_range, output, format, header, verbose):
    """联网搜索

    支持三种搜索类型:
    - web: 普通网页搜索 (默认)
    - image: 图片搜索
    - web_summary: 网页搜索 + AI 智能摘要

    示例:
        # 网页搜索
        coze-coding-ai search "AI 最新进展"
        coze-coding-ai search "AI 最新进展" --type web --count 20 --summary
        
        # 图片搜索
        coze-coding-ai search "可爱的猫咪" --type image
        coze-coding-ai search "可爱的猫咪" -t image -c 20
        
        # 网页搜索 + AI 摘要
        coze-coding-ai search "量子计算原理" --type web_summary
        coze-coding-ai search "量子计算原理" -t web_summary -c 15
        
        # 高级过滤
        coze-coding-ai search "Python 教程" --sites "python.org,github.com" --need-content
        coze-coding-ai search "新闻" --time-range "1d" --need-url
    """
    try:
        from .utils import parse_headers

        config = Config()
        custom_headers = parse_headers(header)
        client = SearchClient(config, custom_headers=custom_headers, verbose=verbose)
        
        if type == "image":
            console.print(f"[bold magenta]正在搜索图片:[/bold magenta] {query}")
            response = client.image_search(query=query, count=count)
        elif type == "web_summary":
            console.print(f"[bold cyan]正在搜索并生成摘要:[/bold cyan] {query}")
            response = client.web_search_with_summary(query=query, count=count)
        else:
            console.print(f"[bold cyan]正在搜索:[/bold cyan] {query}")
            response = client.search(
                query=query,
                search_type="web",
                count=count,
                need_content=need_content,
                need_url=need_url,
                sites=sites,
                block_hosts=block_hosts,
                need_summary=summary,
                time_range=time_range
            )
        
        if format == "json":
            console.print_json(data=response.model_dump())
        elif format == "simple":
            display_simple_format(response)
        else:
            if type == "image":
                display_image_results_table(response)
            else:
                display_web_results_table(response, show_url=True)
        
        if output:
            save_to_json(response, output)
    
    except Exception as e:
        console.print(f"[red]✗ 错误: {str(e)}[/red]")
        raise click.Abort()
