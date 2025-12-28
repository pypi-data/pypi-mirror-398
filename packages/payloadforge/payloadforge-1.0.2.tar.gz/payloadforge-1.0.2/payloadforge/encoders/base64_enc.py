"""
PayloadForge Base64 Encoder

⚠️  ETHICAL USE ONLY ⚠️

Base64 encoding utilities for payload transformation.
For authorized security testing and educational purposes only.
"""

import base64
from typing import Optional
from payloadforge.logger import logger


def encode(text: str, encoding: str = "utf-8") -> str:
    """
    Base64 encode a string.
    
    Args:
        text: Text to encode.
        encoding: Character encoding to use.
        
    Returns:
        Base64 encoded string.
    """
    logger.log_encode("base64", len(text))
    return base64.b64encode(text.encode(encoding)).decode("ascii")


def decode(text: str, encoding: str = "utf-8") -> str:
    """
    Base64 decode a string.
    
    Args:
        text: Base64 encoded text to decode.
        encoding: Character encoding of the decoded bytes.
        
    Returns:
        Decoded string.
    """
    return base64.b64decode(text).decode(encoding)


def encode_urlsafe(text: str) -> str:
    """
    URL-safe Base64 encode (uses - and _ instead of + and /).
    
    Args:
        text: Text to encode.
        
    Returns:
        URL-safe Base64 encoded string.
    """
    return base64.urlsafe_b64encode(text.encode()).decode("ascii")


def decode_urlsafe(text: str) -> str:
    """
    URL-safe Base64 decode.
    
    Args:
        text: URL-safe Base64 encoded text.
        
    Returns:
        Decoded string.
    """
    return base64.urlsafe_b64decode(text).decode()


def encode_command_linux(command: str) -> str:
    """
    Create a Base64-encoded command for Linux execution.
    
    Returns a command string like: echo 'base64' | base64 -d | bash
    
    Args:
        command: Shell command to encode.
        
    Returns:
        Full encoded command string.
    """
    encoded = encode(command)
    return f"echo '{encoded}' | base64 -d | bash"


def encode_command_windows(command: str) -> str:
    """
    Create a Base64-encoded command for Windows PowerShell execution.
    
    Returns a command string like: powershell -enc base64
    
    Args:
        command: PowerShell command to encode.
        
    Returns:
        Full encoded command string.
    """
    # PowerShell -EncodedCommand requires UTF-16LE Base64
    encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
    return f"powershell -enc {encoded}"


def encode_no_padding(text: str) -> str:
    """
    Base64 encode without padding (removes trailing =).
    
    Args:
        text: Text to encode.
        
    Returns:
        Base64 encoded string without padding.
    """
    return encode(text).rstrip("=")


def decode_no_padding(text: str) -> str:
    """
    Base64 decode text without padding.
    
    Args:
        text: Base64 text without padding.
        
    Returns:
        Decoded string.
    """
    # Add padding back
    padding = 4 - len(text) % 4
    if padding != 4:
        text += "=" * padding
    return decode(text)


def encode_base32(text: str) -> str:
    """
    Base32 encode a string.
    
    Args:
        text: Text to encode.
        
    Returns:
        Base32 encoded string.
    """
    return base64.b32encode(text.encode()).decode("ascii")


def decode_base32(text: str) -> str:
    """
    Base32 decode a string.
    
    Args:
        text: Base32 encoded text.
        
    Returns:
        Decoded string.
    """
    return base64.b32decode(text).decode()


def encode_base16(text: str) -> str:
    """
    Base16 (hex) encode a string.
    
    Args:
        text: Text to encode.
        
    Returns:
        Base16 encoded string.
    """
    return base64.b16encode(text.encode()).decode("ascii")


def decode_base16(text: str) -> str:
    """
    Base16 (hex) decode a string.
    
    Args:
        text: Base16 encoded text.
        
    Returns:
        Decoded string.
    """
    return base64.b16decode(text).decode()
