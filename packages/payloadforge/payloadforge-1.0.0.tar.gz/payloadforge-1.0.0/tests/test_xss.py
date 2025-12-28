"""
Tests for XSS Payload Generator
"""

import pytest
from payloadforge.generators.xss import XSSGenerator, generate_basic, generate_dom


class TestXSSGenerator:
    """Test cases for XSSGenerator."""
    
    def test_generate_basic_returns_list(self):
        """Test that generate_basic returns a list."""
        result = XSSGenerator.generate_basic()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_basic_with_count(self):
        """Test that count parameter limits results."""
        result = XSSGenerator.generate_basic(count=3)
        assert len(result) == 3
    
    def test_generate_basic_payloads_are_strings(self):
        """Test that all payloads are strings."""
        result = XSSGenerator.generate_basic()
        for payload in result:
            assert isinstance(payload, str)
    
    def test_generate_basic_contains_script_tag(self):
        """Test that basic payloads contain script elements."""
        result = XSSGenerator.generate_basic()
        has_script = any("<script>" in p.lower() for p in result)
        assert has_script
    
    def test_generate_dom_returns_list(self):
        """Test that generate_dom returns a list."""
        result = XSSGenerator.generate_dom()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_event_handlers_returns_list(self):
        """Test that generate_event_handlers returns a list."""
        result = XSSGenerator.generate_event_handlers()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_event_handlers_contains_events(self):
        """Test that event handler payloads contain event attributes."""
        result = XSSGenerator.generate_event_handlers()
        event_keywords = ["onerror", "onload", "onclick", "onfocus", "onmouseover"]
        has_event = any(
            any(event in p.lower() for event in event_keywords)
            for p in result
        )
        assert has_event
    
    def test_generate_polyglot_returns_list(self):
        """Test that generate_polyglot returns a list."""
        result = XSSGenerator.generate_polyglot()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_generate_all_returns_dict(self):
        """Test that generate_all returns a dictionary with all categories."""
        result = XSSGenerator.generate_all()
        assert isinstance(result, dict)
        assert "basic" in result
        assert "dom" in result
        assert "event_handlers" in result
        assert "polyglot" in result
    
    def test_with_encoding_url(self):
        """Test URL encoding of payloads."""
        original = ["<script>alert('XSS')</script>"]
        result = XSSGenerator.with_encoding(original, "url")
        assert result[0] != original[0]
        assert "%3C" in result[0]  # < encoded
    
    def test_with_encoding_html(self):
        """Test HTML encoding of payloads."""
        original = ["<script>alert('XSS')</script>"]
        result = XSSGenerator.with_encoding(original, "html")
        assert result[0] != original[0]
        assert "&lt;" in result[0]  # < encoded
    
    def test_convenience_functions(self):
        """Test convenience function exports."""
        assert generate_basic() == XSSGenerator.generate_basic()
        assert generate_dom() == XSSGenerator.generate_dom()


class TestXSSPayloadQuality:
    """Test the quality and variety of XSS payloads."""
    
    def test_basic_payloads_minimum_count(self):
        """Test that we have at least 5 basic payloads."""
        result = XSSGenerator.generate_basic()
        assert len(result) >= 5
    
    def test_dom_payloads_minimum_count(self):
        """Test that we have at least 5 DOM payloads."""
        result = XSSGenerator.generate_dom()
        assert len(result) >= 5
    
    def test_event_handler_variety(self):
        """Test that we have variety in event handlers."""
        result = XSSGenerator.generate_event_handlers()
        # Should have at least 3 different event types
        events_found = set()
        for payload in result:
            lower = payload.lower()
            for event in ["onerror", "onload", "onclick", "onfocus", "onmouseover", "ontoggle"]:
                if event in lower:
                    events_found.add(event)
        assert len(events_found) >= 3
    
    def test_payloads_are_unique(self):
        """Test that payloads are unique within each category."""
        for category_payloads in XSSGenerator.generate_all().values():
            assert len(category_payloads) == len(set(category_payloads))
