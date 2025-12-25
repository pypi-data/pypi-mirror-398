# AxeProfiler is a program designed to make saving/switching configurations for
# bitcoin miner devices simpler and more efficient.

# Copyright (C) 2025 [DC] Celshade <ggcelshade@gmail.com>

# This file is part of AxeProfiler.

# AxeProfiler is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# AxeProfiler is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# AxeProfiler. If not, see <https://www.gnu.org/licenses/>.

from os import name as os_name, system

from rich.panel import Panel
from rich.prompt import Confirm
from rich import print as rprint

from axeprofiler.cli import Cli


def show_notice() -> bool:
    notice = ''.join(
        ("[green]AxeProfiler Copyright (C) 2025 [DC] Celshade ",
        "<ggcelshade@gmail.com>[/]\n\n",
        "This program comes with ABSOLUTELY NO WARRANTY.\n",
        "This is free software, and you are welcome to redistribute it under ",
        "certain conditions. For more details, see:")
    )
    copying = "https://github.com/Celshade/AxeProfiler/blob/master/COPYING"

    system("cls" if os_name == "nt" else "clear")
    rprint(Panel(f"{notice}\n[bold magenta]{copying}[/].",
                    title="[bold bright_cyan]Copyright Notice",
                    width=80))
    return Confirm.ask("Do you want to start the program?", default='y')


def main() -> None:  # NOTE Program entry point
    # TODO add title screen?
    if show_notice():
        cli = Cli()
        cli.session()


if __name__ == "__main__":
    main()
