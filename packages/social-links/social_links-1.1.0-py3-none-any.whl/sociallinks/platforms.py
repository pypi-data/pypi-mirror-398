from typing import Dict, List, Any

# ----------------------------------------------------------------------
# Common ID regex
# ----------------------------------------------------------------------
PROFILE_ID = r"(?P<id>[A-Za-z0-9_.-]+)"

# ----------------------------------------------------------------------
# Predefined platforms
# ----------------------------------------------------------------------
PREDEFINED_PLATFORMS: Dict[str, List[Dict[str, Any]]] = {
    "behance": [
        {
            "patterns": [
                rf"https?://(www\.)?behance\.net/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://behance.net/{id}"
        }
    ],
    "dev_to": [
        {
            "patterns": [
                rf"https?://(www\.)?dev\.to/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://dev.to/{id}"
        }
    ],
    "dribbble": [
        {
            "patterns": [
                rf"https?://(www\.)?dribbble\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://dribbble.com/{id}"
        }
    ],
    "exercism": [
        {
            "patterns": [
                rf"https?://(www\.)?exercism\.io/profiles/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://exercism.io/profiles/{id}"
        }
    ],
    "facebook": [
        {
            "patterns": [
                rf"https?://(www\.)?facebook\.com/{PROFILE_ID}/?$",
                rf"https?://m\.facebook\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://facebook.com/{id}"
        }
    ],
    "github": [
        {
            "patterns": [
                rf"https?://(www\.)?github\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://github.com/{id}"
        }
    ],
    "instagram": [
        {
            "patterns": [
                rf"https?://(www\.)?instagram\.com/{PROFILE_ID}/?$",
                rf"https?://m\.instagram\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://instagram.com/{id}"
        }
    ],
    "keybase": [
        {
            "patterns": [
                rf"https?://(www\.)?keybase\.io/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://keybase.io/{id}"
        }
    ],
    "lemmy_world": [
        {
            "patterns": [
                rf"https?://lemmy\.world/u/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://lemmy.world/u/{id}"
        }
    ],
    "linkedin": [
        {
            "patterns": [
                rf"https?://([a-z]{{2,3}}\.)?linkedin\.com/in/{PROFILE_ID}/?$",
                rf"https?://([a-z]{{2,3}}\.)?linkedin\.com/mwlite/in/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://linkedin.com/in/{id}"
        },
        {
            "patterns": [
                rf"https?://(www\.)?linkedin\.com/company/{PROFILE_ID}/?$"
            ],
            "sanitized": "https://www.linkedin.com/company/{id}/"
        }
    ],
    "linktree": [
        {
            "patterns": [
                rf"https?://(www\.)?linktr\.ee/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://linktr.ee/{id}"
        }
    ],
    "mastodon": [
        {
            "patterns": [
                rf"https?://(www\.)?mastodon\.social/@{PROFILE_ID}/?$",
                rf"https?://(www\.)?mstdn\.social/@{PROFILE_ID}/?$",
                rf"https?://(www\.)?mastodon\.world/@{PROFILE_ID}/?$",
                rf"^@?{PROFILE_ID}$"
            ],
            "sanitized": "https://mastodon.social/@{id}"
        }
    ],
    "medium": [
        {
            "patterns": [
                rf"https?://(www\.)?medium\.com/@{PROFILE_ID}/?$",
                rf"^@?{PROFILE_ID}$"
            ],
            "sanitized": "https://medium.com/@{id}"
        }
    ],
    "patreon": [
        {
            "patterns": [
                rf"https?://(www\.)?patreon\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://patreon.com/{id}"
        }
    ],
    "pinterest": [
        {
            "patterns": [
                rf"https?://([a-z]{{1,3}}\.)?pinterest\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://pinterest.com/{id}"
        }
    ],
    "soundcloud": [
        {
            "patterns": [
                rf"https?://(www\.)?soundcloud\.com/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://soundcloud.com/{id}"
        }
    ],
    "spotify": [
        {
            "patterns": [
                rf"https?://(open\.)?spotify\.com/artist/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://open.spotify.com/artist/{id}"
        }
    ],
    "stackoverflow": [
        {
            "patterns": [
                rf"https?://(www\.)?stackoverflow\.com/users/{PROFILE_ID}(/[A-Za-z0-9_\\-\\.]+)?/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://stackoverflow.com/users/{id}"
        }
    ],
    "substack": [
        {
            "patterns": [
                rf"https?://{PROFILE_ID}\.substack\.com/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://{id}.substack.com"
        }
    ],
    "telegram": [
        {
            "patterns": [
                rf"https?://(www\.)?(t\.me|telegram\.me)/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://t.me/{id}"
        }
    ],
    "tiktok": [
        {
            "patterns": [
                rf"https?://(www\.)?tiktok\.com/@{PROFILE_ID}/?$",
                rf"^@?{PROFILE_ID}$"
            ],
            "sanitized": "https://tiktok.com/@{id}"
        }
    ],
    "twitch": [
        {
            "patterns": [
                rf"https?://(www\.)?twitch\.tv/{PROFILE_ID}/?$",
                rf"https?://m\.twitch\.tv/{PROFILE_ID}/?$",
                rf"^{PROFILE_ID}$"
            ],
            "sanitized": "https://twitch.tv/{id}"
        }
    ],
    "vk": [
        {
            "patterns": [
                rf"https?://(www\.)?vk\.com/{PROFILE_ID}/?$",
                rf"https?://m\.vk\.com/@?{PROFILE_ID}/?$",
                rf"^@?{PROFILE_ID}$"
            ],
            "sanitized": "https://vk.com/{id}"
        }
    ],
    "x": [
        {
            "patterns": [
                rf"https?://(www\.)?twitter\.com/@?{PROFILE_ID}/?$",
                rf"https?://mobile\.twitter\.com/@?{PROFILE_ID}/?$",
                rf"https?://x\.com/@?{PROFILE_ID}/?$",
                rf"^@?{PROFILE_ID}$"
            ],
            "sanitized": "https://x.com/{id}"
        }
    ],
    "youtube": [
        {
            "patterns": [
                rf"https?://(www\.)?youtube\.com/@?{PROFILE_ID}/?$",
                rf"https?://(www\.)?youtube\.com/channel/{PROFILE_ID}/?$",
                rf"https?://(www\.)?youtube\.com/user/{PROFILE_ID}/?$",
                rf"https?://m\.youtube\.com/c/{PROFILE_ID}/?$",
                rf"^@?{PROFILE_ID}$"
            ],
            "sanitized": "https://youtube.com/@{id}"
        }
    ]
}
