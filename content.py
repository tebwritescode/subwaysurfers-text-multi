"""
Input content handling.

Turns raw user input into the plain text that the TTS backends narrate.
If the input is a URL the article body is extracted with goose3; otherwise the
text is returned unchanged. This is intentionally backend-agnostic so every TTS
backend receives the same already-extracted text.
"""

import logging

import validators

logger = logging.getLogger(__name__)


def is_url(text):
    """Return True if ``text`` is a valid URL."""
    return bool(validators.url((text or "").strip()))


def extract_text(source):
    """
    Resolve user input to narratable text.

    Args:
        source (str): Either a URL to an article or direct text content.

    Returns:
        str: The extracted article text, or the original text if not a URL.

    Raises:
        ValueError: If a URL was given but no readable text could be extracted.
    """
    if not is_url(source):
        return source

    # Imported lazily so the (heavy) goose3 dependency is only loaded when a URL
    # is actually submitted.
    from goose3 import Goose

    logger.info("Extracting article text from URL")
    goose = Goose()
    try:
        article = goose.extract(url=source.strip())
        text = (article.cleaned_text or "").strip()
    finally:
        goose.close()

    if not text:
        raise ValueError("No readable text could be extracted from the URL.")
    return text
