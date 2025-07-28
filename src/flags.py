FLAG_EMOJIS = {
    "USA": "🇺🇸",
    "Germany": "🇩🇪",
    "Israel": "🇮🇱",
    "China": "🇨🇳",
    "Russia": "🇷🇺",
    "Denmark": "🇩🇰",
    "United Kingdom": "🇬🇧",
    "France": "🇫🇷",
    "Canada": "🇨🇦",
    "Japan": "🇯🇵",
    "India": "🇮🇳",
    "Global": "🌐",
}


def get_flag(country: str) -> str:
    """Return the emoji flag for a given country name."""
    return FLAG_EMOJIS.get(country, "")
