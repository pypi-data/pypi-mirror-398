import pytest
from sociallinks.core import SocialLinks
from sociallinks.exceptions import (
    PlatformNotFoundError,
    URLMismatchError,
)


class TestSocialLinksInitialization:
    """Test SocialLinks initialization"""

    def test_init_with_predefined_platforms(self):
        """Test initialization with predefined platforms"""
        sl = SocialLinks()
        assert len(sl.platforms) >= 25  # Should have all 25 predefined platforms
        # Verify some key platforms exist
        assert "linkedin" in sl.platforms
        assert "facebook" in sl.platforms
        assert "github" in sl.platforms
        assert "instagram" in sl.platforms
        assert "youtube" in sl.platforms
        assert "x" in sl.platforms

    def test_init_without_predefined_platforms(self):
        """Test initialization without predefined platforms"""
        sl = SocialLinks(use_predefined_platforms=False)
        assert len(sl.platforms) == 0
        assert len(sl._compiled) == 0

    def test_init_with_custom_regex_flags(self):
        """Test initialization with custom regex flags"""
        import re
        sl = SocialLinks(regex_flags=re.IGNORECASE | re.MULTILINE)
        assert sl.regex_flags == (re.IGNORECASE | re.MULTILINE)


class TestDetectPlatform:
    """Test detect_platform method"""

    def test_detect_linkedin_personal(self):
        """Test detecting LinkedIn personal platform"""
        sl = SocialLinks()
        assert sl.detect_platform("https://www.linkedin.com/in/johndoe/") == "linkedin"
        assert sl.detect_platform("http://linkedin.com/in/johndoe") == "linkedin"
        assert sl.detect_platform("https://linkedin.com/in/jane-smith") == "linkedin"

    def test_detect_linkedin_company(self):
        """Test detecting LinkedIn company platform"""
        sl = SocialLinks()
        assert sl.detect_platform("https://www.linkedin.com/company/acme/") == "linkedin"
        assert sl.detect_platform("http://linkedin.com/company/techcorp") == "linkedin"

    def test_detect_facebook(self):
        """Test detecting Facebook platform"""
        sl = SocialLinks()
        assert sl.detect_platform("https://www.facebook.com/johndoe/") == "facebook"
        assert sl.detect_platform("http://facebook.com/janedoe") == "facebook"

    def test_detect_none_for_invalid_url(self):
        """Test that invalid URLs return None"""
        sl = SocialLinks()
        assert sl.detect_platform("https://example.com") is None
        assert sl.detect_platform("not a url") is None
        assert sl.detect_platform("") is None

    def test_detect_with_whitespace(self):
        """Test that URLs with whitespace are handled"""
        sl = SocialLinks()
        assert sl.detect_platform("  https://www.linkedin.com/in/johndoe/  ") == "linkedin"


class TestIsValid:
    """Test is_valid method"""

    def test_is_valid_linkedin_personal(self):
        """Test validating LinkedIn personal URLs"""
        sl = SocialLinks()
        assert sl.is_valid("linkedin", "https://www.linkedin.com/in/johndoe/") is True
        assert sl.is_valid("linkedin", "http://linkedin.com/in/jane-smith") is True
        assert sl.is_valid("linkedin", "https://example.com") is False

    def test_is_valid_linkedin_company(self):
        """Test validating LinkedIn company URLs"""
        sl = SocialLinks()
        assert sl.is_valid("linkedin", "https://www.linkedin.com/company/acme/") is True
        assert sl.is_valid("linkedin", "http://linkedin.com/company/techcorp") is True

    def test_is_valid_facebook(self):
        """Test validating Facebook URLs"""
        sl = SocialLinks()
        assert sl.is_valid("facebook", "https://www.facebook.com/johndoe/") is True
        assert sl.is_valid("facebook", "http://facebook.com/janedoe") is True
        assert sl.is_valid("facebook", "https://example.com") is False

    def test_is_valid_unknown_platform(self):
        """Test validating with unknown platform"""
        sl = SocialLinks()
        assert sl.is_valid("unknown", "https://www.linkedin.com/in/johndoe/") is False

    def test_is_valid_with_whitespace(self):
        """Test that URLs with whitespace are handled"""
        sl = SocialLinks()
        assert sl.is_valid("linkedin", "  https://www.linkedin.com/in/johndoe/  ") is True


class TestSanitize:
    """Test sanitize method"""

    def test_sanitize_unknown_platform(self):
        """Test sanitizing with unknown platform"""
        sl = SocialLinks()
        with pytest.raises(PlatformNotFoundError, match="Unknown platform"):
            sl.sanitize("unknown", "https://www.linkedin.com/in/johndoe/")

    def test_sanitize_invalid_url(self):
        """Test sanitizing invalid URL for platform"""
        sl = SocialLinks()
        with pytest.raises(URLMismatchError, match="does not match platform"):
            sl.sanitize("linkedin", "https://example.com")

    def test_sanitize_with_whitespace(self):
        """Test sanitizing URLs with whitespace"""
        sl = SocialLinks()
        result = sl.sanitize("linkedin", "  https://www.linkedin.com/in/johndoe/  ")
        assert result == "https://linkedin.com/in/johndoe"
