"""
Lightweight offline tests for the core modules.

These avoid network access and external services so they can run in CI. Run
with: ``python -m pytest test_app.py`` (or just ``python test_app.py``).
"""

import captions
import text_to_speech
from cleantext import cleantext
from content import is_url
from sub import _atempo_chain
from text_splitter import split_text_into_sections


def test_backends_registered():
    ids = {b["id"] for b in text_to_speech.available_backends()}
    assert ids == {"tiktok", "elevenlabs", "remote"}


def test_resolve_backend_falls_back():
    assert text_to_speech.resolve_backend("nonsense") == text_to_speech.DEFAULT_BACKEND
    assert text_to_speech.resolve_backend("elevenlabs") == "elevenlabs"


def test_is_url():
    assert is_url("https://example.com/article")
    assert not is_url("just some plain text")


def test_cleantext_removes_urls():
    assert "http" not in cleantext("See https://example.com for details now.")


def test_split_sections_non_empty():
    sections = split_text_into_sections("word " * 500)
    assert sections and all(sections)


def test_estimate_word_timings_monotonic():
    timings = captions.estimate_word_timings("one two three four", 8.0)
    assert len(timings) == 4
    assert timings[0][1] == 0.0
    assert timings[-1][2] <= 8.0 + 1e-6
    starts = [t[1] for t in timings]
    assert starts == sorted(starts)


def test_atempo_chain_handles_extremes():
    assert _atempo_chain(1.0) == "atempo=1.0000"
    # 3.0 and 0.25 are outside a single atempo's 0.5-2.0 range -> chained.
    assert _atempo_chain(3.0).count("atempo=") >= 2
    assert _atempo_chain(0.25).count("atempo=") >= 2


if __name__ == "__main__":
    import sys

    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
