# LyriChroma

[English Documentation](README.md)

一个强大的工具，可以将音频文件转换为带有自动生成、同步且高亮显示字幕（卡拉 OK 风格）的视频。

## 功能特性

- **自动转录**：使用 `faster-whisper` 进行高精度的语音转文本，并提供字级别的精确时间戳。
- **动态背景**：带有可选调色板的动态渐变背景（等离子/极光效果）。
- **卡拉OK字幕**：实时高亮显示当前播放的单词。
- **高度可定制**：可调整字体大小、颜色、高亮颜色以及字幕位置。
- **字幕编辑**：支持导出字幕为 JSON 格式进行手动校对，然后重新导入以生成完美的视频。

## 安装指南

本项目使用 `uv` 进行管理。

```bash
# 如果尚未安装 uv，请先安装 (https://github.com/astral-sh/uv)
pip install uv

# 克隆项目并同步依赖
uv sync
```

## 使用方法

### 基础用法
将音频转换为视频（默认黑色背景）：
```bash
uv run lyrichroma --input audio.mp3 --output video.mp4
```

### 进阶用法

#### 1. 动态背景
生成带有炫酷动态背景的视频：
```bash
uv run lyrichroma --input audio.mp3 --output video.mp4 --bg-type dynamic --bg-value aurora
```
可用调色板：`aurora` (默认), `sunset`, `ocean`, `cyberpunk`, `forest`。

#### 2. 字幕编辑工作流
1. 生成字幕 JSON（跳过视频生成）：
    ```bash
    uv run lyrichroma --input audio.mp3 --save-transcript transcript.json
    ```
2. 手动编辑 `transcript.json` 文件。
3. 使用编辑后的字幕生成视频：
    ```bash
    uv run lyrichroma --input audio.mp3 --output video.mp4 --load-transcript transcript.json
    ```

#### 3. 样式定制
自定义字幕的显示效果：
```bash
uv run lyrichroma \
  --input audio.mp3 \
  --output video.mp4 \
  --font-size 60 \
  --font-color "#FFFFFF" \
  --highlight-color "#FF0000" \
  --text-y 0.8
```

## 参数说明

| 参数 | 描述 | 默认值 |
|----------|-------------|---------|
| `--input`, `-i` | 输入音频文件路径 | 必填 |
| `--output`, `-o` | 输出视频文件路径 | 选填 |
| `--bg-type` | 背景类型 (`color`, `image` 或 `dynamic`) | `color` |
| `--bg-value` | 背景值 (Hex 颜色、图片路径或调色板名: `aurora`, `sunset`, `ocean`, `cyberpunk`, `forest`) | `#000000` 或 `aurora` |
| `--model-size` | Whisper 模型大小 (tiny, base, large-v2 等) | `base` |
| `--save-transcript` | 保存转录结果为 JSON 的路径 | 无 |
| `--load-transcript` | 加载 JSON 转录结果的路径 | 无 |
| `--font-size` | 字幕字体大小 | 40 |
| `--font-color` | 字幕颜色 | `white` |
| `--highlight-color` | 当前单词的高亮颜色 | `yellow` |
| `--text-y` | 文字垂直位置 (0.0=顶部, 1.0=底部) | 0.8 |

## 测试

运行单元测试：
```bash
uv run pytest
```

## 高级配置

### 可插拔 ASR (语音识别)
Lyrichroma 支持可插拔的 ASR 架构。默认情况下，它使用 `faster-whisper`。
你可以通过继承 `lyrichroma.asr.base.ASRProvider` 并将其传递给 `Transcriber` 来实现你自己的 ASR 提供商（例如 OpenAI API）。

## 开发指南

1. **安装依赖**: `uv sync`
2. **运行测试**: `uv run pytest`
3. **代码格式化与检查**:
   ```bash
   uv run ruff check .
   uv run black .
   ```
4. **Pre-commit 钩子**:
   安装钩子以便在提交前自动检查代码：
   ```bash
   uv run pre-commit install
   ```
