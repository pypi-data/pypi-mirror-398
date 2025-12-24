# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0]

### Added

- MkDocs documentation setup with Material theme
- Comprehensive Contributing Guide (CONTRIBUTING.md) with development setup instructions
- GitHub Actions workflow for automated documentation deployment
- Documentation badge in README linking to hosted documentation
- Links section in README with all project resources
- Added py.typed file for type hinting

### Changed

- Updated README with clickable links for all 25+ supported platforms
- Enhanced README structure with Changelog, Contributing, and Support sections
- Improved documentation organization with dedicated docs/ directory


## [1.0.0]

### Added

- Initial release of social-links
- `SocialLinks` class for detecting and sanitizing social media URLs
- `detect_platform()` method for automatically detecting platform from URL
- `is_valid()` method for validating URLs against specific platforms
- `sanitize()` method for normalizing URLs to canonical format
- Platform management methods:
  - `set_platform()` - Add or override a single platform
  - `delete_platform()` - Remove a single platform
  - `set_platforms()` - Bulk add/override platforms
  - `delete_platforms()` - Bulk remove platforms
  - `clear_platforms()` - Remove all platforms
  - `get_platform()` - Retrieve platform configuration
  - `list_platforms()` - List all registered platforms
- Support for 25+ predefined social media platforms:
  - behance, dev_to, dribbble, exercism, facebook, github, instagram, keybase, lemmy_world, linkedin, linktree, mastodon, medium, patreon, pinterest, soundcloud, spotify, stackoverflow, substack, telegram, tiktok, twitch, vk, x (Twitter), youtube
- Custom regex pattern support for flexible URL matching
- Multiple pattern support per platform
- Automatic ID extraction from URLs
- Support for various URL formats (with/without protocol, www, mobile variants)
- Customizable regex flags for pattern matching
- Comprehensive error handling with custom exceptions:
  - `SocialLinksError` - Base exception
  - `PlatformNotFoundError` - Platform not found
  - `PlatformAlreadyExistsError` - Platform already exists
  - `InvalidPlatformError` - Invalid platform configuration
  - `PlatformIDExtractionError` - Failed to extract platform ID
  - `URLMismatchError` - URL doesn't match platform pattern
- Full test coverage with comprehensive test suite

### Features

- Zero external dependencies
- Python 3.8+ compatibility
- Case-insensitive URL matching (configurable)
- Support for username-only input (without full URLs)
- Automatic @ symbol handling
- URL normalization and sanitization

[1.1.0]: https://github.com/ysskrishna/social-links/releases/tag/v1.1.0
[1.0.0]: https://github.com/ysskrishna/social-links/releases/tag/v1.0.0
