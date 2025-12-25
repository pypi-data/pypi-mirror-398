from time import sleep

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from clinkey_cli.const import LOGO, LOGOS

console = Console()


def display_logo(fullscreen: bool = False):
    console.clear()
    console.print(
        Align.center(
            Panel.fit(
                Text(
                    r"""
   ___|  |     _ _|   \  |  |  /  ____| \ \   / 
  |      |       |     \ |  ' /   __|    \   /  
  |      |       |   |\  |  . \   |         |   
 \____| _____| ___| _| \_| _|\_\ _____|    _|   
                    """,
                    style="bold light_green",
                ),
                padding=(0, 1),
                box=box.ROUNDED,
                border_style="orchid1",
                subtitle="[dim white]v2.0.1[/]",
                subtitle_align="center",
            )
        )
    )
    

if __name__ == "__main__":
    display_logo()
