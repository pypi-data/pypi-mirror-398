from lyrichroma.asr.base import ASRProvider
from lyrichroma.types import SimpleSegment
import os
import json


class Transcriber:
    def __init__(self, provider: ASRProvider):
        """
        Initialize the Transcriber with a pluggable ASR provider.
        Args:
            provider (ASRProvider): The ASR provider instance to use.
        """
        self.provider = provider

    def transcribe(self, audio_path):
        """
        Transcribe audio file using the configured provider.
        """
        return self.provider.transcribe(audio_path)

    def save_transcript(self, segments, path):
        """Save segments to a JSON file."""
        data = [s.to_dict() for s in segments]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Transcript saved to {path}")

    def load_transcript(self, path):
        """Load segments from a JSON file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Transcript file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = [SimpleSegment.from_dict(s) for s in data]
        print(f"Transcript loaded from {path}")
        return segments
