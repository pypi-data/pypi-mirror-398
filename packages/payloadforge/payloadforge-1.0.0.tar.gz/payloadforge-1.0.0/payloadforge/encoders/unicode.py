"""
PayloadForge Unicode Encoder

⚠️  ETHICAL USE ONLY ⚠️

Unicode encoding utilities for payload transformation.
For authorized security testing and educational purposes only.
"""

from typing import Optional
from payloadforge.logger import logger


def encode_escape(text: str) -> str:
    """
    Encode text using Unicode escape sequences (\\uXXXX format).
    
    Args:
        text: Text to encode.
        
    Returns:
        Unicode escaped string.
    """
    logger.log_encode("unicode", len(text))
    return "".join(f"\\u{ord(c):04x}" for c in text)


def decode_escape(text: str) -> str:
    """
    Decode Unicode escape sequences.
    
    Args:
        text: Unicode escaped text to decode.
        
    Returns:
        Decoded string.
    """
    return text.encode().decode("unicode_escape")


def encode_utf8_hex(text: str) -> str:
    """
    Encode text as UTF-8 hex bytes.
    
    Args:
        text: Text to encode.
        
    Returns:
        UTF-8 hex encoded string.
    """
    return "".join(f"\\x{b:02x}" for b in text.encode("utf-8"))


def encode_utf16_le(text: str) -> str:
    """
    Encode text as UTF-16 LE bytes.
    
    Args:
        text: Text to encode.
        
    Returns:
        UTF-16 LE hex encoded string.
    """
    return "".join(f"\\x{b:02x}" for b in text.encode("utf-16-le"))


def encode_utf16_be(text: str) -> str:
    """
    Encode text as UTF-16 BE bytes.
    
    Args:
        text: Text to encode.
        
    Returns:
        UTF-16 BE hex encoded string.
    """
    return "".join(f"\\x{b:02x}" for b in text.encode("utf-16-be"))


def encode_javascript(text: str) -> str:
    """
    Encode text for JavaScript strings.
    
    Args:
        text: Text to encode.
        
    Returns:
        JavaScript Unicode escaped string.
    """
    result = []
    for char in text:
        code_point = ord(char)
        if code_point > 127 or not char.isalnum():
            result.append(f"\\u{code_point:04x}")
        else:
            result.append(char)
    return "".join(result)


def encode_css(text: str) -> str:
    """
    Encode text for CSS strings.
    
    Args:
        text: Text to encode.
        
    Returns:
        CSS Unicode escaped string.
    """
    return "".join(f"\\{ord(c):x} " for c in text)


def encode_fullwidth(text: str) -> str:
    """
    Convert ASCII to fullwidth Unicode characters.
    
    Useful for bypassing certain input validation.
    
    Args:
        text: Text to convert.
        
    Returns:
        Fullwidth Unicode string.
    """
    result = []
    for char in text:
        code_point = ord(char)
        if 0x21 <= code_point <= 0x7E:
            # Convert to fullwidth (FF01-FF5E)
            result.append(chr(code_point + 0xFEE0))
        elif char == " ":
            result.append("\u3000")  # Ideographic space
        else:
            result.append(char)
    return "".join(result)


def encode_homoglyph(text: str) -> str:
    """
    Replace characters with visually similar Unicode homoglyphs.
    
    Useful for bypassing keyword filters.
    
    Args:
        text: Text to convert.
        
    Returns:
        String with homoglyph replacements.
    """
    homoglyphs = {
        "a": "а",  # Cyrillic
        "c": "с",
        "e": "е",
        "o": "о",
        "p": "р",
        "x": "х",
        "y": "у",
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
    }
    return "".join(homoglyphs.get(c, c) for c in text)


def encode_zero_width(text: str) -> str:
    """
    Insert zero-width characters between visible characters.
    
    Useful for bypassing pattern matching.
    
    Args:
        text: Text to obfuscate.
        
    Returns:
        String with zero-width characters inserted.
    """
    zwsp = "\u200b"  # Zero-width space
    return zwsp.join(text)


def encode_combining_marks(text: str) -> str:
    """
    Add combining marks to characters.
    
    Args:
        text: Text to modify.
        
    Returns:
        String with combining marks added.
    """
    combining_mark = "\u0308"  # Combining diaeresis
    return "".join(c + combining_mark if c.isalpha() else c for c in text)
