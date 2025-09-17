from enum import Enum

class EMOJIS(str, Enum):
    HEADPHONE = '🎧'
    ADD = '➕'
    MIC = '🎤'
    TRASH = '🗑'
    CHECK_MARK = '✅'
    FAIL = '❌'
    LIST = '📋'
    MUSIC = '🎵'
    CAMERA = '📸'
    LINK = '🔗'
    FILE = '📂'
    LIST_WITH_PEN = '📝'
    PHOTO = '🖼️'
    NEW = '🆕'
    DANGER = '☠'
    PEN = '✍🏻'
    WARN = '⚠️'
    CLOCK = '⏰'
    QUESTION = '?'
    HUG = '🫂'
    STAR = '⭐'


def is_text_starts_with_emoji(text: str) -> bool:
    """
    Return True if the given text begins with one of the UI command emojis defined in EMOJIS.
    
    Strips leading/trailing whitespace before checking; returns False for empty or whitespace-only input. Only the first character (first Unicode code point) of the trimmed string is tested against the EMOJIS values.
    """
    text = text.strip()
    if not text:
        return False
    return any(text.startswith(e.value) for e in EMOJIS)