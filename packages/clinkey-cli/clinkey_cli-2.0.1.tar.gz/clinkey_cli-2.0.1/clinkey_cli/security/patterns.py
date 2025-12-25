"""Pattern detection for identifying security-weakening patterns.

Detects keyboard walks, sequential characters, repetitions, and other
patterns that reduce password entropy and security.
"""

import re


# Common keyboard layouts
QWERTY_ROWS = [
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
    "1234567890",
]


def detect_keyboard_walks(password: str) -> list[dict]:
    """Detect keyboard walk patterns.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    list[dict]
        List of detected keyboard walk patterns.

    Examples
    --------
    >>> patterns = detect_keyboard_walks("qwerty")
    >>> len(patterns) > 0
    True
    """
    patterns = []
    password_lower = password.lower()

    for row in QWERTY_ROWS:
        # Check forward and backward walks
        for i in range(len(row) - 2):
            walk = row[i : i + 3]
            reverse_walk = walk[::-1]

            if walk in password_lower or reverse_walk in password_lower:
                patterns.append(
                    {
                        "type": "keyboard_walk",
                        "pattern": walk,
                        "severity": "medium",
                    }
                )

    return patterns


def detect_sequences(password: str) -> list[dict]:
    """Detect sequential character patterns.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    list[dict]
        List of detected sequences.

    Examples
    --------
    >>> patterns = detect_sequences("abc123")
    >>> len(patterns) > 0
    True
    """
    patterns = []
    password_lower = password.lower()

    # Detect alphabetic sequences
    for i in range(len(password_lower) - 2):
        if password_lower[i : i + 3].isalpha():
            chars = password_lower[i : i + 3]
            if _is_alphabetic_sequence(chars):
                patterns.append(
                    {
                        "type": "alphabetic_sequence",
                        "pattern": chars,
                        "severity": "medium",
                    }
                )

    # Detect numeric sequences
    for i in range(len(password) - 2):
        if password[i : i + 3].isdigit():
            nums = password[i : i + 3]
            if _is_numeric_sequence(nums):
                patterns.append(
                    {
                        "type": "numeric_sequence",
                        "pattern": nums,
                        "severity": "medium",
                    }
                )

    return patterns


def _is_alphabetic_sequence(chars: str) -> bool:
    """Check if characters form alphabetic sequence."""
    if len(chars) < 3:
        return False
    return (
        ord(chars[1]) == ord(chars[0]) + 1 and ord(chars[2]) == ord(chars[1]) + 1
    ) or (
        ord(chars[1]) == ord(chars[0]) - 1 and ord(chars[2]) == ord(chars[1]) - 1
    )


def _is_numeric_sequence(nums: str) -> bool:
    """Check if numbers form numeric sequence."""
    if len(nums) < 3:
        return False
    return (
        int(nums[1]) == int(nums[0]) + 1 and int(nums[2]) == int(nums[1]) + 1
    ) or (
        int(nums[1]) == int(nums[0]) - 1 and int(nums[2]) == int(nums[1]) - 1
    )


def detect_repetitions(password: str) -> list[dict]:
    """Detect repeated character/sequence patterns.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    list[dict]
        List of detected repetitions.

    Examples
    --------
    >>> patterns = detect_repetitions("aaa")
    >>> len(patterns) > 0
    True
    """
    patterns = []

    # Detect character repetitions (3+ same chars)
    for match in re.finditer(r"(.)\1{2,}", password):
        patterns.append(
            {
                "type": "character_repetition",
                "pattern": match.group(),
                "severity": "high",
            }
        )

    # Detect sequence repetitions (e.g., 123123)
    for length in range(2, len(password) // 2 + 1):
        for i in range(len(password) - length * 2 + 1):
            sequence = password[i : i + length]
            next_sequence = password[i + length : i + length * 2]
            if sequence == next_sequence:
                patterns.append(
                    {
                        "type": "sequence_repetition",
                        "pattern": sequence * 2,
                        "severity": "high",
                    }
                )

    return patterns


def analyze_patterns(password: str) -> dict:
    """Comprehensive pattern analysis.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict
        Pattern analysis results.

    Examples
    --------
    >>> result = analyze_patterns("qwerty123")
    >>> result["pattern_count"] > 0
    True
    """
    keyboard_walks = detect_keyboard_walks(password)
    sequences = detect_sequences(password)
    repetitions = detect_repetitions(password)

    all_patterns = keyboard_walks + sequences + repetitions
    pattern_count = len(all_patterns)

    # Estimate entropy reduction from patterns
    entropy_reduction = min(pattern_count * 10, 50)  # Cap at 50 bits

    return {
        "keyboard_walks": keyboard_walks,
        "sequences": sequences,
        "repetitions": repetitions,
        "pattern_count": pattern_count,
        "entropy_reduction": entropy_reduction,
    }
