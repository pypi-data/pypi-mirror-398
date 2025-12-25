"""Context analysis for password composition and structure.

Analyzes how password characters are distributed and mixed to detect
structural weaknesses like all digits at the end or uppercase only at start.
"""


def analyze_character_diversity(password: str) -> dict[str, int | bool]:
    """Analyze character type diversity.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict[str, int | bool]
        Character diversity metrics.

    Raises
    ------
    TypeError
        If password is not a string.

    Examples
    --------
    >>> result = analyze_character_diversity("Abc123!@#")
    >>> result["diversity_score"]
    4
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be str, got {type(password).__name__}")

    has_lowercase = any(c.islower() for c in password)
    has_uppercase = any(c.isupper() for c in password)
    has_digits = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    diversity_score = sum([has_lowercase, has_uppercase, has_digits, has_special])

    return {
        "has_lowercase": has_lowercase,
        "has_uppercase": has_uppercase,
        "has_digits": has_digits,
        "has_special": has_special,
        "diversity_score": diversity_score,
    }


def analyze_positional_patterns(password: str) -> dict[str, list[str]]:
    """Analyze positional patterns in password.

    Detects common weak patterns like:
    - All digits at the end
    - All special characters at the end
    - Only first character uppercase

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict[str, list[str]]
        Positional pattern detection results.

    Raises
    ------
    TypeError
        If password is not a string.

    Examples
    --------
    >>> result = analyze_positional_patterns("Password123")
    >>> "digits_at_end" in result["patterns"]
    True
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be str, got {type(password).__name__}")

    patterns = []

    if len(password) < 3:
        return {"patterns": patterns}

    # Check for digits clustered at end
    if password[-3:].isdigit() or (len(password) > 3 and password[-4:].isdigit()):
        patterns.append("digits_at_end")

    # Check for special chars at end
    trailing_special = sum(1 for c in password[-3:] if not c.isalnum())
    if trailing_special >= 2:
        patterns.append("special_at_end")

    # Check for uppercase only at start (weak pattern: Capital followed by all lowercase)
    # Only flag if there are actual letters after first char and they're all lowercase
    if password[0].isupper() and len(password) > 1:
        rest_letters = [c for c in password[1:] if c.isalpha()]
        if rest_letters and all(c.islower() for c in rest_letters):
            # Check if letters dominate (more than half of remaining chars)
            if len(rest_letters) > len(password[1:]) // 2:
                patterns.append("uppercase_at_start")

    return {"patterns": patterns}


def analyze_context(password: str) -> dict[str, dict | int]:
    """Comprehensive context analysis.

    Parameters
    ----------
    password : str
        Password to analyze.

    Returns
    -------
    dict[str, dict | int]
        Context analysis results with mixing score.

    Raises
    ------
    TypeError
        If password is not a string.

    Examples
    --------
    >>> result = analyze_context("P4s5w0r!d")
    >>> result["mixing_score"] >= 80
    True
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be str, got {type(password).__name__}")

    diversity = analyze_character_diversity(password)
    positional = analyze_positional_patterns(password)

    # Calculate mixing score (0-100)
    # Start with diversity score (0-4) * 20 = 0-80
    base_score = diversity["diversity_score"] * 20

    # Deduct for positional patterns (each pattern -15)
    pattern_penalty = len(positional["patterns"]) * 15
    mixing_score = max(0, min(100, base_score - pattern_penalty))

    return {
        "character_diversity": diversity,
        "positional_patterns": positional,
        "mixing_score": mixing_score,
    }
