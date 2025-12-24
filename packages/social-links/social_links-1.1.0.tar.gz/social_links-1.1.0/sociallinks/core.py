import re
from typing import Dict, List, Optional, Any, Tuple
from sociallinks.platforms import PREDEFINED_PLATFORMS
from sociallinks.exceptions import (
    PlatformNotFoundError,
    PlatformAlreadyExistsError,
    InvalidPlatformError,
    PlatformIDExtractionError,
    URLMismatchError,
)


class SocialLinks:
    """
    Social Media URL Sanitizer.
    """

    def __init__(
        self,
        use_predefined_platforms: bool = True,
        regex_flags: int = re.IGNORECASE,
    ):
        self.platforms: Dict[str, Any] = {}
        self._compiled: Dict[str, List[Tuple[re.Pattern, str]]] = {}
        self.regex_flags = regex_flags

        if use_predefined_platforms:
            self.platforms.update(PREDEFINED_PLATFORMS)

        # Compile all
        for name, data in self.platforms.items():
            self._compile_platform(name, data)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _compile_platform(self, name: str, data: Any) -> None:
        compiled_entries: List[Tuple[re.Pattern, str]] = []
        entries = data if isinstance(data, list) else [data]

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            patterns = entry.get("patterns")
            sanitized = entry.get("sanitized")

            if not patterns or not sanitized:
                continue

            for p in (patterns if isinstance(patterns, list) else [patterns]):
                compiled_entries.append(
                    (re.compile(p, flags=self.regex_flags), sanitized)
                )

        if not compiled_entries:
            raise InvalidPlatformError(f"Platform '{name}' has no valid patterns or templates.")

        self._compiled[name] = compiled_entries

    @staticmethod
    def _extract_id(match: re.Match) -> Optional[str]:
        if "id" in match.groupdict() and match.group("id"):
            return match.group("id")

        for g in match.groups():
            if g:
                return g
        return None

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def detect_platform(self, url: str) -> Optional[str]:
        u = url.strip()
        for name, entries in self._compiled.items():
            if any(pattern.search(u) for pattern, _ in entries):
                return name
        return None

    def is_valid(self, platform_name: str, url: str) -> bool:
        entries = self._compiled.get(platform_name)
        if not entries:
            return False
        u = url.strip()
        return any(pattern.search(u) for pattern, _ in entries)

    def sanitize(self, platform_name: str, url: str) -> str:
        entries = self._compiled.get(platform_name)
        if not entries:
            raise PlatformNotFoundError(f"Unknown platform: {platform_name}")

        u = url.strip()
        for pattern, sanitized in entries:
            m = pattern.search(u)
            if m:
                pid = self._extract_id(m)
                if not pid:
                    raise PlatformIDExtractionError("Could not extract platform ID")
                pid = pid.strip().lstrip("@").rstrip("/")
                return sanitized.format(id=pid)

        raise URLMismatchError(f"URL does not match platform '{platform_name}'")

    # ------------------------------------------------------------------
    # Platform CRUD (single + bulk)
    # ------------------------------------------------------------------

    def set_platform(self, name: str, data: Any, *, override: bool = False) -> None:
        """
        Unified add/override method.
        - override=False → error if exists
        - override=True → force replace
        """
        exists = name in self.platforms
        if exists and not override:
            raise PlatformAlreadyExistsError(f"Platform '{name}' already exists. Use override=True.")

        self.platforms[name] = data
        self._compile_platform(name, data)

    def delete_platform(self, name: str) -> None:
        if name not in self.platforms:
            raise PlatformNotFoundError(f"Platform '{name}' not found")
        del self.platforms[name]
        self._compiled.pop(name, None)

    def set_platforms(self, platforms: Dict[str, Any], *, override: bool = False) -> None:
        """
        Bulk add/override.
        """
        if not override:
            conflicts = [name for name in platforms if name in self.platforms]
            if conflicts:
                raise PlatformAlreadyExistsError(f"Platforms already exist: {', '.join(conflicts)}")

        for name, data in platforms.items():
            self.set_platform(name, data, override=override)

    def delete_platforms(self, names: List[str]) -> None:
        missing = [n for n in names if n not in self.platforms]
        if missing:
            raise PlatformNotFoundError(f"Platforms not found: {', '.join(missing)}")
        for n in names:
            self.delete_platform(n)

    def clear_platforms(self) -> None:
        self.platforms.clear()
        self._compiled.clear()

    def get_platform(self, name: str) -> Any:
        if name not in self.platforms:
            raise PlatformNotFoundError(f"Platform '{name}' not found")
        return self.platforms[name]

    def list_platforms(self) -> List[str]:
        return list(self.platforms.keys())
