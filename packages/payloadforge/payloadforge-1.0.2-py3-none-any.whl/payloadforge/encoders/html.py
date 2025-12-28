"""
PayloadForge HTML Entity Encoder

⚠️  ETHICAL USE ONLY ⚠️

HTML entity encoding utilities for payload transformation.
For authorized security testing and educational purposes only.
"""

import html
from typing import Optional
from payloadforge.logger import logger


# Common HTML entity mappings
HTML_ENTITIES = {
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
    "`": "&#x60;",
    "=": "&#x3D;",
}


def encode(text: str, quote: bool = True) -> str:
    """
    HTML entity encode a string.
    
    Args:
        text: Text to encode.
        quote: If True, also encode quotes.
        
    Returns:
        HTML entity encoded string.
    """
    logger.log_encode("html", len(text))
    return html.escape(text, quote=quote)


def decode(text: str) -> str:
    """
    HTML entity decode a string.
    
    Args:
        text: HTML encoded text to decode.
        
    Returns:
        Decoded string.
    """
    return html.unescape(text)


def encode_decimal(text: str) -> str:
    """
    Encode all characters as decimal HTML entities.
    
    Args:
        text: Text to encode.
        
    Returns:
        Decimal HTML entity encoded string.
    """
    return "".join(f"&#{ord(c)};" for c in text)


def encode_hex(text: str) -> str:
    """
    Encode all characters as hexadecimal HTML entities.
    
    Args:
        text: Text to encode.
        
    Returns:
        Hexadecimal HTML entity encoded string.
    """
    return "".join(f"&#x{ord(c):x};" for c in text)


def encode_named(text: str) -> str:
    """
    Encode using named HTML entities where available.
    
    Args:
        text: Text to encode.
        
    Returns:
        Named HTML entity encoded string.
    """
    result = []
    for char in text:
        if char in HTML_ENTITIES:
            result.append(HTML_ENTITIES[char])
        else:
            result.append(char)
    return "".join(result)


def encode_mixed(text: str) -> str:
    """
    Encode with a mix of decimal and hex entities (bypasses some filters).
    
    Args:
        text: Text to encode.
        
    Returns:
        Mixed HTML entity encoded string.
    """
    result = []
    for i, char in enumerate(text):
        if char.isalnum():
            result.append(char)
        elif i % 2 == 0:
            result.append(f"&#{ord(char)};")  # Decimal
        else:
            result.append(f"&#x{ord(char):x};")  # Hex
    return "".join(result)


def encode_long_hex(text: str) -> str:
    """
    Encode using padded hexadecimal entities (bypasses some regex filters).
    
    Args:
        text: Text to encode.
        
    Returns:
        Long hex HTML entity encoded string.
    """
    return "".join(f"&#x{ord(c):06x};" for c in text)


def encode_without_semicolon(text: str) -> str:
    """
    Encode without trailing semicolons (works in some contexts).
    
    Args:
        text: Text to encode.
        
    Returns:
        HTML entity encoded string without semicolons.
    """
    result = []
    for char in text:
        if char.isalnum() or char == " ":
            result.append(char)
        else:
            # Use decimal without semicolon, followed by space if next is digit
            result.append(f"&#{ord(char)}")
    return "".join(result)
