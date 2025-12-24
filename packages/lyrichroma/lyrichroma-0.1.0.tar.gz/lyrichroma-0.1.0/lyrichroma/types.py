class SimpleWord:
    def __init__(self, start, end, word, probability):
        self.start = start
        self.end = end
        self.word = word
        self.probability = probability

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "word": self.word,
            "probability": self.probability,
        }

    @staticmethod
    def from_dict(data):
        return SimpleWord(data["start"], data["end"], data["word"], data["probability"])


class SimpleSegment:
    def __init__(self, start, end, text, words=None):
        self.start = start
        self.end = end
        self.text = text
        self.words = (
            [SimpleWord.from_dict(w) if isinstance(w, dict) else w for w in words]
            if words
            else []
        )

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "words": [w.to_dict() for w in self.words],
        }

    @staticmethod
    def from_dict(data):
        return SimpleSegment(
            data["start"], data["end"], data["text"], data.get("words")
        )
