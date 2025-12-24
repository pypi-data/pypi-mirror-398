# LyriChroma：一键将音频转换为带卡拉OK字幕的视频神器（支持中英双语）

作为一名内容创作者，你是否曾想过把播客、讲座录音或者歌曲demo快速转换成可以在社交媒体分享的视频？又或者你想为你的视频配上精准同步的字幕，甚至实现卡拉OK效果？今天我要给大家介绍一款我最近发现并深度使用的开源工具——LyriChroma，它可以帮你轻松实现这些想法。

## 什么是 LyriChroma？

LyriChroma 是一个基于 Python 开发的强大工具，它的核心功能是将音频文件自动转换为带有同步字幕的视频。最吸引人的是，它不仅能生成普通的字幕，还能实现类似卡拉OK的效果——正在朗读的词语会被高亮显示，非常适合制作音乐视频、教学视频或者播客视频。

## 主要功能一览

在详细介绍如何使用之前，让我们先来看看 LyriChroma 的主要特性：

1. **自动语音识别（ASR）**：基于 `faster-whisper` 引擎，支持多种语言（包括中文），并提供词级别的时间戳
2. **动态背景效果**：内置多种炫酷的动态背景，比如极光、日落、海洋、赛博朋克和森林主题
3. **卡拉OK样式字幕**：实时高亮当前朗读的单词，营造卡拉OK效果
4. **高度可定制化**：支持调整字体大小、颜色、高亮颜色和字幕位置
5. **字幕编辑功能**：可导出字幕为 JSON 文件进行人工校对，再重新导入生成完美视频

## 安装步骤

LyriChroma 使用现代化的 Python 包管理工具 `uv` 进行管理，安装非常简单：

```bash
# 首先安装 uv（如果尚未安装）
pip install uv

# 克隆项目并同步依赖
uv sync
```

就是这么简单！接下来我们就可以开始使用了。

## 基础使用方法

最基本的用法只需要一行命令：

```bash
uv run lyrichroma --input audio.mp3 --output video.mp4
```

这条命令会将 audio.mp3 转换为 video.mp4，并配有黑色背景和白色字幕。

## 进阶使用技巧

### 1. 动态背景效果

如果你觉得纯色背景太单调，LyriChroma 内置了几种炫酷的动态背景：

```bash
uv run lyrichroma --input audio.mp3 --output video.mp4 --bg-type dynamic --bg-value aurora
```

目前支持的调色板包括：
- `aurora`（极光效果，默认）
- `sunset`（日落效果）
- `ocean`（海洋效果）
- `cyberpunk`（赛博朋克效果）
- `forest`（森林效果）

### 2. 自定义静态背景

除了动态背景，你还可以使用纯色或图片作为背景：

```bash
# 使用纯色背景
uv run lyrichroma --input audio.mp3 --output video.mp4 --bg-type color --bg-value "#FF5733"

# 使用图片背景
uv run lyrichroma --input audio.mp3 --output video.mp4 --bg-type image --bg-value background.jpg
```

### 3. 字幕样式定制

LyriChroma 提供了丰富的字幕样式定制选项：

```bash
uv run lyrichroma \
  --input audio.mp3 \
  --output video.mp4 \
  --font-size 60 \
  --font-color "#FFFFFF" \
  --highlight-color "#FF0000" \
  --text-y 0.8
```

各参数含义：
- `--font-size`：设置字幕字体大小（默认40）
- `--font-color`：设置字幕颜色（默认白色）
- `--highlight-color`：设置当前朗读词的高亮颜色（默认黄色）
- `--text-y`：设置字幕垂直位置，范围0.0（顶部）到1.0（底部）（默认0.8）

### 4. 字幕编辑工作流

对于需要精确控制字幕内容的场景，LyriChroma 提供了字幕编辑工作流，这是该工具的一大亮点。由于自动语音识别技术并非完美，有时会出现识别错误，这时就需要人工干预。

LyriChroma 的字幕编辑工作流分为三步：

第一步：只生成字幕文件（不生成视频）：
```bash
uv run lyrichroma --input audio.mp3 --save-transcript transcript.json
```

