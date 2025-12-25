"""Click-powered command line interface for the Clinkey password generator.

Supports both interactive and scripted launches, pairing Click for argument
parsing with Rich for terminal rendering.
"""

import pathlib
import time
from typing import Iterable, Optional

from clinkey_cli.settings import click
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt

from clinkey_cli.logos import display_logo
from clinkey_cli.const import centered_spinner
from clinkey_cli.main import Clinkey
from clinkey_cli.generators import registry
from clinkey_cli.generators.pattern import PatternGenerator

console = Console()


class ClinkeyView:
    """Render the interactive experience using Rich panels and prompts.

    Attributes
    ----------
    _logo_style : dict[str, str]
        Color palette applied to the ASCII art logo and panels.

    Methods
    -------
    display_logo()
        Show the full-screen welcome screen before collecting input.
    ask_for_type()
        Request the desired password profile from the user.
    ask_for_length()
        Request the target password length.
    ask_for_number()
        Request how many passwords should be generated.
    ask_for_options()
        Collect additional option toggles.
    ask_for_output_path()
        Ask where the results should be written.
    ask_for_separator()
        Request a custom separator to override the defaults.
    display_passwords(...)
        Render generated passwords in a styled table.
    """

    def __init__(self) -> None:
        self._logo_style = {
            "title_color": "bold light_green",
            "accent_color": "orchid1",
            "text_color": "grey100",
        }

    def _clear(self) -> None:
        """Clear the console before rendering the next view."""
        console.clear()

    def _logo_panel(self) -> Panel:
        """Build the Rich panel containing the Clinkey ASCII logo.

        Returns
        -------
        rich.panel.Panel
            Panel instance ready to be rendered by the console.
        """
        logo = Text(
            r"""
   ___|  |     _ _|   \  |  |  /  ____| \ \   / 
  |      |       |     \ |  ' /   __|    \   /  
  |      |       |   |\  |  . \   |         |   
 \____| _____| ___| _| \_| _|\_\ _____|    _|   
                                                
             """,
            style=self._logo_style["title_color"],
        )
        return Panel.fit(
            logo,
            padding=(0, 2),
            box=box.ROUNDED,
            border_style=self._logo_style["accent_color"],
        )

    def fullscreen_logo(self):
        display_logo(fullscreen=True)

    def simple_logo(self):
        display_logo()

    def display_logo(self) -> None:
        """Display the full-screen welcome screen and pause until the user confirms.

        The welcome screen fills the terminal with a large ASCII art logo,
        decorative elements, and branding. It is vertically centered based on
        the terminal height.
        """
        self._clear()
        # Get terminal height to create proper vertical centering
        terminal_height = console.size.height
        # Add some top padding for better vertical centering
        top_padding = max(0, (terminal_height // 2))
        console.print("\n" * top_padding)
        # Display the full-screen logo layout
        if terminal_height >= 50:
            self.fullscreen_logo()
        else:
            self.simple_logo()

        # Wait for user input (cursor will be at the end of the layout)
        input()

    def intro_logo(self) -> None:
        """Display the intro logo animation."""
        self._clear()
        display_logo()
        with Live(centered_spinner(), refresh_per_second=20, transient=True) as live:
            time.sleep(4)

    def ask_for_type(self) -> str:
        """Prompt the user for a password profile and return its slug.

        Returns
        -------
        str
            Password preset identifier (``"normal"``, ``"strong"``, or
            ``"super_strong"``); defaults to ``"normal"`` when the input
            is unrecognised.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "How [bold light_green]BOLD[/] do you want your password?\n",
                    style="white",
                )
            )
        )
        choices = Text.from_markup(
            "1 - [bold orchid1]Vanilla[/] (letters only)\n"
            "2 - [bold orchid1]Twisted[/] (letters and digits)\n"
            "3 - [bold orchid1]So NAAASTY[/] (letters, digits, symbols)\n"
            "4 - [bold orchid1]Corporate[/] (memorable word-based passphrase)\n"
            "5 - [bold orchid1]Custom[/] (pattern-based template)",
            style="white",
        )
        console.print(Align.center(choices))
        choice = Prompt.ask("Choose your [bold light_green]TRIBE[/]: > ", choices=["1", "2", "3", "4", "5"])
        return {
            "1": "normal",
            "2": "strong",
            "3": "super_strong",
            "4": "passphrase",
            "5": "pattern",
        }.get(choice, "normal")

    def ask_for_length(self) -> int:
        """Prompt for the target password length, falling back to ``16``.

        Returns
        -------
        int
            Positive length chosen by the user; returns ``16`` when the
            provided value is empty, invalid, or non-positive.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "How [bold light_green]LONG[/] do you like it ?",
                    style="white",
                )
            )
        )
        console.print(
            Align.center(
                Text.from_markup("(default: 16): ", style="bright_black")
            ),
            end="",
        )
        value = input().strip()
        try:
            length = int(value)
            return length if length > 0 else 16
        except ValueError:
            return 16

    def ask_for_number(self) -> int:
        """Prompt for the number of passwords to generate, defaulting to ``1``.

        Returns
        -------
        int
            Positive count requested by the user; returns ``1`` when the
            provided value is empty, invalid, or non-positive.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "How [bold light_green]MANY[/] you fancy at once ?",
                    style="white",
                )
            )
        )
        console.print(
            Align.center(
                Text.from_markup("(default: 1): ", style="bright_black")
            ),
            end="",
        )
        value = input().strip()
        try:
            count = int(value)
            return count if count > 0 else 1
        except ValueError:
            return 1

    def ask_for_word_count(self) -> int:
        """Prompt for word count in passphrase (3-10, default 4).

        Returns
        -------
        int
            Word count between 3 and 10; returns 4 if invalid input.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "How many [bold light_green]WORDS[/] do you want?",
                    style="white",
                )
            )
        )
        console.print(
            Align.center(
                Text.from_markup(
                    "(3-10, default: 4): ", style="bright_black"
                )
            ),
            end="",
        )
        value = input().strip()
        try:
            count = int(value)
            if 3 <= count <= 10:
                return count
            return 4
        except ValueError:
            return 4

    def ask_for_capitalize(self) -> bool:
        """Prompt whether to capitalize words in passphrase.

        Returns
        -------
        bool
            True to capitalize, False otherwise; defaults to True.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "[bold light_green]Capitalize[/] first letter of each word?",
                    style="white",
                )
            )
        )
        console.print(
            Align.center(
                Text.from_markup("(Y/n, default: Y): ", style="bright_black")
            ),
            end="",
        )
        value = input().strip().lower()
        return value != "n"

    def ask_for_pattern(self) -> str:
        """Prompt for pattern template with validation.

        Returns
        -------
        str
            Valid pattern template string.
        """
        gen = PatternGenerator()

        while True:
            self._clear()
            console.print(Align.center(self._logo_panel()))
            console.print(
                Align.center(
                    Text.from_markup(
                        "Enter your [bold light_green]PATTERN[/] template:",
                        style="white",
                    )
                )
            )
            console.print(
                Align.center(
                    Text.from_markup(
                        "Examples: Cvvc-9999, LLLL-DDDD, CVCVCV",
                        style="bright_black",
                    )
                )
            )
            console.print(
                Align.center(
                    Text.from_markup("Pattern: ", style="bright_black")
                ),
                end="",
            )
            pattern = input().strip()

            if pattern and gen.validate_pattern(pattern):
                return pattern

            console.print(
                Align.center(
                    Text.from_markup(
                        "[bold red]Invalid pattern! Try again.[/]",
                        style="white",
                    )
                )
            )
            time.sleep(1.5)

    def ask_for_options(self) -> list[str]:
        """Prompt for extra option keywords such as ``lower`` or ``no_sep``.

        Returns
        -------
        list[str]
            Tokens entered by the user separated by whitespace; returns an
            empty list when no extra options are provided.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "Any extra [bold light_green]OPTIONS[/]? (separate by spaces)",
                    style="white",
                )
            )
        )
        console.print(
            Align.center(
                Text.from_markup(
                    "Available: lower, no_sep", style="bright_black"
                )
            )
        )
        choices = input().strip()
        return choices.split() if choices else []

    def ask_for_output_path(self) -> Optional[str]:
        """Prompt for an output file path, returning ``None`` when skipped.

        Returns
        -------
        str | NoneUns§ fè
            Absolute or relative path entered by the user, or ``None`` if the
            prompt is left blank.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "Enter a file path to save the result (press ENTER to skip):",
                    style="white",
                )
            ),
            end="",
        )
        value = input().strip()
        return value or None

    def ask_for_separator(self) -> Optional[str]:
        """Prompt for a custom separator character, returning its first char.

        Returns
        -------
        str | None
            First character of the user input when provided; otherwise ``None``.
        """
        self._clear()
        console.print(Align.center(self._logo_panel()))
        console.print(
            Align.center(
                Text.from_markup(
                    "Custom [bold light_green]SEPARATOR[/]? (press ENTER to skip)",
                    style="white",
                )
            )
        )
        console.print(
            Align.center(
                Text.from_markup(
                    "Use exactly one non-space character.",
                    style="bright_black",
                )
            )
        )
        console.print(
            Align.center(Text.from_markup("Value: ", style="bright_black")),
            end="",
        )
        value = input().strip()
        if not value:
            return None
        return value[0]

    def display_passwords(self, passwords: Iterable[str], interactive: bool = False) -> None:
        """Render generated passwords in a Rich table for easy copying.

        Parameters
        ----------
        passwords : Iterable[str]
            Collection of passwords to render.
        """
        if interactive:
            self._clear()
            console.print(Align.center(self._logo_panel()))
            console.print(
                Align.center(
                    Panel.fit(
                        Align.center(
                            Text.from_markup(
                                (
                                    "Your Clinkey [bold light_green]PASSWORDS[/] "
                                    "are [bold light_green]READY[/]"
                                ),
                                style="white",
                            )
                        ),
                        padding=(0, 1),
                        box=box.ROUNDED,
                        border_style=self._logo_style["accent_color"],
                    )
                )
            )
        table = Table(
            show_header=False,
            box=box.ROUNDED,
            border_style=self._logo_style["accent_color"],
        )
        table.add_column(
            "password", style=self._logo_style["title_color"], justify="center"
        )
        for password in passwords:
            table.add_row(
                Text(password, style="bold light_green", justify="center")
            )
        console.print(Align.center(table))

        console.print(
            Align.center(
                Text.from_markup("Choose one to copy !", style="white"),
            )
        )


view = ClinkeyView()


def _parse_extra_options(options: Iterable[str]) -> dict[str, bool]:
    """Map option tokens collected interactively to CLI flag booleans.

    Parameters
    ----------
    options : Iterable[str]
        Raw tokens provided by the user.

    Returns
    -------
    dict[str, bool]
        Dictionary with ``lower`` and ``no_sep`` keys indicating whether each
        option has been requested. Unrecognised tokens are ignored.
    """
    lookup = {
        "lower": {"lower", "low", "-l", "--lower", "lw"},
        "no_sep": {"no_sep", "nosep", "-ns", "--no-sep", "no-sep", "ns"},
    }
    result = {"lower": False, "no_sep": False}
    for option in options:
        token = option.strip().lower()
        for key, aliases in lookup.items():
            if token in aliases:
                result[key] = True
    return result


def _write_passwords(path: pathlib.Path, passwords: Iterable[str]) -> None:
    """Persist generated passwords to the provided file path.

    Parameters
    ----------
    path : pathlib.Path
        Destination file that will receive the passwords.
    passwords : Iterable[str]
        Passwords to write, one per line. The iterable is consumed once.
    """
    with path.open("w", encoding="utf-8") as handle:
        for password in passwords:
            handle.write(f"{password}\n")


def _generate_passwords(
    type_: str,
    length: int,
    number: int,
    lower: bool,
    no_sep: bool,
    separator: Optional[str],
    word_count: int,
    capitalize: bool,
    pattern: Optional[str],
) -> list[str]:
    """Generate passwords using the appropriate generator from registry.

    Transformations (lowercase, separator removal/replacement) are handled
    by the generators themselves, not applied as post-processing.

    Parameters
    ----------

    type_ : str
        Generator type (normal, strong, super_strong, passphrase, pattern).

    length : int
        Password length (for syllable types).

    number : int
        Number of passwords to generate.

    lower : bool
        Convert to lowercase (passed to syllable generators).

    no_sep : bool
        Remove separators (passed to syllable generators).

    separator : str | None
        Custom separator character (passed to generators).

    word_count : int
        Number of words (passphrase only).

    capitalize : bool
        Capitalize words (passphrase only).

    pattern : str | None
        Pattern template (pattern only, required).

    Returns
    -------
    list[str]
        Generated passwords.

    Raises
    ------
    click.BadParameter
        If pattern type is used without pattern template.
    """
    # Get generator class from registry
    generator_class = registry.get(type_)
    generator = generator_class()

    # Build kwargs based on generator type
    if type_ == "passphrase":
        kwargs = {
            "word_count": word_count,
            "separator": separator or "-",
            "capitalize": capitalize,
        }
    elif type_ == "pattern":
        if not pattern:
            raise click.BadParameter(
                "Pattern template required for pattern type. "
                "Example: --pattern 'Cvvc-9999'",
                param_hint="--pattern",
            )
        kwargs = {"pattern": pattern}
    else:  # syllable types (normal, strong, super_strong)
        kwargs = {
            "length": length,
            "password_type": type_,
            "lower": lower,
            "no_separator": no_sep,
        }
        if separator:
            kwargs["separator"] = separator

    # Generate batch
    passwords = []
    for _ in range(number):
        password = generator.generate(**kwargs)
        passwords.append(password)

    return passwords


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-l",
    "--length",
    type=int,
    default=None,
    help="Password length (default: 16).",
)
@click.option(
    "-t",
    "--type",
    "type_",
    type=click.Choice(
        ["normal", "strong", "super_strong", "passphrase", "pattern"],
        case_sensitive=False
    ),
    default=None,
    help="Password type: normal, strong, super_strong, passphrase, or pattern.",
)
@click.option(
    "-n",
    "--number",
    type=int,
    default=None,
    help="Number of passwords to generate (default: 1).",
)
@click.option(
    "-ns",
    "--no-sep",
    "no_sep",
    is_flag=True,
    help="Remove separators from the result.",
)
@click.option(
    "-low",
    "--lower",
    is_flag=True,
    help="Convert generated passwords to lowercase.",
)
@click.option(
    "-s",
    "--separator",
    "new_separator",
    type=str,
    default=None,
    help="Use a custom separator character instead of '-' and '_'.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(
        dir_okay=False,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    default=None,
    help="Write the result to a file instead of displaying it.",
)
@click.option(
    "--word-count",
    type=click.IntRange(3, 10),
    default=4,
    help="Number of words in passphrase (passphrase type only).",
)
@click.option(
    "--capitalize/--no-capitalize",
    default=True,
    help="Capitalize first letter of each word (passphrase type only).",
)
@click.option(
    "--pattern",
    type=str,
    default=None,
    help="Pattern template for password generation (required for pattern type).",
)
def main(
    length: Optional[int],
    type_: Optional[str],
    number: Optional[int],
    no_sep: bool,
    lower: bool,
    new_separator: Optional[str],
    output: Optional[pathlib.Path],
    word_count: int,
    capitalize: bool,
    pattern: Optional[str],
) -> None:
    """Generate secure, pronounceable passwords from the command line.

    Parameters
    ----------
    length : int | None
        Desired password length. When ``None``, prompt the user interactively.
    type_ : str | None
        Password type to use. Supported values: ``"normal"``, ``"strong"``,
        ``"super_strong"``, ``"passphrase"``, ``"pattern"``. When ``None``,
        prompt the user interactively.
    number : int | None
        Number of passwords to output. Defaults to ``1`` if left ``None``.
    no_sep : bool
        Strip separator characters from each password when ``True``.
    lower : bool
        Convert generated passwords to lowercase when ``True``.
    new_separator : str | None
        Optional custom separator to apply to generated passwords.
    output : pathlib.Path | None
        Path where passwords should be saved. When ``None``, display them to
        stdout or via the interactive view.
    word_count : int
        Number of words for passphrase generation. Defaults to 4.
        Only applies when ``type_`` is ``"passphrase"``.
    capitalize : bool
        Whether to capitalize first letter of each word in passphrase.
        Defaults to ``True``. Only applies when ``type_`` is ``"passphrase"``.
    pattern : str | None
        Pattern template for pattern-based generation. Required when
        ``type_`` is ``"pattern"``. Example: ``"Cvvc-9999-Cvvc"``.

    Raises
    ------
    click.BadParameter
        If ``new_separator`` is provided but is not exactly one non-space
        character.
    """
    interactive = length is None and type_ is None and number is None

    if interactive:
        view.intro_logo()
        type_ = view.ask_for_type()

        if type_ in ["normal", "strong", "super_strong"]:
            # Existing syllable flow
            length = view.ask_for_length()
            number = view.ask_for_number()
            extra = _parse_extra_options(view.ask_for_options())
            lower = extra["lower"]
            no_sep = extra["no_sep"]
            chosen_sep = view.ask_for_separator()
            if chosen_sep:
                new_separator = chosen_sep
            chosen_output = view.ask_for_output_path()
            if chosen_output:
                output = pathlib.Path(chosen_output).expanduser().resolve()

        elif type_ == "passphrase":
            # Passphrase flow - initialize syllable-specific variables
            length = 16  # Not used for passphrase, but needed for _generate_passwords
            lower = False  # Passphrase handles its own casing
            no_sep = False  # Passphrase uses separators
            word_count = view.ask_for_word_count()
            chosen_sep = view.ask_for_separator()
            if chosen_sep:
                new_separator = chosen_sep
            capitalize = view.ask_for_capitalize()
            number = view.ask_for_number()
            chosen_output = view.ask_for_output_path()
            if chosen_output:
                output = pathlib.Path(chosen_output).expanduser().resolve()

        elif type_ == "pattern":
            # Pattern flow - initialize syllable-specific variables
            length = 16  # Not used for pattern, but needed for _generate_passwords
            lower = False  # Not used for pattern
            no_sep = False  # Not used for pattern
            pattern = view.ask_for_pattern()
            number = view.ask_for_number()
            chosen_output = view.ask_for_output_path()
            if chosen_output:
                output = pathlib.Path(chosen_output).expanduser().resolve()

    length = 16 if not length else length
    type_ = "normal" if not type_ else type_
    number = 1 if not number else number

    if new_separator:
        new_separator = new_separator.strip()
        if len(new_separator) != 1 or new_separator.isspace():
            raise click.BadParameter(
                "Separator must be exactly one non-space character.",
                param_hint="--separator",
            )

    passwords = _generate_passwords(
        type_=type_,
        length=length,
        number=number,
        lower=lower,
        no_sep=no_sep,
        separator=new_separator,
        word_count=word_count,
        capitalize=capitalize,
        pattern=pattern,
    )

    if output:
        _write_passwords(output, passwords)
        click.echo(f"Passwords saved to {output}")
    else:
        view.display_passwords(passwords, interactive=interactive)


if __name__ == "__main__":  # pragma: no cover
    main()
