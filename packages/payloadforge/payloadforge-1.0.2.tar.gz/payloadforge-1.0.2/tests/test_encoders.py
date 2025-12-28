"""
Tests for Encoding Utilities
"""

import pytest
from payloadforge.encoders import url, html, unicode, base64_enc


class TestURLEncoder:
    """Test cases for URL encoder."""
    
    def test_encode_basic(self):
        """Test basic URL encoding."""
        result = url.encode("<script>")
        assert result == "%3Cscript%3E"
    
    def test_encode_with_safe(self):
        """Test encoding with safe characters."""
        result = url.encode("<script>", safe="<>")
        assert "<" in result
        assert ">" in result
    
    def test_encode_with_plus(self):
        """Test space encoding as +."""
        result = url.encode("hello world", plus=True)
        assert "+" in result
    
    def test_decode_basic(self):
        """Test basic URL decoding."""
        result = url.decode("%3Cscript%3E")
        assert result == "<script>"
    
    def test_double_encode(self):
        """Test double URL encoding."""
        result = url.double_encode("<")
        assert "%253C" in result
    
    def test_encode_decode_roundtrip(self):
        """Test that encode/decode roundtrips correctly."""
        original = "<script>alert('test')</script>"
        encoded = url.encode(original)
        decoded = url.decode(encoded)
        assert decoded == original


class TestHTMLEncoder:
    """Test cases for HTML encoder."""
    
    def test_encode_basic(self):
        """Test basic HTML encoding."""
        result = html.encode("<script>")
        assert "&lt;" in result
        assert "&gt;" in result
    
    def test_decode_basic(self):
        """Test basic HTML decoding."""
        result = html.decode("&lt;script&gt;")
        assert result == "<script>"
    
    def test_encode_decimal(self):
        """Test decimal entity encoding."""
        result = html.encode_decimal("<")
        assert "&#60;" in result
    
    def test_encode_hex(self):
        """Test hex entity encoding."""
        result = html.encode_hex("<")
        assert "&#x3c;" in result
    
    def test_encode_named(self):
        """Test named entity encoding."""
        result = html.encode_named("<>&")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
    
    def test_encode_decode_roundtrip(self):
        """Test that encode/decode roundtrips correctly."""
        original = "<script>alert('test')</script>"
        encoded = html.encode(original)
        decoded = html.decode(encoded)
        assert decoded == original


class TestUnicodeEncoder:
    """Test cases for Unicode encoder."""
    
    def test_encode_escape(self):
        """Test Unicode escape encoding."""
        result = unicode.encode_escape("A")
        assert result == "\\u0041"
    
    def test_encode_javascript(self):
        """Test JavaScript Unicode encoding."""
        result = unicode.encode_javascript("<script>")
        assert "\\u" in result
    
    def test_encode_fullwidth(self):
        """Test fullwidth conversion."""
        result = unicode.encode_fullwidth("abc")
        assert result != "abc"
        # Fullwidth characters are in different Unicode range
        assert ord(result[0]) > 127
    
    def test_encode_homoglyph(self):
        """Test homoglyph encoding."""
        result = unicode.encode_homoglyph("script")
        # 'c' should be replaced with Cyrillic 'с'
        assert result != "script"
    
    def test_encode_zero_width(self):
        """Test zero-width character insertion."""
        result = unicode.encode_zero_width("abc")
        assert len(result) > len("abc")
        assert "\u200b" in result


class TestBase64Encoder:
    """Test cases for Base64 encoder."""
    
    def test_encode_basic(self):
        """Test basic Base64 encoding."""
        result = base64_enc.encode("hello")
        assert result == "aGVsbG8="
    
    def test_decode_basic(self):
        """Test basic Base64 decoding."""
        result = base64_enc.decode("aGVsbG8=")
        assert result == "hello"
    
    def test_encode_urlsafe(self):
        """Test URL-safe Base64 encoding."""
        result = base64_enc.encode_urlsafe("hello?world!")
        assert "+" not in result
        assert "/" not in result
    
    def test_encode_command_linux(self):
        """Test Linux command encoding."""
        result = base64_enc.encode_command_linux("id")
        assert "base64 -d" in result
        assert "bash" in result
    
    def test_encode_command_windows(self):
        """Test Windows command encoding."""
        result = base64_enc.encode_command_windows("whoami")
        assert "powershell -enc" in result
    
    def test_encode_no_padding(self):
        """Test encoding without padding."""
        result = base64_enc.encode_no_padding("hello")
        assert not result.endswith("=")
    
    def test_encode_decode_roundtrip(self):
        """Test that encode/decode roundtrips correctly."""
        original = "Hello, World!"
        encoded = base64_enc.encode(original)
        decoded = base64_enc.decode(encoded)
        assert decoded == original
    
    def test_encode_base32(self):
        """Test Base32 encoding."""
        result = base64_enc.encode_base32("hello")
        assert result == "NBSWY3DP"
    
    def test_encode_base16(self):
        """Test Base16 (hex) encoding."""
        result = base64_enc.encode_base16("AB")
        assert result == "4142"
