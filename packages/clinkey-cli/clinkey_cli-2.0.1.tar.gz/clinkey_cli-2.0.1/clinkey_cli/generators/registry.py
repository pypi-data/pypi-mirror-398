"""Generator registry for managing password generator types.

Provides central registry for discovering and instantiating different
password generator types dynamically.
"""

from typing import Type

from clinkey_cli.generators.base import BaseGenerator


class GeneratorRegistry:
    """Registry for password generator types.

    Manages registration and retrieval of generator classes,
    enabling dynamic generator discovery and plugin architecture.

    Examples
    --------
    >>> registry = GeneratorRegistry()
    >>> registry.register("test", SyllableGenerator)
    >>> gen_class = registry.get("test")
    """

    def __init__(self):
        """Initialize empty registry."""
        self._generators: dict[str, Type[BaseGenerator]] = {}

    def register(self, name: str, generator_class: Type[BaseGenerator]):
        """Register a generator class.

        Parameters
        ----------
        name : str
            Name to register generator under.
        generator_class : Type[BaseGenerator]
            Generator class to register.

        Examples
        --------
        >>> registry = GeneratorRegistry()
        >>> registry.register("syllable", SyllableGenerator)
        """
        self._generators[name] = generator_class

    def get(self, name: str) -> Type[BaseGenerator]:
        """Get generator class by name.

        Parameters
        ----------
        name : str
            Generator name.

        Returns
        -------
        Type[BaseGenerator]
            Generator class.

        Raises
        ------
        ValueError
            If generator name not found.

        Examples
        --------
        >>> registry = GeneratorRegistry()
        >>> registry.register("syllable", SyllableGenerator)
        >>> gen_class = registry.get("syllable")
        """
        if name not in self._generators:
            available = ", ".join(sorted(self._generators.keys()))
            raise ValueError(
                f"Unknown generator: '{name}'. "
                f"Available: {available if available else 'none'}"
            )
        return self._generators[name]

    def list_generators(self) -> list[str]:
        """List all registered generator names.

        Returns
        -------
        list[str]
            List of registered generator names.

        Examples
        --------
        >>> registry = GeneratorRegistry()
        >>> registry.register("syllable", SyllableGenerator)
        >>> registry.list_generators()
        ['syllable']
        """
        return list(self._generators.keys())


# Global default registry with pre-registered generators
registry = GeneratorRegistry()

# Import generators for registration
from clinkey_cli.generators.passphrase import PassphraseGenerator
from clinkey_cli.generators.pattern import PatternGenerator
from clinkey_cli.generators.syllable import SyllableGenerator

# Register syllable-based generators (backward compatible)
registry.register("normal", SyllableGenerator)
registry.register("strong", SyllableGenerator)
registry.register("super_strong", SyllableGenerator)

# Register new generator types
registry.register("passphrase", PassphraseGenerator)
registry.register("pattern", PatternGenerator)
