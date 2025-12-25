"""Syllable-based password generator.

Generates pronounceable passwords using consonant-vowel syllable patterns.
This is the original Clinkey generation method, refactored into the new
generator architecture while maintaining 100% backward compatibility.
"""

import secrets
import string
from typing import Callable

from clinkey_cli.generators.base import BaseGenerator

# Security and validation constants
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 16


class SyllableGenerator(BaseGenerator):
    """Generate pronounceable passwords using syllable patterns.

    Supports multiple complexity levels (normal, strong, super_strong) and
    customizable separators. Uses cryptographically secure randomness.

    Parameters
    ----------
    language : str, default "english"
        Syllable set language (currently only "english" supported).

    Attributes
    ----------
    _consonants : list[str]
        Consonants used to build syllables.
    _vowels : list[str]
        Vowels used to build syllables.
    _digits : list[str]
        Digits used in strong/super_strong passwords.
    _specials : list[str]
        Special characters used in super_strong passwords.
    _simple_syllables : list[str]
        Consonant-vowel pairs for basic pronounceability.
    _complex_syllables : list[str]
        More complex consonant clusters.
    _separators : list[str]
        Default separator characters.
    language : str
        Current language setting.
    """

    def __init__(self, language: str = "english"):
        """Initialize syllable generator with specified language.

        Parameters
        ----------
        language : str, default "english"
            Language for syllable patterns.
        """
        self.language = language

        # Character sets
        self._consonants = list("bcdfghjklmnpqrstvwxz")
        self._vowels = list("aeiouy")
        self._digits = list(string.digits)
        self._specials = list("!@#$%^€£-_;:,.?")

        # Build syllable sets
        self._simple_syllables = [
            c + v for c in self._consonants for v in self._vowels
        ]
        self._complex_syllables = [
            "TRE", "TRI", "TRO", "TRA", "TRU", "TRY", "TSA", "TSE",
            "TSI", "TSO", "TSU", "TSY", "DRE", "DRI", "DRO", "DRA",
            "DRU", "DRY", "BRE", "BRI", "BRO", "BRA", "BRU", "BRY",
            "BLA", "BLE", "BLI", "BLO", "BLU", "BLY", "CRE", "CRI",
            "CRO", "CRA", "CRU", "CRY", "CHA", "CHE", "CHI", "CHO",
            "CHU", "CHY", "FRE", "FRI", "FRO", "FRA", "FRY", "FLA",
            "FLE", "FLI", "FLO", "FLU", "FLY", "GRE", "GRI", "GRO",
            "GRA", "GRU", "GRY", "GLA", "GLE", "GLI", "GLO", "GLU",
            "GLY", "GNA", "GNE", "GNI", "GNO", "GNU", "GNY", "PRE",
            "PRI", "PRO", "PRA", "PRU", "PRY", "PLA", "PLE", "PLI",
            "PLO", "PLU", "PLY", "QUA", "QUE", "QUI", "QUO", "QUY",
            "SRE", "SRI", "SRO", "SRA", "SRU", "SRY", "SLA", "SLE",
            "SLI", "SLO", "SLU", "SLY", "STA", "STE", "STI", "STO",
            "STU", "STY", "SNA", "SNE", "SNI", "SNO", "SNU", "SNY",
            "SMA", "SME", "SMI", "SMO", "SMU", "SMY", "SHA", "SHE",
            "SHI", "SHO", "SHU", "SHY", "SPY", "SPA", "SPE", "SPI",
            "SPO", "SPU", "VRE", "VRI", "VRO", "VRA", "VRU", "VRY",
            "VLA", "VLE", "VLI", "VLO", "VLU", "VLY", "VNA", "VNE",
            "VNI", "VNO", "VNU", "VNY", "VHA", "VHE", "VHI", "VHO",
            "VHU", "VHY", "VJA", "VJE", "VJI", "VJO", "VJU", "VJY",
            "WHA", "WHE", "WHI", "WHO", "WHU", "ZRE", "ZRU", "ZRI",
            "ZRO", "ZRA", "ABD", "ABF", "ABG", "ABH", "ABJ", "ABK",
            "ABL", "ABN", "ABR", "ABS", "ABT", "ABV", "ABZ", "ACD",
            "ACF", "ACH", "ACJ", "ACK", "ACL", "ACM", "ACN", "ACP",
            "ACR", "ACS", "ACT", "ACV", "ACZ", "EBD", "EBF", "EBH",
            "EBJ", "EBK", "EBL", "EBN", "EBR", "EBS", "EBT", "EBV",
            "EBZ", "ECF", "ECH", "ECJ", "ECK", "ECL", "ECM", "ECN",
            "ECP", "ECR", "ECS", "ECT", "ECV", "ECZ", "EDF", "EDH",
            "EDJ", "EDK", "EDL", "EDN", "EDR", "EDS", "EDT", "EDV",
            "EDZ", "EFF", "EFH", "EFJ", "EFK", "EFL", "EFN", "EFP",
            "EFR", "EFS", "EFT", "EFV", "EFZ", "EGF", "EGH", "EGJ",
            "EGK", "EGL", "EGN", "EGP", "EGR", "EGS", "EGT", "EGV",
            "EGZ", "EHF", "EHJ", "EHK", "EHL", "EHN", "EHP", "EHR"
        ]

        # Default separators
        self._separators = ["-"]

        # Generator method mapping
        self._generators: dict[str, Callable[[], list[str]]] = {
            "normal": self._normal_words,
            "strong": self._strong_words,
            "super_strong": self._super_strong_words,
        }

    def generate(
        self,
        length: int,
        # This is a preset label, not a hardcoded password.
        password_type: str = "normal",  # nosec B107
        lower: bool = False,
        no_separator: bool = False,
        separator: str | None = None,
    ) -> str:
        """Generate syllable-based password.

        Parameters
        ----------
        length : int
            Target password length.
        password_type : str, default "normal"
            Password complexity: "normal", "strong", or "super_strong".
        lower : bool, default False
            Convert to lowercase if True.
        no_separator : bool, default False
            Remove separators if True.
        separator : str | None, default None
            Custom separator to use instead of default.

        Returns
        -------
        str
            Generated password of specified length.

        Raises
        ------
        ValueError
            If length is invalid or password_type is unsupported.
        """
        # Validate length
        if length < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"length must be at least {MIN_PASSWORD_LENGTH}, got {length}"
            )
        if length > MAX_PASSWORD_LENGTH:
            raise ValueError(
                f"length cannot exceed {MAX_PASSWORD_LENGTH}, got {length}"
            )

        # Validate password type
        if password_type not in self._generators:
            valid_types = ", ".join(sorted(self._generators.keys()))
            raise ValueError(
                f"Unsupported type: '{password_type}'. "
                f"Valid types: {valid_types}"
            )

        # Generate base password
        generator = self._generators[password_type]
        separator_to_use = secrets.choice(self._separators)
        words = generator()

        # Extend with new unique words instead of repeating patterns to reach
        # the desired length safely.
        words = self._extend_words_to_length(words, length, separator_to_use)

        password = self._join_words(words, separator_to_use)

        # Fit to target length
        password = self.fit_to_length(password, length)

        # Apply transformations
        password = self.transform(password, lower, no_separator, separator)

        return password

    def _random_word_lengths(self) -> list[int]:
        """Pick random syllable counts for the four words.

        Guarantees at least one word uses multiple CV pairs so we never fall
        back to a CV-CV-CV-CV-CV pattern.
        """

        while True:
            lengths = [secrets.choice((1, 2, 3, 4)) for _ in range(4)]

            # Avoid devolving into uniform or overly short words. We want
            # mostly multi-syllable words with at least one 3–4 syllable word
            # and at most one single-syllable segment.
            if lengths.count(1) > 1:
                continue
            if max(lengths) < 3:
                continue
            if len(set(lengths)) == 1:
                continue
            if sum(1 for length in lengths if length >= 2) < 3:
                continue

            return lengths

    def _generate_word(self, syllable_count: int) -> str:
        """Generate a word with random selection of simple/complex syllables."""

        syllables = []
        # Combine pools of syllables
        # simple: ~120 combinations (consonant + vowel)
        # complex: ~170 combinations (clusters)
        all_syllables = self._simple_syllables + self._complex_syllables

        for _ in range(syllable_count):
            syllable = secrets.choice(all_syllables)
            syllables.append(syllable)

        return "".join(syllables).upper()

    def _build_word_list(self) -> list[str]:
        """Create the four-word base used by all variants."""

        words: list[str] = []
        seen: set[str] = set()

        for count in self._random_word_lengths():
            word = self._generate_word(count)
            while word in seen:
                word = self._generate_word(count)
            seen.add(word)
            words.append(word)

        return words

    def _letters_only(self, word: str) -> str:
        """Strip non-letters for uniqueness checks."""

        return "".join(ch for ch in word if ch.isalpha())

    def _generate_unique_word(self, seen: set[str]) -> str:
        """Generate a new word that does not duplicate prior words."""

        while True:
            count = secrets.choice((1, 2, 3, 4))
            candidate = self._generate_word(count)
            if self._letters_only(candidate) not in seen:
                return candidate

    def _extend_words_to_length(
        self, words: list[str], target_length: int, separator: str
    ) -> list[str]:
        """Extend word list with new unique words until assembled length fits."""

        seen_letters = {self._letters_only(w) for w in words}

        while len(separator.join(words)) < target_length:
            new_word = self._generate_unique_word(seen_letters)
            words.append(new_word)
            seen_letters.add(self._letters_only(new_word))

        return words

    def _join_words(self, words: list[str], separator: str | None = None) -> str:
        """Join words with a consistent separator."""

        return (separator or secrets.choice(self._separators)).join(words)

    def _normal_words(self) -> list[str]:
        """Generate normal password words: letters and separators only."""

        return self._build_word_list()

    def _strong_words(self) -> list[str]:
        """Generate strong password words: letters, digits, and separators."""

        words = self._build_word_list()
        digit_block = "".join(secrets.choice(self._digits) for _ in range(2))

        # Prefix digits to the first word so they survive truncation
        words[0] = digit_block + words[0]

        return words

    def _super_strong_words(self) -> list[str]:
        """Generate super strong password words: letters, digits, specials, separators."""

        words = self._build_word_list()
        digit_block = "".join(secrets.choice(self._digits) for _ in range(2))
        special_char = secrets.choice(self._specials)

        # Place digits and special characters at the start of early words to
        # avoid losing them when trimming to the requested length.
        words[0] = digit_block + words[0]
        words[1 % len(words)] = special_char + words[1 % len(words)]

        return words

    # Backward compatibility methods (called by Clinkey adapter)
    def normal(self) -> str:
        """Generate normal password (backward compatibility).

        Returns
        -------
        str
            Normal password.
        """
        return self._join_words(self._normal_words())

    def strong(self) -> str:
        """Generate strong password (backward compatibility).

        Returns
        -------
        str
            Strong password.
        """
        return self._join_words(self._strong_words())

    def super_strong(self) -> str:
        """Generate super strong password (backward compatibility).

        Returns
        -------
        str
            Super strong password.
        """
        return self._join_words(self._super_strong_words())
