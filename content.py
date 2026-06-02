"""
Input content handling.

Turns raw user input into the plain text that the TTS backends narrate.
If the input is a URL the article body is extracted with goose3; otherwise the
text is returned unchanged. This is intentionally backend-agnostic so every TTS
backend receives the same already-extracted text.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import validators

logger = logging.getLogger(__name__)


def is_url(text):
    """Return True if ``text`` is a valid URL."""
    return bool(validators.url((text or "").strip()))


def is_safe_public_url(url):
    """
    SSRF guard: allow only http/https URLs whose host resolves to public IPs.

    Rejects private, loopback, link-local (incl. cloud metadata 169.254.169.254),
    reserved and multicast addresses so the server-side article fetch cannot be
    pointed at internal services.
    """
    try:
        parsed = urlparse((url or "").strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


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

    if not is_safe_public_url(source):
        raise ValueError("That URL is not allowed (must be a public http/https address).")

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
