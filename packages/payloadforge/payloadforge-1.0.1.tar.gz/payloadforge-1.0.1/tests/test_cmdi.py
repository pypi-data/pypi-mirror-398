"""
Tests for Command Injection Payload Generator
"""

import pytest
from payloadforge.generators.cmdi import CMDiGenerator, generate_linux, generate_windows


class TestCMDiGenerator:
    """Test cases for CMDiGenerator."""
    
    def test_generate_linux(self):
        """Test Linux payload generation."""
        result = CMDiGenerator.generate_linux()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_linux_with_count(self):
        """Test count parameter."""
        result = CMDiGenerator.generate_linux(count=5)
        assert len(result) == 5
    
    def test_generate_linux_contains_commands(self):
        """Test that Linux payloads contain command syntax."""
        result = CMDiGenerator.generate_linux()
        command_indicators = [";", "|", "&&", "||", "`", "$(", "&", "\n", "\r"]
        # Most payloads should contain at least one command indicator
        count_with_cmd = sum(
            1 for p in result
            if any(ind in p for ind in command_indicators)
        )
        # At least 80% should have command indicators
        assert count_with_cmd >= len(result) * 0.8
    
    def test_generate_linux_no_spaces(self):
        """Test Linux payloads with space bypass."""
        result = CMDiGenerator.generate_linux_no_spaces()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_windows(self):
        """Test Windows payload generation."""
        result = CMDiGenerator.generate_windows()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_windows_contains_commands(self):
        """Test that Windows payloads contain command syntax."""
        result = CMDiGenerator.generate_windows()
        command_indicators = ["&", "|"]
        has_cmd = all(
            any(ind in p for ind in command_indicators)
            for p in result
        )
        assert has_cmd
    
    def test_generate_blind_linux(self):
        """Test Linux blind injection payloads."""
        result = CMDiGenerator.generate_blind("linux")
        assert isinstance(result, list)
        assert any("sleep" in p.lower() for p in result)
    
    def test_generate_blind_windows(self):
        """Test Windows blind injection payloads."""
        result = CMDiGenerator.generate_blind("windows")
        assert isinstance(result, list)
        assert any("ping" in p.lower() or "timeout" in p.lower() for p in result)
    
    def test_generate_oob_linux(self):
        """Test Linux OOB payloads."""
        result = CMDiGenerator.generate_oob("linux", "test.com")
        assert isinstance(result, list)
        assert any("test.com" in p for p in result)
    
    def test_generate_oob_windows(self):
        """Test Windows OOB payloads."""
        result = CMDiGenerator.generate_oob("windows", "test.com")
        assert isinstance(result, list)
        assert any("test.com" in p for p in result)
    
    def test_generate_all_linux(self):
        """Test generate_all for Linux."""
        result = CMDiGenerator.generate_all("linux")
        assert isinstance(result, dict)
        assert "basic" in result
        assert "blind" in result
        assert "oob" in result
    
    def test_generate_all_windows(self):
        """Test generate_all for Windows."""
        result = CMDiGenerator.generate_all("windows")
        assert isinstance(result, dict)
        assert "basic" in result
        assert "blind" in result
    
    def test_with_encoding_url(self):
        """Test URL encoding."""
        payloads = ["; id"]
        result = CMDiGenerator.with_encoding(payloads, "url")
        assert result[0] != payloads[0]
        assert "%3B" in result[0]  # ; encoded
    
    def test_with_encoding_base64(self):
        """Test Base64 encoding."""
        payloads = ["; id"]
        result = CMDiGenerator.with_encoding(payloads, "base64")
        assert result[0] != payloads[0]
    
    def test_convenience_functions(self):
        """Test convenience function exports."""
        assert generate_linux() == CMDiGenerator.generate_linux()
        assert generate_windows() == CMDiGenerator.generate_windows()


class TestCMDiPayloadQuality:
    """Test the quality of CMDi payloads."""
    
    def test_linux_payloads_minimum_count(self):
        """Test minimum payload count."""
        assert len(CMDiGenerator.generate_linux()) >= 10
    
    def test_windows_payloads_minimum_count(self):
        """Test minimum payload count."""
        assert len(CMDiGenerator.generate_windows()) >= 10
    
    def test_linux_windows_different(self):
        """Test that Linux and Windows payloads are different."""
        linux = set(CMDiGenerator.generate_linux())
        windows = set(CMDiGenerator.generate_windows())
        # Should be completely different (or almost)
        assert len(linux & windows) < len(linux) / 2
