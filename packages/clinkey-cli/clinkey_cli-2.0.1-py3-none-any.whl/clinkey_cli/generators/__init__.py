"""Password generator implementations for Clinkey 2.0.

This module provides the base generator interface and concrete implementations
for different password generation strategies.
"""

from clinkey_cli.generators.base import BaseGenerator
from clinkey_cli.generators.passphrase import PassphraseGenerator
from clinkey_cli.generators.pattern import PatternGenerator
from clinkey_cli.generators.registry import GeneratorRegistry, registry
from clinkey_cli.generators.syllable import SyllableGenerator

__all__ = [
    "BaseGenerator",
    "SyllableGenerator",
    "PassphraseGenerator",
    "PatternGenerator",
    "GeneratorRegistry",
    "registry",
]
