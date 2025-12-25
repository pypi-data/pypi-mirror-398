"""Language detection utility."""

import re
from typing import List

from ..types import Language


def _contains_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    # Chinese: 4E00-9FFF
    # Japanese Hiragana: 3040-309F
    # Japanese Katakana: 30A0-30FF
    # Korean Hangul: AC00-D7AF
    cjk_pattern = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
    return bool(cjk_pattern.search(text))


def detect_language(text: str, default: Language = "zh") -> Language:
    """
    Detect the language of the given text.

    Args:
        text: Text to detect language for
        default: Default language if detection fails

    Returns:
        Detected language code
    """
    if not text or not text.strip():
        return default

    # Count characters by type
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    japanese_hira = len(re.findall(r"[\u3040-\u309f]", text))
    japanese_kata = len(re.findall(r"[\u30a0-\u30ff]", text))
    korean = len(re.findall(r"[\uac00-\ud7af]", text))
    english = len(re.findall(r"[a-zA-Z]", text))

    # Determine dominant language
    japanese = japanese_hira + japanese_kata

    if korean > 0 and korean >= max(chinese, japanese, english):
        return "ko"
    if japanese > 0 and japanese >= max(chinese, korean, english):
        return "ja"
    if chinese > 0 and chinese >= max(japanese, korean, english):
        return "zh"
    if english > 0:
        return "en"

    return default


def detect_languages(texts: List[str], default: Language = "zh") -> List[Language]:
    """
    Detect languages for multiple texts.

    Args:
        texts: List of texts to detect languages for
        default: Default language if detection fails

    Returns:
        List of detected language codes
    """
    return [detect_language(text, default) for text in texts]
