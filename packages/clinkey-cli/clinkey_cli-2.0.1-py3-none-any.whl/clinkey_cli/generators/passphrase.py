"""Passphrase generator using word-based (diceware-style) passwords.

Generates memorable passphrases by combining randomly selected words
from curated wordlists like the EFF large wordlist.
"""

import secrets
from typing import Any

from clinkey_cli.generators.base import BaseGenerator
from clinkey_cli.wordlists import EFF_LARGE_WORDLIST


# Wordlist registry
WORDLISTS = {
    "eff_large": EFF_LARGE_WORDLIST,
}

# Validation constants
MIN_WORD_COUNT = 3
MAX_WORD_COUNT = 10
DEFAULT_WORD_COUNT = 4


class PassphraseGenerator(BaseGenerator):
    """Generate passphrases from word lists.

    Creates memorable passphrases by combining randomly selected words
    from cryptographically secure wordlists.

    Parameters
    ----------
    wordlist : str, default "eff_large"
        Wordlist to use. Options: "eff_large".

    Attributes
    ----------
    wordlist_name : str
        Name of the loaded wordlist.
    _wordlist : list[str]
        Loaded wordlist.

    Examples
    --------
    >>> gen = PassphraseGenerator()
    >>> passphrase = gen.generate(word_count=4)
    >>> len(passphrase.split("-"))
    4
    """

    def __init__(self, wordlist: str = "eff_large"):
        """Initialize passphrase generator with wordlist.

        Parameters
        ----------
        wordlist : str, default "eff_large"
            Name of wordlist to use.

        Raises
        ------
        ValueError
            If wordlist name is not recognized.
        """
        if wordlist not in WORDLISTS:
            available = ", ".join(WORDLISTS.keys())
            raise ValueError(
                f"Unknown wordlist: '{wordlist}'. Available: {available}"
            )

        self.wordlist_name = wordlist
        self._wordlist = WORDLISTS[wordlist]

    def generate(
        self,
        length: int = 0,  # Ignored for passphrases
        word_count: int = DEFAULT_WORD_COUNT,
        separator: str = "-",
        capitalize: bool = True,
        **kwargs: Any,
    ) -> str:
        """Generate a passphrase.

        Parameters
        ----------
        length : int, default 0
            Ignored for passphrases (kept for BaseGenerator compatibility).
        word_count : int, default 4
            Number of words in passphrase.
        separator : str, default "-"
            Separator between words. Use "" for no separator.
        capitalize : bool, default True
            Capitalize first letter of each word.
        **kwargs
            Additional arguments (ignored).

        Returns
        -------
        str
            Generated passphrase.

        Raises
        ------
        ValueError
            If word_count is out of valid range.

        Examples
        --------
        >>> gen = PassphraseGenerator()
        >>> passphrase = gen.generate(word_count=4)
        >>> "-" in passphrase
        True
        """
        # Validate word count
        if word_count < MIN_WORD_COUNT:
            raise ValueError(
                f"word_count must be at least {MIN_WORD_COUNT}, got {word_count}"
            )
        if word_count > MAX_WORD_COUNT:
            raise ValueError(
                f"word_count cannot exceed {MAX_WORD_COUNT}, got {word_count}"
            )

        # Select random words
        words = [secrets.choice(self._wordlist) for _ in range(word_count)]

        # Apply capitalization (or enforce lowercase when disabled)
        if capitalize:
            words = [word.capitalize() for word in words]
        else:
            words = [word.upper() for word in words]

        # Join with separator
        return separator.join(words)
