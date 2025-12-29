# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2024-12-24

### Added
- 🔗 **Context 上下文追踪支持**: 所有 Client 支持传入 Context 对象
  - 在 Client 初始化时可选传入 `ctx` 参数
  - Context 信息自动注入到 HTTP 请求头
  - 支持请求链路追踪、日志关联等场景
  - 向后兼容,不传入 Context 不影响正常使用
- 📝 **文档更新**:
  - README 新增"上下文追踪"章节
  - 新增 `examples/context_example.py` 示例文件
  - 展示 Context 的三种使用场景

### Changed
- 🔧 **依赖更新**: 添加 `coze-coding-utils>=0.1.0` 依赖
- 🏗️ **架构优化**: 
  - BaseClient 支持 Context 参数
  - 所有 Client 类统一支持 Context 初始化
  - LLMClient 在创建 ChatOpenAI 时自动注入 Context headers

### Supported Clients
所有以下 Client 均支持 Context:
- `ImageGenerationClient` - 图片生成
- `VideoGenerationClient` - 视频生成
- `LLMClient` - 大语言模型
- `SearchClient` - 联网搜索
- `TTSClient` - 语音合成
- `ASRClient` - 语音识别

## [0.3.0] - 2024-12-24

### Added
- 🛠️ **CLI 工具集成**: 将 `coze-coding-cli` 集成到 SDK 包中
  - 新增 `coze_coding_dev_sdk.cli` 模块
  - 提供 `coze-coding-ai` 命令行工具
  - 支持图片生成命令: `coze-coding-ai image`
  - 支持视频生成命令: `coze-coding-ai video`
  - 支持任务状态查询: `coze-coding-ai video-status`
- 📦 **可选依赖**: 新增 `[cli]` 可选依赖组
  - `click>=8.0.0` - CLI 框架
  - `rich>=13.0.0` - 终端 UI
- 🖼️ **图片生成增强**:
  - 图生图功能支持单个或多个参考图片
  - 尺寸验证: 仅支持 2K/4K 或 2560-4096 范围
  - 超出范围自动使用默认 2K

### Changed
- 📝 更新 README 文档,添加 CLI 使用说明
- 🔄 优化包描述,强调 CLI 工具功能

### Installation
```bash
# 仅 SDK
pip install coze-coding-dev-sdk

# SDK + CLI
pip install coze-coding-dev-sdk[cli]
```

## [0.2.0] - 2025-12-19

### Added
- 🎬 视频生成模块（VideoGenerationClient）
  - 支持文本生成视频（text-to-video）
  - 支持图片生成视频（image-to-video）
  - 支持首帧、尾帧和参考图片
  - 异步任务轮询机制
- 🤖 大语言模型模块（LLMClient）
  - 支持流式和非流式对话
  - 支持思考链（thinking）
  - 支持缓存机制
  - 集成 LangChain
- 🔍 联网搜索模块（SearchClient）
  - Web 搜索功能
  - Web 搜索 + AI 总结
  - 图片搜索功能
- 📦 完善的 PyPI 发布配置
  - 添加 LICENSE（MIT）
  - 添加 MANIFEST.in
  - 完善 pyproject.toml 元数据

### Changed
- 优化项目结构，模块化设计
- 更新 README 文档
- 改进异常处理机制

## [0.1.0] - 2025-12-18

### Added
- 🎨 图片生成模块（ImageGenerationClient）
  - 支持 2K/4K 分辨率
  - 同步/异步双模式
  - 批量并发生成
  - 参考图片风格迁移
- 🎙️ 语音合成模块（TTSClient）
  - 30+ 音色选择
  - 支持 SSML 格式
  - 可调节语速和音量
  - 流式返回
- 🎧 语音识别模块（ASRClient）
  - 支持 URL 和 Base64 输入
  - 多种音频格式
  - 详细时间戳信息
- 🏗️ 核心基础设施
  - BaseClient 基础客户端
  - Config 统一配置管理
  - 完整的异常体系
  - 自动重试机制
- 📊 可观测性
  - 集成 cozeloop 监控
  - API 调用追踪

### Infrastructure
- 基于 Pydantic 的类型安全
- 完整的类型提示
- 模块化架构设计

[0.2.0]: https://github.com/coze/coze-sdk/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/coze/coze-sdk/releases/tag/v0.1.0
