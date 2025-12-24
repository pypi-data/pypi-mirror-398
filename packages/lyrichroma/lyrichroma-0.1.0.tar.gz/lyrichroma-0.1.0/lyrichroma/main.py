import argparse
import sys
import os
from lyrichroma.transcriber import Transcriber
from lyrichroma.renderer import SubtitleRenderer
from lyrichroma.asr.faster_whisper import FasterWhisperASR


def main():
    parser = argparse.ArgumentParser(
        description="Audio to Video Converter with Auto-Subtitles"
    )
    parser.add_argument("--input", "-i", required=True, help="Input audio file path")
    parser.add_argument(
        "--output",
        "-o",
        help="Output video file path (optional, skip to only save transcript)",
    )
    parser.add_argument(
        "--bg-type",
        choices=["color", "image", "dynamic"],
        default="color",
        help="Background type: 'color', 'image', or 'dynamic'",
    )
    parser.add_argument(
        "--bg-value",
        default="#000000",
        help="Background value: Hex color code (e.g. #000000) or Image path",
    )
    parser.add_argument(
        "--model-size",
        default="base",
        help="Whisper model size (tiny, base, small, medium, large)",
    )
    parser.add_argument(
        "--device", default="cpu", help="Device to run Whisper on (cpu, cuda)"
    )

    parser.add_argument("--save-transcript", help="Path to save transcript JSON")
    parser.add_argument(
        "--load-transcript", help="Path to load transcript JSON (skips transcription)"
    )

    # Subtitle customization
    parser.add_argument(
        "--font-size", type=int, default=40, help="Subtitle font size (default: 40)"
    )
    parser.add_argument(
        "--font-color", default="white", help="Subtitle font color (default: white)"
    )
    parser.add_argument(
        "--highlight-color",
        default="yellow",
        help="Highlight color for current word (default: yellow)",
    )
    parser.add_argument(
        "--text-y",
        type=float,
        default=0.8,
        help="Vertical position of text (0.0 top, 1.0 bottom) (default: 0.8)",
    )

    args = parser.parse_args()

    # Validation
    if not args.load_transcript and not os.path.exists(args.input):
        print(f"Error: Input file {args.input} does not exist.")
        sys.exit(1)

    if args.bg_type == "image" and not os.path.exists(args.bg_value):
        print(f"Error: Background image {args.bg_value} does not exist.")
        sys.exit(1)

    # Initialize ASR Provider (defaulting to Faster Whisper)
    asr_provider = FasterWhisperASR(model_size=args.model_size, device=args.device)
    transcriber = Transcriber(provider=asr_provider)

    segments = []

    # 1. Transcribe or Load
    if args.load_transcript:
        try:
            print(f"Loading transcript from {args.load_transcript}...")
            segments = transcriber.load_transcript(args.load_transcript)
        except Exception as e:
            print(f"Error loading transcript: {e}")
            sys.exit(1)
    else:
        try:
            print("Starting transcription...")
            segments = transcriber.transcribe(args.input)

            if args.save_transcript:
                transcriber.save_transcript(segments, args.save_transcript)

        except Exception as e:
            print(f"Error during transcription: {e}")
            sys.exit(1)

    # Check if we should render video
    if not args.output:
        print("No output file specified. Video generation skipped.")
        return

    # 2. Render
    try:
        print("Starting video rendering...")
        renderer = SubtitleRenderer(font_size=args.font_size)
        renderer.generate_video(
            audio_path=args.input,
            segments=segments,
            output_path=args.output,
            bg_type=args.bg_type,
            bg_value=args.bg_value,
            font_color=args.font_color,
            highlight_color=args.highlight_color,
            text_y_ratio=args.text_y,
        )
    except Exception as e:
        print(f"Error during rendering: {e}")
        # traceback.print_exc() # detailed debug
        sys.exit(1)

    print(f"Done! Video saved to {args.output}")


if __name__ == "__main__":
    main()
