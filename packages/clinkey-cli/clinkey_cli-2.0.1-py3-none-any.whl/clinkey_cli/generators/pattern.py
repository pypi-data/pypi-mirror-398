"""Pattern-based password generator using template syntax.

Generates passwords following custom patterns with character class definitions
like 'Cvvc-9999-Cvvc' for template-based password generation.
"""

import secrets
import string

from clinkey_cli.generators.base import BaseGenerator


class PatternGenerator(BaseGenerator):
    """Generate passwords from pattern templates.

    Supports character classes:
    - C = consonant
    - V = vowel
    - L = any letter (uppercase)
    - l = any letter (lowercase)
    - D = digit
    - S = special character
    - [abc] = custom character set
    - Any other character = literal

    Parameters
    ----------
    None

    Examples
    --------
    >>> gen = PatternGenerator()
    >>> password = gen.generate(pattern="Cvvc-9999")
    >>> len(password)
    9
    """

    def __init__(self) -> None:
        """Initialize pattern generator."""
        # Character sets
        self._consonants = list("bcdfghjklmnpqrstvwxz")
        self._vowels = list("aeiouy")
        self._digits = list(string.digits)
        self._specials = list("!@#$%^&*()-_=+[]{}|;:,.<>?")

    def validate_pattern(self, pattern: str) -> bool:
        """Validate pattern syntax.

        Parameters
        ----------
        pattern : str
            Pattern to validate.

        Returns
        -------
        bool
            True if pattern is valid.

        Examples
        --------
        >>> gen = PatternGenerator()
        >>> gen.validate_pattern("LLLL-DDDD")
        True
        >>> gen.validate_pattern("XYZ")
        False
        """
        if not pattern:
            return False

        # Parse pattern and check for valid character classes
        # Valid classes: C, V, L, l, D, S
        # Also accept: [custom], literals (-, @, etc.)
        i = 0
        has_valid_class = False

        while i < len(pattern):
            char = pattern[i]

            # Custom character set
            if char == "[":
                close = pattern.find("]", i)
                if close == -1:
                    return False  # Unclosed bracket
                has_valid_class = True
                i = close + 1
                continue

            # Character classes
            if char in "CVLlDS":
                has_valid_class = True
                i += 1
                continue

            # Check if it's a literal character
            # (not alphanumeric uppercase like X, Y, Z)
            # We accept lowercase letters, digits, and special chars
            # But uppercase letters that aren't C, V, L, D, S are invalid
            if char.isupper() and char.isalpha():
                # Uppercase letter that's not a valid class = invalid
                return False

            # Other characters (lowercase, digits, special) are valid literals
            i += 1

        return has_valid_class

    def get_pattern_length(self, pattern: str) -> int:
        """Calculate final password length from pattern.

        Parameters
        ----------
        pattern : str
            Pattern to analyze.

        Returns
        -------
        int
            Final password length.

        Examples
        --------
        >>> gen = PatternGenerator()
        >>> gen.get_pattern_length("LLLL-DDDD")
        9
        """
        length = 0
        i = 0

        while i < len(pattern):
            char = pattern[i]

            # Custom character set [abc]
            if char == "[":
                close = pattern.find("]", i)
                if close != -1:
                    length += 1
                    i = close + 1
                    continue

            # All characters contribute 1 to length
            length += 1
            i += 1

        return length

    def generate(
        self,
        length: int = 0,
        pattern: str | None = None,
        **kwargs,
    ) -> str:
        """Generate password from pattern.

        Parameters
        ----------
        length : int, default 0
            Ignored if pattern is provided
            (kept for BaseGenerator compatibility).
        pattern : str | None, default None
            Pattern template for password generation.
        **kwargs
            Additional arguments (ignored).

        Returns
        -------
        str
            Generated password matching pattern.

        Raises
        ------
        ValueError
            If pattern is invalid or missing.

        Examples
        --------
        >>> gen = PatternGenerator()
        >>> password = gen.generate(pattern="LLLL-DDDD")
        >>> len(password)
        9
        """
        # Validate inputs
        if pattern is None:
            if not length:
                raise ValueError(
                    "must provide either pattern or length parameter"
                )
            raise ValueError("pattern cannot be empty")

        if pattern == "":
            raise ValueError("pattern cannot be empty")

        if not self.validate_pattern(pattern):
            raise ValueError(f"Invalid pattern: '{pattern}'")

        # Generate password from pattern
        result = []
        i = 0

        while i < len(pattern):
            char = pattern[i]

            # Custom character set [abc]
            if char == "[":
                close = pattern.find("]", i)
                charset = pattern[i + 1:close]
                result.append(secrets.choice(list(charset)))
                i = close + 1
                continue

            # Character classes
            if char == "C":
                result.append(secrets.choice(self._consonants).upper())
            elif char == "V":
                result.append(secrets.choice(self._vowels).upper())
            elif char == "L":
                result.append(secrets.choice(string.ascii_uppercase))
            elif char == "l":
                result.append(secrets.choice(string.ascii_lowercase))
            elif char == "D":
                result.append(secrets.choice(self._digits))
            elif char == "S":
                result.append(secrets.choice(self._specials))
            else:
                # Literal character
                result.append(char)

            i += 1

        return "".join(result)