执行这个命令后，你会得到一个名为 `transcript.json` 的文件，它包含了所有的识别结果和时间戳信息。

第二步：手动编辑生成的 `transcript.json` 文件

打开这个 JSON 文件，你会发现它的结构类似于：
```json
[
  {
    "start": 0.0,
    "end": 3.0,
    "text": "你好世界",
    "words": [
      {
        "start": 0.0,
        "end": 1.5,
        "word": "你好",
        "probability": 0.9
      },
      {
        "start": 1.5,
        "end": 3.0,
        "word": "世界",
        "probability": 0.85
      }
    ]
  }
]
```

在这个文件中，你可以：
1. 更正识别错误的文字内容
2. 调整时间戳以改善同步效果
3. 删除不必要的段落
4. 添加遗漏的内容

例如，如果某个词被错误识别，你可以直接修改对应的 `word` 或 `text` 字段。如果你发现某个时间段的字幕时间不对，可以调整 `start` 和 `end` 时间戳。

第三步：使用编辑后的字幕生成视频：
```bash
uv run lyrichroma --input audio.mp3 --output video.mp4 --load-transcript transcript.json
```

这样就能生成带有经过人工修正的高质量字幕的视频了。

这种方式特别适合需要对自动识别结果进行校正的场景，比如：
- 专业术语识别不准确
- 人名、地名识别错误
- 方言口音导致的识别偏差
- 背景噪音影响识别准确性

### 5. Whisper 模型选择

LyriChroma 默认使用 `base` 模型，你也可以根据需要选择其他模型：

```bash
uv run lyrichroma --input audio.mp3 --output video.mp4 --model-size large
```

支持的模型包括：
- `tiny`：最快但精度最低
- `base`：平衡速度和精度（默认）
- `small`：较好的精度
- `medium`：高精度
- `large`：最高精度但速度较慢

注意：更大的模型需要更多的内存和计算资源。

## 完整参数说明

为了方便查阅，这里列出所有可用参数：

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--input`, `-i` | 输入音频文件路径 | 必填 |
| `--output`, `-o` | 输出视频文件路径 | 可选 |
| `--bg-type` | 背景类型（`color`、`image` 或 `dynamic`） | `color` |
| `--bg-value` | 背景值（十六进制颜色、图片路径或调色板名称） | `#000000` 或 `aurora` |
| `--model-size` | Whisper 模型大小（tiny、base、small、medium、large） | `base` |
| `--device` | 运行 Whisper 的设备（cpu、cuda） | `cpu` |
| `--save-transcript` | 保存转录结果为 JSON 的路径 | 无 |
| `--load-transcript` | 加载 JSON 转录结果的路径 | 无 |
| `--font-size` | 字幕字体大小 | 40 |
| `--font-color` | 字幕颜色 | `white` |
| `--highlight-color` | 当前单词的高亮颜色 | `yellow` |
| `--text-y` | 文字垂直位置（0.0=顶部, 1.0=底部） | 0.8 |

## 实际应用场景

LyriChroma 在很多场景下都非常有用：

1. **播客视频化**：将播客音频转换为带字幕的视频，便于在 YouTube、B站等平台传播
2. **教学材料制作**：为在线课程添加同步字幕，提升学习体验
3. **音乐分享**：为歌曲创作卡拉OK效果的视频
4. **会议记录整理**：将会议录音转换为带字幕的回顾视频
5. **语言学习**：通过卡拉OK样式字幕帮助语言学习者跟读练习

## 总结

LyriChroma 是一款功能强大且易于使用的音视频转换工具。它不仅实现了基础的音频转视频功能，还提供了丰富的定制选项和专业级的字幕效果。特别是对中英双语的良好支持，使得它在国际化使用场景中表现出色。

无论你是内容创作者、教育工作者还是普通用户，LyriChroma 都能帮你轻松制作出专业的带字幕视频内容。赶快试试吧！

项目地址：[https://github.com/your-repo/lyrichroma](https://github.com/your-repo/lyrichroma)

> 欢迎在评论区分享你的使用体验或者提出改进建议！