from abc import ABC, abstractmethod
from typing import List
from lyrichroma.types import SimpleSegment


class ASRProvider(ABC):
    """Abstract base class for ASR providers."""

    @abstractmethod
    def transcribe(self, audio_path: str) -> List[SimpleSegment]:
        """
        Transcribe the given audio file and return a list of SimpleSegment objects.
        """
        pass
