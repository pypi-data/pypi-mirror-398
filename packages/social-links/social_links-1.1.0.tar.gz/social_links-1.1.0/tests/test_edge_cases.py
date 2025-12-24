import pytest
import re
from sociallinks.core import SocialLinks
from sociallinks.exceptions import (
    PlatformIDExtractionError,
)


class TestExtractId:
    """Test _extract_id static method"""

    def test_extract_id_with_named_group(self):
        """Test extracting ID from named group"""
        pattern = re.compile(r"https?://example\.com/(?P<id>[A-Za-z0-9_]+)/?$")
        match = pattern.search("https://example.com/johndoe")
        assert match is not None
        assert SocialLinks._extract_id(match) == "johndoe"

    def test_extract_id_with_unnamed_group(self):
        """Test extracting ID from unnamed group"""
        pattern = re.compile(r"https?://example\.com/([A-Za-z0-9_]+)/?$")
        match = pattern.search("https://example.com/johndoe")
        assert match is not None
        assert SocialLinks._extract_id(match) == "johndoe"

    def test_extract_id_no_match(self):
        """Test extracting ID when no groups match"""
        pattern = re.compile(r"https?://example\.com/")
        match = pattern.search("https://example.com/")
        assert match is not None
        assert SocialLinks._extract_id(match) is None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_sanitize_no_id_extracted(self):
        """Test sanitize when ID cannot be extracted"""
        sl = SocialLinks(use_predefined_platforms=False)
        # Create a platform with pattern that doesn't capture ID
        platform_data = {
            "patterns": ["https?://example\\.com/static/?$"],
            "sanitized": "https://example.com/{id}/"
        }
        sl.set_platform("example", platform_data)
        with pytest.raises(PlatformIDExtractionError, match="Could not extract platform ID"):
            sl.sanitize("example", "https://example.com/static")

    def test_case_insensitive_matching(self):
        """Test case insensitive URL matching"""
        sl = SocialLinks()
        # Should work with uppercase
        assert sl.detect_platform("HTTPS://WWW.LINKEDIN.COM/IN/JOHNDOE/") == "linkedin"
        assert sl.is_valid("linkedin", "HTTPS://WWW.LINKEDIN.COM/IN/JOHNDOE/") is True

    def test_multiple_patterns_same_platform(self):
        """Test platform with multiple patterns"""
        sl = SocialLinks()
        # LinkedIn has both personal and company patterns
        assert sl.is_valid("linkedin", "https://www.linkedin.com/in/johndoe/") is True
        assert sl.is_valid("linkedin", "https://www.linkedin.com/company/acme/") is True

