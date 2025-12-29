# Coze Coding Dev SDK

> 优雅、模块化的多功能 AI SDK，支持图片生成、视频生成、语音合成、语音识别、大语言模型和联网搜索。同时提供强大的命令行工具 `coze-coding-ai`。

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/coze-coding-dev-sdk.svg)](https://pypi.org/project/coze-coding-dev-sdk/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/coze-coding-dev-sdk.svg)](https://pypi.org/project/coze-coding-dev-sdk/)

## ✨ 特性

- 🎨 **图片生成** - 基于豆包 SeeDream 模型的高质量图片生成 (2K/4K)
- 🎬 **视频生成** - 文本/图片生成视频，支持多种模型和配置
- 🤖 **大语言模型** - 支持流式对话、思考链、缓存机制
- 🔍 **联网搜索** - Web 搜索、AI 总结、图片搜索
- 🎙️ **语音合成 (TTS)** - 多音色、高质量的文本转语音
- 🎧 **语音识别 (ASR)** - 快速准确的语音转文字
- 🏗️ **模块化设计** - 清晰的模块划分，易于扩展
- 🔒 **类型安全** - 完整的类型提示
- 🔄 **自动重试** - 内置重试机制
- 📊 **可观测性** - 集成 cozeloop 监控
- 🛠️ **命令行工具** - 提供 `coze-coding-ai` CLI 工具，快速使用 AI 功能

## 📦 安装

### 仅安装 SDK

```bash
pip install coze-coding-dev-sdk
```

### 安装 SDK + CLI 工具

```bash
pip install coze-coding-dev-sdk[cli]
```

### 开发安装

```bash
git clone https://github.com/coze/coze-coding-dev-sdk.git
cd coze-coding-dev-sdk/packages/python
pip install -e ".[dev]"
```

## 🚀 快速开始

### 环境配置

#### 必需配置

```bash
export COZE_WORKLOAD_IDENTITY_API_KEY="your_api_key"
export COZE_INTEGRATION_BASE_URL="https://api.coze.com"
export COZE_INTEGRATION_MODEL_BASE_URL="https://model.coze.com"
```

#### 可选配置（Cozeloop 监控）

如果需要使用扣子罗盘（Cozeloop）进行模型监控和可观测性追踪，需要额外配置：

```bash
export COZELOOP_WORKSPACE_ID="your_workspace_id"
export COZELOOP_API_TOKEN="your_api_token"
```

**获取 workspace_id 的方法：**

1. 登录扣子罗盘平台
2. 在项目设置或工作区设置中找到 `workspace_id`
3. 复制该 ID 并设置到环境变量中

**注意：** 如果不配置 Cozeloop 相关环境变量，会看到警告信息，但不影响 SDK 的正常使用。

### 图片生成

```python
from coze_coding_dev_sdk import ImageGenerationClient, ImageConfig

client = ImageGenerationClient()

files, response = client.generate(
    prompt="一只可爱的橘猫坐在窗台上",
    config=ImageConfig(size="4K", watermark=False)
)

print(f"图片 URL: {response.image_urls}")
```

### 视频生成

```python
from coze_coding_dev_sdk import VideoGenerationClient, VideoConfig

client = VideoGenerationClient()

task = client.text_to_video(
    prompt="一只可爱的小猫在草地上玩耍",
    config=VideoConfig(resolution="1080p", ratio="16:9", duration=5)
)

print(f"视频 URL: {task.video_url}")
```

### 大语言模型

```python
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import HumanMessage

client = LLMClient()

messages = [HumanMessage(content="你好，介绍一下你自己")]

for chunk in client.stream(messages=messages):
    if chunk.content:
        print(chunk.content, end="", flush=True)
```

### 联网搜索

```python
from coze_coding_dev_sdk import SearchClient

client = SearchClient()

results = client.web_search("Python 最新特性")
for item in results:
    print(f"{item.title}: {item.url}")
```

### 语音合成 (TTS)

```python
from coze_coding_dev_sdk import TTSClient

client = TTSClient()

audio_file, size = client.synthesize(
    uid="user123",
    text="你好，欢迎使用 Coze SDK！",
    speaker="zh_female_xiaohe_uranus_bigtts"
)

print(f"音频文件: {audio_file.url}")
```

### 语音识别 (ASR)

```python
from coze_coding_dev_sdk import ASRClient

client = ASRClient()

text, data = client.recognize(
    uid="user123",
    url="https://example.com/audio.mp3"
)

print(f"识别结果: {text}")
```

### 上下文追踪 (Context)

SDK 支持通过 Context 对象进行请求追踪和上下文管理。Context 会自动注入到 HTTP 请求头中，用于链路追踪、日志关联等场景。

```python
from coze_coding_dev_sdk import ImageGenerationClient
from coze_coding_utils.runtime_ctx.context import Context

# 创建 Context 对象
ctx = Context(
    request_id="req-123456",
    trace_id="trace-789",
    user_id="user-001"
)

# 在初始化 Client 时传入 ctx
client = ImageGenerationClient(ctx=ctx)

# 后续所有请求都会自动携带 Context 信息
response = client.generate(prompt="一只可爱的小猫")
```

**支持 Context 的所有 Client：**

- `ImageGenerationClient` - 图片生成
- `VideoGenerationClient` - 视频生成
- `LLMClient` - 大语言模型
- `SearchClient` - 联网搜索
- `TTSClient` - 语音合成
- `ASRClient` - 语音识别

**注意事项：**

- Context 参数是可选的，不传入时不影响正常使用
- Context 只在 Client 初始化时传入，不需要在每个方法中传递
- Context 信息会通过 `default_headers()` 自动转换为 HTTP 请求头

## 📁 项目结构

```
coze-coding-dev-sdk/
├── coze_coding_dev_sdk/          # SDK 主包
│   ├── core/                # 核心层（配置、异常、基础客户端）
│   ├── image/               # 图片生成模块
│   ├── video/               # 视频生成模块
│   ├── llm/                 # 大语言模型模块
│   ├── search/              # 联网搜索模块
│   └── voice/               # 语音模块（TTS + ASR）
├── examples/                # 使用示例
│   ├── image_examples/      # 图片生成示例
│   ├── video_examples/      # 视频生成示例
│   ├── llm_examples/        # LLM 示例
│   ├── search_examples/     # 搜索示例
│   └── voice_examples/      # 语音功能示例
├── LICENSE                  # MIT 许可证
├── CHANGELOG.md             # 版本变更记录
└── README.md                # 项目文档
```

## 🎯 核心模块

### 1. 图片生成 (Image)

```python
from coze_coding_dev_sdk import ImageGenerationClient, ImageConfig

client = ImageGenerationClient()

files, response = client.generate(
    prompt="壮丽的雪山日出",
    config=ImageConfig(size="4K", watermark=False)
)

results = await client.batch_generate([
    {"prompt": "春天的樱花", "size": "2K"},
    {"prompt": "夏日的海滩", "size": "4K"},
])
```

**功能特性：**

- 支持 2K/4K 或自定义尺寸
- 同步/异步双模式
- 批量并发生成
- 参考图片风格迁移
- 组图生成

### 2. 视频生成 (Video)

```python
from coze_coding_dev_sdk import VideoGenerationClient, VideoConfig

client = VideoGenerationClient()

task = client.image_to_video(
    prompt="小猫从坐着到站起来",
    first_frame_url="https://example.com/cat_sitting.jpg",
    last_frame_url="https://example.com/cat_standing.jpg",
    config=VideoConfig(resolution="1080p", duration=5)
)
```

**功能特性：**

- 文本生成视频（text-to-video）
- 图片生成视频（image-to-video）
- 支持首帧、尾帧、参考图片
- 异步任务轮询
- 多种分辨率和比例

### 3. 大语言模型 (LLM)

```python
from coze_coding_dev_sdk import LLMClient

client = LLMClient()

response = client.chat(
    messages=[{"role": "user", "content": "解释量子计算"}],
    enable_thinking=True,
    enable_cache=True
)

for chunk in client.chat_stream(messages=[...]):
    print(chunk, end="")
```

**功能特性：**

- 流式和非流式对话
- 思考链（thinking）
- 缓存机制
- 多模态支持
- 集成 LangChain

### 4. 联网搜索 (Search)

```python
from coze_coding_dev_sdk import SearchClient

client = SearchClient()

web_results = client.web_search("AI 最新进展")

summary, results = client.web_search_with_summary("量子计算原理")

images = client.image_search("可爱的猫咪")
```

**功能特性：**

- Web 搜索
- Web 搜索 + AI 总结
- 图片搜索
- 结构化结果返回

### 5. 语音合成 (TTS)

```python
from coze_coding_dev_sdk import TTSClient, TTSConfig

client = TTSClient()

audio, size = client.synthesize(
    uid="user123",
    text="你好世界",
    speaker="zh_female_xiaohe_uranus_bigtts",
    audio_format="mp3",
    speech_rate=0
)
```

**功能特性：**

- 30+ 音色选择
- 支持 SSML 格式
- 可调节语速和音量
- 多种音频格式（MP3/PCM/OGG）
- 流式返回

### 6. 语音识别 (ASR)

```python
from coze_coding_dev_sdk import ASRClient

client = ASRClient()

text, data = client.recognize(
    uid="user123",
    url="https://example.com/audio.mp3"
)
```

**功能特性：**

- 支持 URL 和 Base64 输入
- 多种音频格式
- 详细的时间戳信息
- 最长 2 小时音频

## 🔧 高级配置

### 统一配置

```python
from coze_coding_dev_sdk import Config, ImageGenerationClient, TTSClient

config = Config(
    api_key="your_api_key",
    base_url="https://api.coze.com",
    retry_times=5,
    retry_delay=2.0,
    timeout=120
)

image_client = ImageGenerationClient(config=config)
tts_client = TTSClient(config=config)
```

### 异常处理

```python
from coze_coding_dev_sdk import (
    CozeSDKError,
    APIError,
    NetworkError,
    ValidationError,
    ConfigurationError
)

try:
    files, response = client.generate(prompt="测试")
except ValidationError as e:
    print(f"参数错误: {e.field} = {e.value}")
except APIError as e:
    print(f"API 错误: {e.message}, 状态码: {e.status_code}")
except NetworkError as e:
    print(f"网络错误: {e}")
except ConfigurationError as e:
    print(f"配置错误: {e.missing_key}")
```

## 💡 使用示例

查看 `examples/` 目录获取更多示例：

- `examples/image_examples/` - 图片生成示例
- `examples/video_examples/` - 视频生成示例
- `examples/llm_examples/` - 大语言模型示例
- `examples/search_examples/` - 联网搜索示例
- `examples/voice_examples/` - 语音功能示例

运行示例：

```bash
python examples/image_examples/simple_example.py
python examples/video_examples/text_to_video.py
python examples/llm_examples/simple_chat.py
python examples/search_examples/web_search.py
python examples/voice_examples/tts_example.py
```

## 🛠️ 命令行工具 (CLI)

安装 CLI 工具后,可以直接在命令行中使用 AI 功能:

```bash
# 安装 CLI
pip install coze-coding-dev-sdk[cli]

# 查看帮助
coze-coding-ai --help
```

### 图片生成

**支持的图片尺寸:**

- `2K` (默认, ~2560x1440)
- `4K` (~3840x2160)
- 自定义: `WIDTHxHEIGHT` (宽度 2560-4096, 高度 1440-4096)

```bash
# 文生图 (默认 2K)
coze-coding-ai image -p "A beautiful landscape" -o "./image.png"

# 4K 分辨率
coze-coding-ai image -p "Professional portrait" -o "./portrait.png" -s 4K

# 图生图
coze-coding-ai image \
  -p "Transform into watercolor style" \
  -i "https://example.com/photo.jpg" \
  -o "./result.png"
```

### 视频生成

```bash
# 文生视频
coze-coding-ai video -p "A cat playing with a ball" --poll

# 图生视频
coze-coding-ai video \
  -i "https://example.com/image.png" \
  -p "Make the scene come alive" \
  --poll

# 查询任务状态
coze-coding-ai video-status <task-id>

# Mock 模式（测试运行，不消耗配额）
coze-coding-ai video -p "Test video" --mock --poll
coze-coding-ai video-status <task-id> --mock
```

### Chat 对话

```bash
# 基础对话
coze-coding-ai chat -p "Hello, how are you?"

# 自定义系统提示词
coze-coding-ai chat \
  -p "Review this code: function add(a,b) { return a+b; }" \
  -s "You are an expert code reviewer" \
  -o review.json

# 启用思考链 (Chain of Thought)
coze-coding-ai chat \
  -p "Solve this math problem: If a train travels 120km in 2 hours, what's its speed?" \
  -t \
  -o solution.json

# 流式输出
coze-coding-ai chat \
  -p "Write a short story about a robot" \
  --stream
```

### 联网搜索

```bash
# 网页搜索（默认）
coze-coding-ai search "AI 最新进展"

# 网页搜索 + 指定结果数量
coze-coding-ai search "Python 教程" --count 20

# 网页搜索 + AI 智能摘要
coze-coding-ai search "量子计算原理" --type web_summary

# 图片搜索
coze-coding-ai search "可爱的猫咪" --type image
coze-coding-ai search "可爱的猫咪" -t image -c 20

# 高级过滤 - 指定站点
coze-coding-ai search "Python 教程" --sites "python.org,github.com"

# 高级过滤 - 屏蔽站点
coze-coding-ai search "新闻" --block-hosts "example.com"

# 高级过滤 - 时间范围（1d=1天, 1w=1周, 1m=1月）
coze-coding-ai search "最新科技" --time-range "1d"

# 高级过滤 - 仅返回有正文的结果
coze-coding-ai search "技术文章" --need-content

# 保存结果到 JSON 文件
coze-coding-ai search "AI 研究" -o results.json

# 不同输出格式
coze-coding-ai search "Python" --format table    # 表格格式（默认）
coze-coding-ai search "Python" --format simple   # 简单文本格式
coze-coding-ai search "Python" --format json     # JSON 格式
```

**搜索类型说明：**

- `web` - 普通网页搜索（默认）
- `image` - 图片搜索
- `web_summary` - 网页搜索 + AI 智能摘要

**高级过滤选项：**

- `--count, -c` - 返回结果数量（默认 10）
- `--summary, -s` - 启用 AI 摘要（仅 web 类型）
- `--need-content` - 仅返回有正文的结果
- `--need-url` - 仅返回有原文链接的结果
- `--sites` - 指定搜索的站点范围（逗号分隔）
- `--block-hosts` - 屏蔽的站点（逗号分隔）
- `--time-range` - 发文时间范围（1d, 1w, 1m）
- `--output, -o` - 保存结果到 JSON 文件
- `--format, -f` - 输出格式（table, json, simple）

更多 CLI 使用说明请查看 [CLI 文档](https://github.com/coze/coze-coding-dev-sdk/blob/main/packages/shell/README.md)

## 📊 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本变更记录。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与贡献。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

基于 Coze AI Integrations 和豆包大模型构建。

## 📞 联系方式

- 项目主页: https://github.com/coze/coze-sdk
- 问题反馈: https://github.com/coze/coze-sdk/issues
- 邮箱: support@coze.com

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐️
