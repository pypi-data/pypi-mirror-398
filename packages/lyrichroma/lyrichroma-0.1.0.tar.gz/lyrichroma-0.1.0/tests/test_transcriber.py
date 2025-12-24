import os
from lyrichroma.transcriber import Transcriber
from lyrichroma.types import SimpleSegment, SimpleWord
from lyrichroma.asr.base import ASRProvider


class DummyASR(ASRProvider):
    def transcribe(self, audio_path):
        return []


def test_simple_word_serialization():
    word = SimpleWord(0.0, 1.0, "hello", 0.9)
    data = word.to_dict()
    assert data["word"] == "hello"
    assert data["start"] == 0.0
    assert data["end"] == 1.0
    assert data["probability"] == 0.9

    word2 = SimpleWord.from_dict(data)
    assert word2.word == "hello"
    assert word2.start == 0.0


def test_simple_segment_serialization():
    word1 = SimpleWord(0.0, 0.5, "hello", 0.9)
    word2 = SimpleWord(0.5, 1.0, "world", 0.8)
    seg = SimpleSegment(0.0, 1.0, "hello world", [word1, word2])

    data = seg.to_dict()
    assert len(data["words"]) == 2
    assert data["text"] == "hello world"

    seg2 = SimpleSegment.from_dict(data)
    assert len(seg2.words) == 2
    assert seg2.text == "hello world"
    assert seg2.words[0].word == "hello"


def test_transcriber_save_load(tmp_path):
    # Use dummy provider for testing save/load (no model loading needed)
    transcriber = Transcriber(provider=DummyASR())
    file_path = tmp_path / "test.json"

    word1 = SimpleWord(0.0, 0.5, "hello", 0.9)
    seg = SimpleSegment(0.0, 0.5, "hello", [word1])
    segments = [seg]

    transcriber.save_transcript(segments, str(file_path))
    assert os.path.exists(file_path)

    loaded_segments = transcriber.load_transcript(str(file_path))
    assert len(loaded_segments) == 1
    assert loaded_segments[0].text == "hello"
    assert loaded_segments[0].words[0].word == "hello"
