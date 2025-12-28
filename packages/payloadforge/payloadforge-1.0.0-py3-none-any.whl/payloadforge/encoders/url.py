"""
PayloadForge URL Encoder

⚠️  ETHICAL USE ONLY ⚠️

URL encoding utilities for payload transformation.
For authorized security testing and educational purposes only.
"""

import urllib.parse
from typing import Optional
from payloadforge.logger import logger


def encode(text: str, safe: str = "", plus: bool = False) -> str:
    """
    URL encode a string.
    
    Args:
        text: Text to encode.
        safe: Characters to not encode.
        plus: If True, use + for spaces instead of %20.
        
    Returns:
        URL encoded string.
    """
    logger.log_encode("url", len(text))
    
    if plus:
        return urllib.parse.quote_plus(text, safe=safe)
    return urllib.parse.quote(text, safe=safe)


def decode(text: str, plus: bool = False) -> str:
    """
    URL decode a string.
    
    Args:
        text: URL encoded text to decode.
        plus: If True, decode + as space.
        
    Returns:
        Decoded string.
    """
    if plus:
        return urllib.parse.unquote_plus(text)
    return urllib.parse.unquote(text)


def double_encode(text: str) -> str:
    """
    Double URL encode a string.
    
    Useful for bypassing certain WAF filters.
    
    Args:
        text: Text to double encode.
        
    Returns:
        Double URL encoded string.
    """
    return encode(encode(text))


def encode_special_chars(text: str) -> str:
    """
    Encode only special/dangerous characters, leaving alphanumeric intact.
    
    Args:
        text: Text to encode.
        
    Returns:
        Partially URL encoded string.
    """
    # Keep alphanumeric and common safe chars
    return encode(text, safe="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


def encode_unicode(text: str) -> str:
    """
    URL encode using Unicode escape sequences.
    
    Args:
        text: Text to encode.
        
    Returns:
        Unicode URL encoded string.
    """
    result = []
    for char in text:
        code_point = ord(char)
        if code_point > 127:
            # Encode high code points as %uXXXX
            result.append(f"%u{code_point:04X}")
        elif char.isalnum():
            result.append(char)
        else:
            result.append(f"%{code_point:02X}")
    return "".join(result)


def mixed_case_encode(text: str) -> str:
    """
    URL encode with mixed case hex digits (bypasses some filters).
    
    Args:
        text: Text to encode.
        
    Returns:
        Mixed case URL encoded string.
    """
    result = []
    toggle = True
    for char in text:
        if char.isalnum():
            result.append(char)
        else:
            code_point = ord(char)
            if toggle:
                result.append(f"%{code_point:02X}")  # Uppercase
            else:
                result.append(f"%{code_point:02x}")  # Lowercase
            toggle = not toggle
    return "".join(result)
