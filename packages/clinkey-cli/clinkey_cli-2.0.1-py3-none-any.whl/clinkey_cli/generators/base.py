"""Base generator abstract class for all password generators.

Defines the common interface that all password generators must implement,
along with shared utility methods for password transformation.
"""

from abc import ABC, abstractmethod


class BaseGenerator(ABC):
    """Abstract base class for all password generators.

    All password generators must inherit from this class and implement
    the `generate` method. This ensures a consistent API across all
    generator types.

    Methods
    -------
    generate(length: int, **kwargs) -> str
        Generate a password of specified length with optional parameters.
    fit_to_length(password: str, target_length: int) -> str
        Fit password to exact target length by truncating or padding.
    transform(password: str, lower: bool, no_separator: bool, separator: str | None) -> str
        Apply transformations to generated password.
    """

    @abstractmethod
    def generate(self, length: int, **kwargs) -> str:
        """Generate a password of specified length.

        Parameters
        ----------
        length : int
            Target length for the generated password.
        **kwargs : dict
            Additional generator-specific parameters.

        Returns
        -------
        str
            Generated password matching requested length.

        Raises
        ------
        ValueError
            If length is invalid or parameters are incompatible.
        """
        pass

    def fit_to_length(self, password: str, target_length: int) -> str:
        """Fit password to exact target length.

        Parameters
        ----------
        password : str
            Password to fit to target length.
        target_length : int
            Desired final length.

        Returns
        -------
        str
            Password adjusted to exact target length.
        """
        if len(password) == target_length:
            return password
        elif len(password) > target_length:
            return password[:target_length]
        else:
            # Repeat password until we reach target length
            repetitions = (target_length // len(password)) + 1
            return (password * repetitions)[:target_length]

    def transform(
        self,
        password: str,
        lower: bool = False,
        no_separator: bool = False,
        separator: str | None = None,
    ) -> str:
        """Apply transformations to password.

        Parameters
        ----------
        password : str
            Password to transform.
        lower : bool, default False
            Convert password to lowercase.
        no_separator : bool, default False
            Remove separator characters.
        separator : str | None, default None
            If provided, replace default separators with this character.

        Returns
        -------
        str
            Transformed password.
        """
        result = password

        # Apply separator transformations first
        if no_separator:
            # Remove common separators
            result = result.replace("-", "").replace("_", "")
        elif separator is not None:
            # Replace separators with custom character
            result = result.replace("-", separator).replace("_", separator)

        # Apply case transformation
        if lower:
            result = result.lower()

        return result
