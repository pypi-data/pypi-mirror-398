import pytest
from sociallinks.core import SocialLinks
from sociallinks.exceptions import (
    PlatformNotFoundError,
    PlatformAlreadyExistsError,
    InvalidPlatformError,
)


class TestSetPlatform:
    """Test set_platform method"""

    def test_set_platform_new(self):
        """Test adding a new platform"""
        sl = SocialLinks(use_predefined_platforms=False)
        platform_data = {
            "patterns": ["https?://(www\\.)?twitter\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
            "sanitized": "https://www.twitter.com/{id}/"
        }
        sl.set_platform("twitter", platform_data)
        assert "twitter" in sl.platforms
        assert sl.detect_platform("https://www.twitter.com/johndoe") == "twitter"

    def test_set_platform_override_false(self):
        """Test that setting existing platform without override raises error"""
        sl = SocialLinks()
        platform_data = {
            "patterns": ["https?://(www\\.)?twitter\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
            "sanitized": "https://www.twitter.com/{id}/"
        }
        with pytest.raises(PlatformAlreadyExistsError, match="already exists"):
            sl.set_platform("linkedin", platform_data)

    def test_set_platform_override_true(self):
        """Test overriding existing platform"""
        sl = SocialLinks()
        platform_data = {
            "patterns": ["https?://(www\\.)?linkedin\\.com/custom/(?P<id>[A-Za-z0-9_]+)/?$"],
            "sanitized": "https://www.linkedin.com/custom/{id}/"
        }
        sl.set_platform("linkedin", platform_data, override=True)
        assert sl.detect_platform("https://www.linkedin.com/custom/johndoe") == "linkedin"
        assert sl.detect_platform("https://www.linkedin.com/in/johndoe") is None

    def test_set_platform_with_list(self):
        """Test setting platform with list of patterns"""
        sl = SocialLinks(use_predefined_platforms=False)
        platform_data = [
            {
                "patterns": ["https?://(www\\.)?twitter\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
                "sanitized": "https://www.twitter.com/{id}/"
            },
            {
                "patterns": ["https?://twitter\\.com/x/(?P<id>[A-Za-z0-9_]+)/?$"],
                "sanitized": "https://www.twitter.com/x/{id}/"
            }
        ]
        sl.set_platform("twitter", platform_data)
        assert sl.detect_platform("https://www.twitter.com/johndoe") == "twitter"
        assert sl.detect_platform("https://twitter.com/x/johndoe") == "twitter"

    def test_set_platform_invalid_patterns(self):
        """Test setting platform with invalid patterns"""
        sl = SocialLinks(use_predefined_platforms=False)
        platform_data = {
            "patterns": [],
            "sanitized": "https://www.example.com/{id}/"
        }
        with pytest.raises(InvalidPlatformError, match="no valid patterns"):
            sl.set_platform("example", platform_data)

    def test_set_platform_missing_sanitized(self):
        """Test setting platform without sanitized template"""
        sl = SocialLinks(use_predefined_platforms=False)
        platform_data = {
            "patterns": ["https?://example\\.com/(?P<id>[A-Za-z0-9_]+)/?$"]
        }
        with pytest.raises(InvalidPlatformError, match="no valid patterns"):
            sl.set_platform("example", platform_data)


class TestDeletePlatform:
    """Test delete_platform method"""

    def test_delete_platform(self):
        """Test deleting a platform"""
        sl = SocialLinks()
        assert "linkedin" in sl.platforms
        sl.delete_platform("linkedin")
        assert "linkedin" not in sl.platforms
        assert "linkedin" not in sl._compiled

    def test_delete_platform_not_found(self):
        """Test deleting non-existent platform"""
        sl = SocialLinks()
        with pytest.raises(PlatformNotFoundError, match="not found"):
            sl.delete_platform("nonexistent")


class TestSetPlatforms:
    """Test set_platforms method"""

    def test_set_platforms_new(self):
        """Test bulk adding new platforms"""
        sl = SocialLinks(use_predefined_platforms=False)
        platforms = {
            "twitter": {
                "patterns": ["https?://(www\\.)?twitter\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
                "sanitized": "https://www.twitter.com/{id}/"
            },
            "instagram": {
                "patterns": ["https?://(www\\.)?instagram\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
                "sanitized": "https://www.instagram.com/{id}/"
            }
        }
        sl.set_platforms(platforms)
        assert "twitter" in sl.platforms
        assert "instagram" in sl.platforms

    def test_set_platforms_with_conflicts(self):
        """Test bulk adding platforms with conflicts"""
        sl = SocialLinks()
        platforms = {
            "linkedin": {
                "patterns": ["https?://example\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
                "sanitized": "https://example.com/{id}/"
            }
        }
        with pytest.raises(PlatformAlreadyExistsError, match="already exist"):
            sl.set_platforms(platforms)

    def test_set_platforms_override(self):
        """Test bulk adding platforms with override"""
        sl = SocialLinks()
        platforms = {
            "linkedin": {
                "patterns": ["https?://example\\.com/(?P<id>[A-Za-z0-9_]+)/?$"],
                "sanitized": "https://example.com/{id}/"
            }
        }
        sl.set_platforms(platforms, override=True)
        assert sl.detect_platform("https://example.com/johndoe") == "linkedin"


class TestDeletePlatforms:
    """Test delete_platforms method"""

    def test_delete_platforms(self):
        """Test bulk deleting platforms"""
        sl = SocialLinks()
        assert "linkedin" in sl.platforms
        assert "facebook" in sl.platforms
        sl.delete_platforms(["linkedin", "facebook"])
        assert "linkedin" not in sl.platforms
        assert "facebook" not in sl.platforms

    def test_delete_platforms_missing(self):
        """Test bulk deleting with missing platforms"""
        sl = SocialLinks()
        with pytest.raises(PlatformNotFoundError, match="not found"):
            sl.delete_platforms(["linkedin", "nonexistent"])


class TestClearPlatforms:
    """Test clear_platforms method"""

    def test_clear_platforms(self):
        """Test clearing all platforms"""
        sl = SocialLinks()
        assert len(sl.platforms) > 0
        sl.clear_platforms()
        assert len(sl.platforms) == 0
        assert len(sl._compiled) == 0


class TestGetPlatform:
    """Test get_platform method"""

    def test_get_platform(self):
        """Test getting a platform"""
        sl = SocialLinks()
        platform = sl.get_platform("linkedin")
        assert platform is not None
        assert isinstance(platform, list)

    def test_get_platform_not_found(self):
        """Test getting non-existent platform"""
        sl = SocialLinks()
        with pytest.raises(PlatformNotFoundError, match="not found"):
            sl.get_platform("nonexistent")


class TestListPlatforms:
    """Test list_platforms method"""

    def test_list_platforms(self):
        """Test listing all platforms"""
        sl = SocialLinks()
        platforms = sl.list_platforms()
        assert isinstance(platforms, list)
        # Should have all 25 predefined platforms
        assert len(platforms) >= 25
        # Verify some key platforms exist
        assert "linkedin" in platforms
        assert "facebook" in platforms
        assert "github" in platforms
        assert "instagram" in platforms
        assert "youtube" in platforms
        assert "x" in platforms
        assert "behance" in platforms
        assert "dev_to" in platforms

    def test_list_platforms_empty(self):
        """Test listing platforms when empty"""
        sl = SocialLinks(use_predefined_platforms=False)
        platforms = sl.list_platforms()
        assert platforms == []

