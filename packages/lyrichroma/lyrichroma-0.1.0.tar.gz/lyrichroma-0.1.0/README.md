# LyriChroma

[中文文档](README_zh.md)

A powerful tool to convert audio files into videos with auto-generated, synchronized, and highlighted subtitles (Karaoke style).

## Features

- **Auto Transcription**: Uses `faster-whisper` for high-accuracy speech-to-text with word-level timestamps.
- **Dynamic Backgrounds**: Moving multi-color gradient with selectable palettes (plasma/aurora effects).
- **Karaoke Subtitles**: Real-time highlighting of spoken words.
- **Customizable**: Adjust font size, color, highlight color, and position.
- **Transcript Editing**: Export transcripts to JSON for manual correction, then re-import to generate the perfect video.

## Installation

This project is managed with `uv`.

```bash
# Install uv if you haven't (https://github.com/astral-sh/uv)
pip install uv

# Clone and sync dependencies
uv sync
```

## Usage

### Basic Usage
Convert audio to video with a black background:
```bash
uv run lyrichroma --input audio.mp3 --output video.mp4
```

### Advanced Usage

#### 1. Dynamic Background
Generate a video with a cool moving background:
```bash
uv run lyrichroma --input audio.mp3 --output video.mp4 --bg-type dynamic --bg-value aurora
```
Available palettes: `aurora` (default), `sunset`, `ocean`, `cyberpunk`, `forest`.

#### 2. Transcript Editing Workflow
1. Generate transcript JSON (skip video generation):
    ```bash
    uv run lyrichroma --input audio.mp3 --save-transcript transcript.json
    ```
2. Edit `transcript.json` manually.
3. Generate video from edited transcript:
    ```bash
    uv run lyrichroma --input audio.mp3 --output video.mp4 --load-transcript transcript.json
    ```

#### 3. Styling
Customize the subtitle appearance:
```bash
uv run lyrichroma \
  --input audio.mp3 \
  --output video.mp4 \
  --font-size 60 \
  --font-color "#FFFFFF" \
  --highlight-color "#FF0000" \
  --text-y 0.8
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input`, `-i` | Input audio file path | Required |
| `--output`, `-o` | Output video file path | Optional |
| `--bg-type` | `color`, `image`, or `dynamic` | `color` |
| `--bg-value` | Hex color (`#000000`), image path, or palette name (`aurora`, `sunset`, `ocean`, `cyberpunk`, `forest`) | `#000000` or `aurora` |
| `--model-size` | Whisper model size (tiny, base, large-v2, etc.) | `base` |
| `--save-transcript` | Path to save JSON transcript | None |
| `--load-transcript` | Path to load JSON transcript | None |
| `--font-size` | Subtitle font size | 40 |
| `--font-color` | Text color | `white` |
| `--highlight-color` | Highlight color for active word | `yellow` |
| `--text-y` | Vertical position (0.0=top, 1.0=bottom) | 0.8 |

## Testing

Run unit tests:
```bash
uv run pytest
```

## Advanced Configuration

### Pluggable ASR
Lyrichroma supports a pluggable ASR architecture. By default, it uses `faster-whisper`.
You can implement your own ASR provider by subclassing `lyrichroma.asr.base.ASRProvider` and passing it to the `Transcriber`.

## Development

1. **Install Dependencies**: `uv sync`
2. **Run Tests**: `uv run pytest`
3. **Format & Lint**:
   ```bash
   uv run ruff check .
   uv run black .
   ```
4. **Pre-commit Hooks**:
   Install hooks to automatically check code before committing:
   ```bash
   uv run pre-commit install
   ```
