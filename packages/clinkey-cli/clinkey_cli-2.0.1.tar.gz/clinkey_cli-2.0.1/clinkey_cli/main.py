"""
Core password generation logic for the Clinkey CLI package.

Exposes the :class:`Clinkey` password generator and a module-level ``clinkey``
instance used by the CLI entrypoints.

Note: This module now serves as a backward-compatible adapter to the new
generator architecture. The actual generation logic is in generators/syllable.py.
"""

import secrets
import string
from typing import Callable

from clinkey_cli.generators.syllable import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    SyllableGenerator,
)

# Re-export constants for backward compatibility
__all__ = [
    "Clinkey",
    "clinkey",
    "MAX_PASSWORD_LENGTH",
    "MAX_BATCH_SIZE",
    "MIN_PASSWORD_LENGTH",
    "SAFE_SEPARATOR_CHARS",
]

# Security and validation constants
MAX_BATCH_SIZE = 500

# Safe separator characters (printable, non-whitespace)
SAFE_SEPARATOR_CHARS = string.printable.replace(" \t\n\r\x0b\x0c", "")


class Clinkey:
    """Generate pronounceable passwords with configurable complexity levels.

    This class serves as a backward-compatible adapter to the new generator
    architecture introduced in Clinkey 2.0. It delegates to SyllableGenerator
    while maintaining the exact same API as Clinkey 1.x.

    Attributes
    ----------
    _generator : SyllableGenerator
        Internal syllable generator instance.
    _consonants : list[str]
        Consonants from the Latin alphabet (for backward compatibility).
    _vowels : list[str]
        Vowels from the Latin alphabet (for backward compatibility).
    _digits : list[str]
        Digits from ``0`` through ``9`` (for backward compatibility).
    _specials : list[str]
        Safe special characters (for backward compatibility).
    _simple_syllables : list[str]
        Consonant/vowel pairs (for backward compatibility).
    _complex_syllables : list[str]
        Predefined consonant clusters (for backward compatibility).
    _separators : list[str]
        Default separators (for backward compatibility).
    _generators : dict[str, Callable[[], str]]
        Mapping of password type to generator method (for backward compatibility).
    new_separator : str | None
        Custom separator overriding defaults (for backward compatibility).

    Methods
    -------
    normal()
        Generate a pronounceable password made of words and separators.
    strong()
        Generate a password made of words, digits, and separators.
    super_strong()
        Generate a password with all character types.
    generate_password(...)
        Generate a single password with specified parameters.
    generate_batch(...)
        Generate multiple passwords.
    """

    def __init__(self) -> None:
        """Initialize the Clinkey password generator."""
        # Initialize internal generator
        self._generator = SyllableGenerator(language="english")

        # Store custom separator (backward compatibility)
        self.new_separator = None

        # Expose internal attributes for backward compatibility
        self._consonants = self._generator._consonants
        self._vowels = self._generator._vowels
        self._digits = self._generator._digits
        self._specials = self._generator._specials
        self._simple_syllables = self._generator._simple_syllables
        self._complex_syllables = self._generator._complex_syllables
        self._separators = self._generator._separators
        self._generators = {
            "normal": self.normal,
            "strong": self.strong,
            "super_strong": self.super_strong,
        }

    def normal(self) -> str:
        """Generate a pronounceable password made of words and separators.

        Returns
        -------
        str
            A password containing uppercase letters and separators.

        Examples
        --------
        >>> clinkey = Clinkey()
        >>> password = clinkey.normal()
        >>> len(password) > 0
        True
        """
        return self._generator.normal()

    def strong(self) -> str:
        """Generate a password made of words, digits, and separators.

        Returns
        -------
        str
            A password with uppercase letters, digits, and separators.

        Examples
        --------
        >>> clinkey = Clinkey()
        >>> password = clinkey.strong()
        >>> any(c.isdigit() for c in password)
        True
        """
        return self._generator.strong()

    def super_strong(self) -> str:
        """Generate a password with all character types.

        Returns
        -------
        str
            A password with letters, digits, special chars, and separators.

        Examples
        --------
        >>> clinkey = Clinkey()
        >>> password = clinkey.super_strong()
        >>> any(c.isalpha() for c in password)
        True
        """
        return self._generator.super_strong()

    def _fit_to_length(
        self, generator: Callable[[], str], target_length: int
    ) -> str:
        """Compose a password until the requested length is exactly reached.

        Parameters
        ----------
        generator : Callable[[], str]
            Function that yields password chunks (e.g. ``self.normal``).
        target_length : int
            Desired length for the final password.

        Returns
        -------
        str
            Generated password whose length exactly matches ``target_length``.
        """
        # Initializing an accumulator string, not a hardcoded credential.
        password = ""  # nosec B105
        while len(password) < target_length:
            chunk = generator()
            if len(password) + len(chunk) <= target_length:
                password += chunk
            else:
                remaining = target_length - len(password)
                password += chunk[:remaining]
                break
        return password

    def generate_password(
        self,
        length: int = 16,
        type: str = "normal",
        lower: bool = False,
        no_separator: bool = False,
        new_separator: str | None = None,
        output: str | None = None,
    ) -> str:
        """Generate a single password matching the requested configuration.

        Parameters
        ----------
        length : int, default 16
            Length of the password to produce.
        type : str, default "normal"
            Password preset to use. Options: "normal", "strong", "super_strong".
        lower : bool, default False
            Convert the final password to lowercase if True.
        no_separator : bool, default False
            Remove separator characters if True.
        new_separator : str | None, default None
            Custom separator character to use instead of defaults.
        output : str | None, default None
            Optional output path consumed by the CLI layer; no file I/O is
            performed inside this method.

        Returns
        -------
        str
            Generated password.

        Raises
        ------
        ValueError
            If length is not strictly positive, exceeds max, is below min,
            or type is unknown.
            If new_separator is not exactly one safe printable character.

        Examples
        --------
        >>> clinkey = Clinkey()
        >>> password = clinkey.generate_password(length=20, type="strong")
        >>> len(password)
        20
        """
        if length < MIN_PASSWORD_LENGTH:
            raise ValueError(f"length must be at least {MIN_PASSWORD_LENGTH}")
        if length > MAX_PASSWORD_LENGTH:
            raise ValueError(f"length cannot exceed {MAX_PASSWORD_LENGTH}")

        # Validate separator if provided
        separator_to_use = (
            new_separator if new_separator is not None else self.new_separator
        )
        if separator_to_use:
            if len(separator_to_use) != 1:
                raise ValueError("separator must be exactly one character")
            if separator_to_use not in SAFE_SEPARATOR_CHARS:
                raise ValueError(
                    "separator must be a safe printable character (no whitespace)"
                )

        # Validate type
        key = type.strip().lower()
        if key not in self._generators:
            valid = ", ".join(sorted(self._generators.keys()))
            raise ValueError(
                f"Unsupported type '{type}'. Choose among: {valid}."
            )

        # Temporarily override separator for this generation if provided
        previous_separator = self.new_separator
        previous_gen_separators = self._generator._separators.copy()
        if new_separator is not None:
            self.new_separator = new_separator
            self._generator._separators = [new_separator]

        try:
            raw_password = self._fit_to_length(self._generators[key], length)
        finally:
            # Restore previous separator to avoid leaking state between calls
            self.new_separator = previous_separator
            self._generator._separators = previous_gen_separators

        separators_to_strip = "-_"
        effective_separator = (
            new_separator if new_separator is not None else previous_separator
        )
        if effective_separator and effective_separator not in "-_":
            separators_to_strip += effective_separator

        cleaned = raw_password.strip(separators_to_strip)

        if no_separator:
            cleaned = cleaned.replace("-", "").replace("_", "")
            if effective_separator and effective_separator not in "-_":
                cleaned = cleaned.replace(effective_separator, "")

        if lower:
            cleaned = cleaned.lower()

        return cleaned

    def generate_batch(
        self,
        length: int = 16,
        type: str = "normal",
        count: int = 1,
        lower: bool = False,
        no_separator: bool = False,
        new_separator: str | None = None,
        output: str | None = None,
    ) -> list[str]:
        """Generate multiple passwords with the same configuration.

        Parameters
        ----------
        length : int, default 16
            Length of each password.
        type : str, default "normal"
            Password preset to use.
        count : int, default 1
            Number of passwords to generate.
        lower : bool, default False
            Convert passwords to lowercase if True.
        no_separator : bool, default False
            Remove separator characters if True.
        new_separator : str | None, default None
            Custom separator character to use.
        output : str | None, default None
            Optional output path retained for interface parity with the CLI.

        Returns
        -------
        list[str]
            List of generated passwords.

        Raises
        ------
        ValueError
            If count is not a positive integer or exceeds MAX_BATCH_SIZE.

        Examples
        --------
        >>> clinkey = Clinkey()
        >>> passwords = clinkey.generate_batch(count=5, length=16)
        >>> len(passwords)
        5
        """
        # Validate count
        if count <= 0:
            raise ValueError("count must be a positive integer")
        if count > MAX_BATCH_SIZE:
            raise ValueError(f"count cannot exceed {MAX_BATCH_SIZE}")

        # Generate batch
        return [
            self.generate_password(
                length=length,
                type=type,
                lower=lower,
                no_separator=no_separator,
                new_separator=new_separator,
            )
            for _ in range(count)
        ]


clinkey = Clinkey()
