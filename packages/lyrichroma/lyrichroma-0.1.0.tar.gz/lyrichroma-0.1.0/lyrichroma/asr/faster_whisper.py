from faster_whisper import WhisperModel
import os
from typing import List
from lyrichroma.asr.base import ASRProvider
from lyrichroma.types import SimpleSegment, SimpleWord


class FasterWhisperASR(ASRProvider):
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initialize the Faster Whisper ASR provider.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None  # Lazy load

    def _load_model(self):
        if self.model is None:
            print(f"Loading Whisper model: {self.model_size} on {self.device}...")
            self.model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )

    def transcribe(self, audio_path: str) -> List[SimpleSegment]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()
        print(f"Transcribing {audio_path}...")
        segments, info = self.model.transcribe(audio_path, word_timestamps=True)

        result = []
        for segment in segments:
            words = []
            if segment.words:
                for w in segment.words:
                    words.append(SimpleWord(w.start, w.end, w.word, w.probability))

            s = SimpleSegment(segment.start, segment.end, segment.text, words)
            result.append(s)

        print(f"Transcription complete. Detected language: {info.language}")
        return result
