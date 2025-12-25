"""Entropy calculation for password strength assessment.

Provides Shannon entropy and character-set-based entropy calculations
to measure password randomness and theoretical strength.
"""

import math
from collections import Counter


def calculate_shannon_entropy(password: str) -> float:
    """Calculate Shannon entropy in bits.

    Shannon entropy measures the average information content per character
    based on character frequency distribution.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    float
        Shannon entropy in bits per character.

    Examples
    --------
    >>> calculate_shannon_entropy("aaaa")
    0.0
    >>> calculate_shannon_entropy("abcd")
    2.0
    """
    if not password:
        return 0.0

    # Count character frequencies
    char_counts = Counter(password)
    length = len(password)

    # Calculate Shannon entropy: H = -Σ(p(x) * log₂(p(x)))
    entropy = 0.0
    for count in char_counts.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def calculate_charset_entropy(password: str, length: int) -> float:
    """Calculate theoretical entropy based on character set size.

    Assumes uniform random selection from the detected character set.

    Parameters
    ----------
    password : str
        Password to analyze for character set.
    length : int
        Password length.

    Returns
    -------
    float
        Theoretical entropy in bits.

    Examples
    --------
    >>> calculate_charset_entropy("abc", 3)
    14.094...
    """
    if not password or length <= 0:
        return 0.0

    # Detect character set size
    charset_size = _detect_charset_size(password)

    # Calculate entropy: log₂(charset_size^length) = length * log₂(charset_size)
    return length * math.log2(charset_size)


def _detect_charset_size(password: str) -> int:
    """Detect character set size from password.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    int
        Estimated character set size.
    """
    has_lowercase = any(c.islower() for c in password)
    has_uppercase = any(c.isupper() for c in password)
    has_digits = any(c.isdigit() for c in password)
    has_specials = any(not c.isalnum() for c in password)

    charset_size = 0
    if has_lowercase:
        charset_size += 26
    if has_uppercase:
        charset_size += 26
    if has_digits:
        charset_size += 10
    if has_specials:
        charset_size += 33  # Common special characters

    return max(charset_size, 1)  # Avoid division by zero


def get_entropy_score(password: str) -> dict:
    """Get comprehensive entropy analysis.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict
        Entropy analysis with Shannon entropy, charset entropy, and metrics.

    Examples
    --------
    >>> score = get_entropy_score("MyPassword123")
    >>> score["charset_size"]
    62
    """
    length = len(password)
    shannon = calculate_shannon_entropy(password)
    charset_size = _detect_charset_size(password)
    charset = calculate_charset_entropy(password, length)
    bits_per_char = charset / length if length > 0 else 0

    return {
        "shannon_entropy": shannon,
        "charset_entropy": charset,
        "bits_per_char": bits_per_char,
        "charset_size": charset_size,
        "length": length,
    }
