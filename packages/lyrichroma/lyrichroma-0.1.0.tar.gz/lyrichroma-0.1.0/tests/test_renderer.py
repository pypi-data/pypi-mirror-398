from lyrichroma.renderer import SubtitleRenderer
from lyrichroma.types import SimpleSegment

# Mock imports if necessary, but we can test logic without moviepy heavy lifting if we stick to methods


def test_get_current_segment():
    renderer = SubtitleRenderer()

    seg1 = SimpleSegment(0.0, 5.0, "hello")
    seg2 = SimpleSegment(5.5, 10.0, "world")
    segments = [seg1, seg2]

    # Hit
    assert renderer._get_current_segment(2.5, segments) == seg1
    assert renderer._get_current_segment(7.0, segments) == seg2

    # Miss
    assert renderer._get_current_segment(5.2, segments) is None
    assert renderer._get_current_segment(11.0, segments) is None


# Ideally we mock ImageFont to avoid system font dependency issues in CI
# But the renderer has a fallback.
