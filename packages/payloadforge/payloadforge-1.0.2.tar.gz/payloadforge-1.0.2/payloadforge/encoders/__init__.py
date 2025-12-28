"""
PayloadForge Encoders Package

⚠️  ETHICAL USE ONLY ⚠️

This package contains encoding utilities for payload transformation.
All encoders are for educational and authorized testing purposes only.
"""

from payloadforge.encoders.url import encode as url_encode, decode as url_decode
from payloadforge.encoders.html import encode as html_encode, decode as html_decode
from payloadforge.encoders.unicode import encode_escape as unicode_encode
from payloadforge.encoders.base64_enc import encode as base64_encode, decode as base64_decode

__all__ = [
    "url_encode",
    "url_decode",
    "html_encode",
    "html_decode",
    "unicode_encode",
    "base64_encode",
    "base64_decode",
]
