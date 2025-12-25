"""Dictionary analysis for detecting common passwords and dictionary words.

Checks passwords against lists of common passwords and English dictionary
words to identify easily guessable passwords.
"""

from pathlib import Path
from typing import Any


# Load common passwords list
_DATA_DIR = Path(__file__).parent / "data"
_COMMON_PASSWORDS_FILE = _DATA_DIR / "common_passwords.txt"


def _load_common_passwords() -> set[str]:
    """Load common passwords from data file.

    Returns
    -------
    set[str]
        Set of common passwords (lowercase).
    """
    if not _COMMON_PASSWORDS_FILE.exists():
        return set()

    with open(_COMMON_PASSWORDS_FILE, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


# Pre-load common passwords
_COMMON_PASSWORDS = _load_common_passwords()


# Common English dictionary words (subset for lightweight detection)
_COMMON_WORDS = {
    "elephant", "tiger", "monkey", "dragon", "sunshine", "princess",
    "master", "admin", "welcome", "login", "password", "user", "guest",
    "blue", "red", "green", "yellow", "black", "white",
    "love", "hate", "happy", "sad", "angry", "peace",
    "computer", "laptop", "phone", "tablet", "keyboard",
    "summer", "winter", "spring", "autumn", "fall",
}


def check_common_password(password: str) -> dict[str, Any]:
    """Check if password is in common passwords list.

    Parameters
    ----------
    password : str
        Password to check.

    Returns
    -------
    dict[str, Any]
        Detection results with is_common flag and matches.

    Raises
    ------
    TypeError
        If password is not a string.

    Examples
    --------
    >>> result = check_common_password("password123")
    >>> result["is_common"]
    True
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a string, got {type(password).__name__}")

    if not password:
        return {
            "is_common": False,
            "matches": [],
        }

    password_lower = password.lower()

    # Direct match
    if password_lower in _COMMON_PASSWORDS:
        return {
            "is_common": True,
            "matches": [password_lower],
        }

    # Check for variations (with numbers appended)
    for common in _COMMON_PASSWORDS:
        if password_lower.startswith(common):
            # Check if rest is just numbers
            suffix = password_lower[len(common):]
            if suffix.isdigit() or not suffix:
                return {
                    "is_common": True,
                    "matches": [common],
                }

    return {
        "is_common": False,
        "matches": [],
    }


def check_dictionary_words(password: str) -> dict[str, Any]:
    """Check for dictionary words in password.

    Parameters
    ----------
    password : str
        Password to check.

    Returns
    -------
    dict[str, Any]
        Dictionary words found in password.

    Raises
    ------
    TypeError
        If password is not a string.

    Examples
    --------
    >>> result = check_dictionary_words("elephant2024")
    >>> len(result["words"]) > 0
    True
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a string, got {type(password).__name__}")

    if not password:
        return {
            "words": [],
        }

    password_lower = password.lower()
    found_words = []

    # Check for whole word matches
    if password_lower in _COMMON_WORDS:
        found_words.append(password_lower)
    else:
        # Check for embedded words (minimum 4 chars)
        for word in _COMMON_WORDS:
            if len(word) >= 4 and word in password_lower:
                found_words.append(word)

    return {
        "words": found_words,
    }


def analyze_dictionary(password: str) -> dict[str, Any]:
    """Comprehensive dictionary analysis.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict[str, Any]
        Dictionary analysis results with penalty score.

    Raises
    ------
    TypeError
        If password is not a string.

    Examples
    --------
    >>> result = analyze_dictionary("password123")
    >>> result["is_common"]
    True
    >>> result["score_penalty"] >= 50
    True
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a string, got {type(password).__name__}")

    if not password:
        return {
            "is_common": False,
            "common_matches": [],
            "dictionary_words": [],
            "word_count": 0,
            "score_penalty": 0,
        }

    common_check = check_common_password(password)
    word_check = check_dictionary_words(password)

    is_common = common_check["is_common"]
    common_matches = common_check["matches"]
    dictionary_words = word_check["words"]
    # Note: word_count counts common password matches and dictionary words separately.
    # If a password matches both common password and contains dictionary words,
    # both are counted to reflect total weakness indicators.
    word_count = len(common_matches) + len(dictionary_words)

    # Calculate penalty
    if is_common:
        score_penalty = 50  # Severe penalty for common passwords
    elif len(dictionary_words) > 0:
        # Penalty based on number and length of dictionary words
        score_penalty = min(len(dictionary_words) * 15, 40)
    else:
        score_penalty = 0

    return {
        "is_common": is_common,
        "common_matches": common_matches,
        "dictionary_words": dictionary_words,
        "word_count": word_count,
        "score_penalty": score_penalty,
    }
