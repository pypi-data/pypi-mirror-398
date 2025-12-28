"""
Tests for SSTI Payload Generator
"""

import pytest
from payloadforge.generators.ssti import SSTIGenerator, generate_jinja2, generate_twig


class TestSSTIGenerator:
    """Test cases for SSTIGenerator."""
    
    def test_generate_jinja2(self):
        """Test Jinja2 payload generation."""
        result = SSTIGenerator.generate_jinja2()
        assert isinstance(result, list)
        assert len(result) > 0
        # Should contain Jinja2 syntax
        assert any("{{" in p for p in result)
    
    def test_generate_jinja2_safe_only(self):
        """Test Jinja2 safe detection payloads."""
        result = SSTIGenerator.generate_jinja2(safe_only=True)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_jinja2_with_count(self):
        """Test count parameter."""
        result = SSTIGenerator.generate_jinja2(count=3)
        assert len(result) == 3
    
    def test_generate_twig(self):
        """Test Twig payload generation."""
        result = SSTIGenerator.generate_twig()
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("{{" in p for p in result)
    
    def test_generate_smarty(self):
        """Test Smarty payload generation."""
        result = SSTIGenerator.generate_smarty()
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("{" in p for p in result)
    
    def test_generate_velocity(self):
        """Test Velocity payload generation."""
        result = SSTIGenerator.generate_velocity()
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("#" in p or "$" in p for p in result)
    
    def test_generate_freemarker(self):
        """Test Freemarker payload generation."""
        result = SSTIGenerator.generate_freemarker()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_erb(self):
        """Test ERB payload generation."""
        result = SSTIGenerator.generate_erb()
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("<%" in p for p in result)
    
    def test_generate_detection(self):
        """Test detection payload generation."""
        result = SSTIGenerator.generate_detection()
        assert isinstance(result, dict)
        assert "jinja2" in result
        assert "twig" in result
        assert "smarty" in result
        assert "velocity" in result
    
    def test_generate_all(self):
        """Test generate_all returns all engines."""
        result = SSTIGenerator.generate_all()
        assert isinstance(result, dict)
        assert len(result) >= 4
    
    def test_convenience_functions(self):
        """Test convenience function exports."""
        assert generate_jinja2() == SSTIGenerator.generate_jinja2()
        assert generate_twig() == SSTIGenerator.generate_twig()


class TestSSTIPayloadQuality:
    """Test the quality of SSTI payloads."""
    
    def test_jinja2_contains_magic_number(self):
        """Test that Jinja2 has the 7*7 detection payload."""
        result = SSTIGenerator.generate_jinja2()
        assert any("7*7" in p for p in result)
    
    def test_each_engine_has_minimum_payloads(self):
        """Test minimum payload count per engine."""
        assert len(SSTIGenerator.generate_jinja2()) >= 5
        assert len(SSTIGenerator.generate_twig()) >= 5
        assert len(SSTIGenerator.generate_smarty()) >= 5
        assert len(SSTIGenerator.generate_velocity()) >= 4
    
    def test_detection_payloads_are_safer(self):
        """Test that detection payloads are subset or simpler."""
        full = SSTIGenerator.generate_jinja2()
        safe = SSTIGenerator.generate_jinja2(safe_only=True)
        assert len(safe) <= len(full)
