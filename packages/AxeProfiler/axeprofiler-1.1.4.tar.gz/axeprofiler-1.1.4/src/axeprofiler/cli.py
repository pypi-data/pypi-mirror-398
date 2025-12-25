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

import json
from time import sleep
from time import sleep
from typing import TypeAlias
from os import system, path, listdir, remove, name as os_name

from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt, Confirm
from requests.exceptions import ConnectionError

from axeprofiler.profiles import Profile
from axeprofiler.utils import validate_config, validate_profile_dir


CONFIG: TypeAlias = dict[str, str | int]  # config obj format
DEFAULTS = {  # BitAxe and NerdQAxe model defaults
    "Supra": {"frequency": 490, "core_voltage": 1166, "fanspeed": 90},
    "Gamma": {"frequency": 525, "core_voltage": 1150, "fanspeed": 90},
    "NerdQ++": {"frequency": 600, "core_voltage": 1150, "fanspeed": 90},
    "NerdQX": {"frequency": 777, "core_voltage": 1200, "fanspeed": 90}
}


class Cli(Console):
    """
    Command-line interface for managing AxeProfiler device profiles.

    Inherits from Rich's Console to provide enhanced terminal output and user
    interaction. Handles profile creation, listing, updating, deletion, and
    application to devices. Provides a session loop for interactive use and]
    utilities for rendering menus and defaults.

    Methods:
        main_menu: Display the main menu with available options.
        list_profiles: List all existing profiles with pagination.
        create_profile: Create and save a profile for the given configuration.
        update_profile: Update the configuration of an existing profile.
        run_profile: Apply the selected profile to a device.
        delete_profile: Delete the specified profile.
        show_profile: Display the details of the selected profile.
        session: Start the CLI session loop.
    """
    def __init__(self) -> None:
        super().__init__()  # Inherit Console() ability to render/color
        self.__root: str  = __file__.split("src")[0]  # program root
        # self.__config: str  = f"{self.__root}.config"  # program config
        self.__profile_dir: str = None  # local profile dir
        self._profile: Profile = None  # Currently selected Profile

        with Progress() as progress:  # Start progress bar
            # Validate config file
            config_task = progress.add_task("[blue]Validating config files...")
            progress.update(config_task, advance=25)
            config = validate_config(root_path=self.__root,
                                     config_path=f"{self.__root}.config")
            progress.update(config_task, advance=75)


            # Validate profile_dir
            profile_task = progress.add_task("[blue]Validating profiles...")
            progress.update(profile_task, advance=30)
            self.__profile_dir = validate_profile_dir(
                config=config,
                root_path=self.__root,
                profile_dir=config.get("profile_dir")
            )
            progress.update(profile_task, advance=70)

        self.print("[blue]Starting program...")
        sleep(0.5)  # Pause render before clearing

    def __repr__(self):
        return f"Cli()"

    def __str__(self) -> str:
        return json.dumps(
            {
                "num_profiles": len(listdir(self.__profile_dir)),
                "active_profile": self._profile.name if self._profile else None
            }, indent=4)

    @property
    def profile_dir(self) -> str:
        """
        Return the path where profiles are saved locally - set in `.config`. The
        default will be set to the `{program_root}/.profiles/`
        """
        return self.__profile_dir

    @property
    def num_profiles(self) -> int:
        """
        Return the number of existing profiles found.
        """
        return len(listdir(self.profile_dir))

    @property
    def profile(self) -> Profile:
        """
        Return the active `Profile()` obj.
        """
        return self._profile

    @profile.setter
    def profile(self, profile: Profile) -> None:
        """
        Set an active `Profile()`.

        Args:
            profile: The `Profile()` obj to set as active."""
        self._profile = profile if isinstance(profile, Profile) else None

    def main_menu(self) -> None:
        """
        Display the main menu with available options.

        Renders the main menu using a Rich Table, showing all available actions
        and their descriptions. The menu adapts based on whether a profile is
        currently selected.
        """
        system("cls" if os_name == "nt" else "clear")

        # Create the main menu as a table
        menu = Table("Option", "Description",
                     title="[green]Enter one of the following options",
                     width=76)

        # Add a row for each menu option
        menu.add_row(f"[bold green]L[/] ({self.num_profiles} found)",
                     "List all of the available Profiles")
        menu.add_row("[bold green]N", "Create a new Profile")
        # Toggle selection indicators
        if self.profile:
            menu.add_row("[bold green]U", "Update the selected Profile")
            menu.add_row("[bold green]R", "Run the selected Profile")
            menu.add_row("[bold green]D", "Delete an existing Profile")

            name = Text(self.profile.name)
            name.truncate(max_width=15, overflow="ellipsis")
            menu.add_row(f"[bold magenta]S [white]({name})",
                         "Show selected Profile")
        else:
            menu.add_row("[grey]U", "Update the selected Profile")
            menu.add_row("[grey]R", "Run the selected Profile")
            menu.add_row("[grey]D", "Delete an existing Profile")
            menu.add_row("[grey]S", "Show selected Profile")
        menu.add_row(
            "[bold cyan]M[/] (default)", "Show this menu again")
        menu.add_row("[bold red]Q", "Quit the program")

        # Render the main menu
        self.print(Panel(menu, title="[bold bright_cyan]Main Menu", width=80))

    def _load_profile(self, profile_name: str) -> Profile:
        """
        Load an existing profile.

        Args:
            profile_name: The name of the profile to load.

        Returns:
            A `Profile` obj containing axe config data.

        Raises:
            FileNotFoundError: if no file is found for the given name.
        """
        try:
            with open(f"{self.profile_dir}{profile_name}", 'r') as f:
                return Profile.create_profile(json.loads(f.read()))

        except FileNotFoundError:
            self.print(f"[red]Could not find a profile named: {profile_name} ⚠")
        except Exception as e:
            print(e)

    def _get_page_count(self, num_profiles: int, num_rendered: int) -> str:
        """
        Return a str display of x-y profile count for the current page being
        listed by `list_profiles()`. i.e. 1-4, 5-8, etc

        Args:
            num_profiles: The number of profiles.
            num_rendered: The number of profiles rendered so far.
        """
        if num_profiles >=4:
            if num_rendered == 0:
                return "1-4"
            else:
                return f"{num_rendered + 1}-{num_rendered + 4}"
        elif num_rendered == 0:
                return f"0-0" if num_profiles == 0 else f"1-{num_profiles}"
        else:
            return f"{num_rendered + 1}-{num_rendered + num_profiles}"

    def _drop_profile_name(self, profile: Profile) -> dict[str, str | int]:
        """
        Return profile data with the `profile_name` removed from the `dict`.

        Used for rendering Profile's as Rich Tables when the name is the title.

        Args:
            Profile: The Profile in use.
        """
        # Remove profile name from render table since it's in title
        profile_data = profile.data
        profile_data.pop("profile_name")
        return profile_data

    def _build_profile_list_view(self, choices: list[str],
                                 profiles: list[str]) -> dict[str, Table]:
        tables = {}

        for num, _profile in zip(choices, profiles):
            profile: Profile = self._load_profile(_profile)
            # Truncate text to match profile window size with room for options
            title = Text(profile.name)
            title.truncate(max_width=32, overflow="ellipsis")
            # Create and add to table dict
            table = Table(title=f"[green][{num}] [bold magenta]{title}",
                          width=37, show_header=False)
            table.add_row(json.dumps(self._drop_profile_name(profile),
                                     indent=4))
            tables[num] = {
                "profile": profile,
                "table": table
            }
        # self.print(tables)  # Testing
        return tables

    def list_profiles(self, profiles: list[str] | None = None,
                      num_rendered: int = 0, first_page: bool = False) -> None:
        """
        List all existing profiles.

        Args:
            profiles: An array of profile names (default=None).
            num_rendered: The number of profiles rendered so far (default=0).
            first_page: Toggle Rule() on first page load (default=False).
        """
        # TODO next iteration, add filters/search
        # Operational text
        if first_page:
            self.print(Rule("[bold cyan]Listing Profiles"), width=80)
        else:
            self.print("[blue]Loading profiles...⏳")

        # Get current screen totals based on what's passed in and render count
        profiles = profiles or listdir(self.profile_dir)
        num_profiles = len(profiles)
        current = self._get_page_count(num_profiles, num_rendered)
        _min, _max = [int(i) for i in current.split('-')]
        choices = [*map(str, list(range(_min, _max + 1)))]  # current page

        # Create base message prompt and render existing profiles
        if self.num_profiles == 0:
            msg = "No Profiles. Enter [red][Q][/] to quit to [cyan]Main Menu[/]"
        else:
            msg = '\n'.join((
                "Enter a [green]number[/] to select the corresponding profile.",
                "Enter [red][Q][/] to quit to [cyan]Main Menu[/]"
            ))

            # Turn each Profile() into a renderable Table()
            # NOTE: max 2x2 (4) per page (width=37)
            tables = self._build_profile_list_view(choices, profiles[:4])

            # Render the profiles
            # NOTE We create rows by taking advantage of the display's wrapping;
            # else create Group() of Panel() of Columns()
            self.print(Panel(
                    Columns((tables[data]["table"] for data in tables)),
                    title=f"[bold cyan]Profiles ({current}/{self.num_profiles})",
                    width=80))

        # Establish sub menu options
        choices = [*map(str, list(range(1, self.num_profiles + 1))), 'Q']
        default = 'Q'
        if num_profiles > 4:  # Add pagination prompt
            msg += " or [green][P][/] to see more profiles"
            choices.insert(-1, 'P')  # Add `page` option
            default = 'P'

        # Manually display choices to include elipses w/o breaking selection
        if self.num_profiles > 1:
            msg += f" [bold magenta][1...{self.num_profiles}]"

        user_choice = Prompt.ask(msg, choices=choices, default=default,
                                 case_sensitive=False,
                                 show_choices=False).lower()

        # Use recursion to paginate as needed (4 per page)
        if user_choice == 'p':
            return self.list_profiles(profiles=profiles[4:],
                                      num_rendered=num_rendered + 4)
        # Set the selected profile and return to main menu
        elif user_choice != 'q':
            if user_choice in tables:
                self.profile = tables[user_choice]["profile"]
            else:
                self.profile = self._load_profile(
                    listdir(self.profile_dir)[int(user_choice) - 1]
                )

    def _validate_int_prompt(self, prompt: str,
                             default: int, flag: str) -> int | bool:
        """
        Validate integer prompts while allowing for a string flag to interrupt.

        Prompts the user for an integer value, with support for a special flag
        to cancel the process. Recursively re-prompts on invalid input.

        Args:
            prompt: The user prompt.
            default: The default value if users enters nothing.
            flag: The escape flag to interrupt the Profile creation process.

        Returns:
            Returns an `int` if the user doesn't pass the `flag` else `False`
        """
        try:
            assert isinstance(default, int)  # Ensure to avoid recursion issues

            # Get user propmt and check for the escape flag
            # NOTE: str(default) is required to render here for some reason
            # NOTE: Rich will auto convert int values returned from ask()
            user_choice = Prompt.ask(prompt, default=str(default))
            if isinstance(user_choice, str) and user_choice.lower() == flag:
                return False

            # int() handles the default oddity mentioned above
            return int(user_choice)

        except ValueError:
            self.print("[red]Please enter a valid integer number")
            # NOTE: must include the return here, lest you like recursion bugs
            return self._validate_int_prompt(prompt, default, flag)
        except AssertionError:
            self.print("[red]arg: `default` value is not of type int")
            return False

    def _get_profile_config(self, retain_name: str = None) -> CONFIG:
        """
        Prompt the user for profile configuration values.

        Guides the user through entering configuration values for a new or
        updated profile. Optionally retains the profile name if provided.

        Args:
            retain_name: The profile name to retain (default=None).

        Returns:
            A dictionary containing the profile configuration values.
        """
        self.print("[italic]Enter [red][!!][/] at any time to cancel\n")
        FLAG = "!!"  # escape hatch

        # Get profile values
        profile_name = Prompt.ask("Enter a [green]profile name[/]:",
                                    default=retain_name or "Default")
        assert profile_name != FLAG  # escape hatch
        hostname = Prompt.ask("Enter [green]hostname[/] (Optional):",
                                default="Unknown")
        assert hostname != FLAG
        frequency = self._validate_int_prompt("Enter [green]frequency[/]",
                                                default=550, flag=FLAG)
        assert frequency and isinstance(frequency, int)  # escape hatch
        c_voltage = self._validate_int_prompt("Enter [green]coreVoltage[/]",
                                                default=1150, flag=FLAG)
        assert c_voltage and isinstance(c_voltage, int)
        fanspeed = self._validate_int_prompt("Enter [green]fanspeed[/]",
                                                default=100, flag=FLAG)
        assert fanspeed and isinstance(fanspeed, int)

        return {"profile_name": profile_name, "hostname": hostname,
                "frequency": frequency, "coreVoltage": c_voltage,
                "fanspeed": fanspeed}

    def _render_defaults(self) -> None:
        """
        Display the default configuration values for all supported models.

        Renders a Rich table showing the default frequency, core voltage, and
        fan speed for each supported miner model.
        """
        # Render defaults for supra, gamma, nerd++
        default_tables = []
        for model in DEFAULTS:
            default_tables.append(
                Table(json.dumps(DEFAULTS[model], indent=4),
                        title=f"[bold magenta]{model}", width=37)
            )
        self.print(Panel(Columns(default_tables),
                                    title="[bold cyan]Defaults", width=80))

    def create_profile(self) -> Profile | None:
        """
        Create and save a profile for the given configuration.

        Guides the user through the process of creating a new profile, with
        validation and the ability to cancel at any step. Displays model
        defaults and confirms before saving.

        Returns:
            A `Profile` obj containing axe config data else `None` if the user
            cancels mid process.
        """
        self.print(Rule("[bold cyan]Creating Profile"), width=80)
        try:
            self._render_defaults()
            # Prompt user and create a new Profile()
            profile = Profile.create_profile(self._get_profile_config())
        except AssertionError:  # _get_profile_config() will raise to escape
            self.print("[blue]Canceling profile creation...⏳")
            return

        try:
            # Render created profile
            new_profile = Table(profile.__str__(),
                                title=f"[bold magenta]{profile.name}", width=50)
            print()
            self.print(new_profile)
            # Confirm before saving else create another profile
            user_choice = Confirm.ask("[bold green]Create[/] this profile?")
            if not user_choice:
                return self.create_profile()

            profile.save_profile(profile_dir=self.profile_dir)
            assert path.exists(f"{self.profile_dir}{profile.name}.json")

            self.print(f"\n[bold]Profile [blue]{profile.name}[/] created! 🍞")
            sleep(1)
            return profile
        except AssertionError:
            self.print("[red]Error[/] verifying [magenta]profile[/] was saved")

    def update_profile(self, profile: Profile) -> None:
        """
        Update the configuration of an existing profile.

        Prompts the user to modify the configuration values of the selected
        profile. Saves the updated profile if changes are confirmed.

        Args:
            profile: The profile to update.
        """
        self.print(Rule("[bold cyan]Updating Profile"), width=80)
        try:
            if not profile:
                raise ValueError

            # Render the selected profile
            self.print(Table(
                self.profile.__str__(),
                title=f"[bold magenta]{self.profile.name}[/] (current)",
                width=50)
            )

            # Create a new profile to override selected with
            new_profile = Profile.create_profile(
                self._get_profile_config(retain_name=profile.name)
            )

        except ValueError:
            self.print("No Profile is currently [green]selected")
            sleep(0.25)
            return
        except AssertionError:  # _get_profile_config() will raise to escape
            self.print("[blue]Canceling profile creation...⏳")
            sleep(0.25)
            return

        try:
            # Render current config vs selected profile # TODO breakout
            print()
            selected = Table(profile.__str__(),
                             title=f"[bold magenta]{profile.name}", width=37)
            updated = Table(new_profile.__str__(),
                           title=f"[bold magenta]{new_profile.name}", width=37)
            self.print(Columns([selected, "[bold green]->", updated]))

            # Confirm before saving else re-rerun the update process
            user_choice = Confirm.ask("[bold green]Update[/] this profile?")
            if not user_choice:
                return self.update_profile(self.profile)

            # Set and save the updated profile
            self.profile = new_profile
            if self.profile.name != profile.name:
                self.profile.save_profile(profile_dir=self.profile_dir,
                                          replace=profile.name)
            else:
                self.profile.save_profile(profile_dir=self.profile_dir)
            assert path.exists(f"{self.profile_dir}{self.profile.name}.json")

            self.print(
                f"\n[bold]Profile [blue]{self.profile.name}[/] updated! 👍")
            sleep(1)
        except AssertionError:
            self.print("[red]Error[/] verifying [magenta]profile[/] was saved")

    def run_profile(self, profile: Profile) -> None:
        """
        Apply the selected profile to a device.

        Prompts the user for a device IP address, displays the current and
        selected configurations, and applies the profile if confirmed.

        Args:
            profile: The profile to apply.

        Raises:
            AssertionError: If no profile is currently selected.
            ConnectionError: If IP cannot be reached or is not AxeOS compliant.
        """
        self.print(Rule("[bold cyan]Running Profile"), width=80)
        try:
            assert profile

            # Get IP
            ip = Prompt.ask("Enter target [green]IP address[/] or "
                            + "[Q] to quit to [cyan]Main Menu",
                            case_sensitive=False,
                            default=['Q'])
            if not ip or isinstance(ip, (int, float)) or len(ip) < 4:
                # shortest(?) IP format being abc.d
                self.print(
                    "[blue]Invalid IP address. Returning to main menu...⏳")
                sleep(0.25)
                return

            # Render current config vs selected profile
            print()
            active_config = Profile.create_profile_from_active(ip)
            active = Table(active_config.__str__(),
                           title="[bold magenta]Active", width=37)
            selected = Table(profile.__str__(),
                             title=f"[bold magenta]{profile.name}", width=37)
            self.print(Columns([active, "[bold green]->", selected]))

            # Confirm before appplying
            user_choice = Confirm.ask(
                f"Apply [bold magenta]{profile.name}[/] to {ip}?",
                case_sensitive=False,
                default=False)
            if user_choice:
                self.print(f"[blue]Applying {profile.name} to device...⏳")
                self.profile.run_profile(ip)
                self.print("Success! 🥳")
                sleep(0.5)
            else:
                self.print("[blue]Returning to main menu...⏳")
            sleep(0.25)

        except ConnectionError:
            self.print(f"[red]Error[/] connecting to [green]{ip}[/]."
                       + " Check device/IP.\n[blue]Returning to main menu...⏳")
            sleep(1)
        except AssertionError:
            self.print("No Profile is currently [green]selected")
            sleep(0.25)

    def show_profile(self, profile: Profile = None,
                     rule: str = None,
                     message: str | None = None,
                     choices: list[str] | None = None,
                     show_choices: bool | None = True,
                     show_default: bool | None = True,
                     default: bool | None = False,
                     prompt: bool | None = False) -> bool | None:
        """
        Display the details of the selected profile.

        Renders the profile's configuration in a Rich table and returns `True`
        or `False` depending on the user's response to any `message` passed in.

        Args:
            profile: The profile to display.
            rule: A Rich rule (line separator) (default=None).
            message: The message confirmation prompt (default=None).
            choices: A list of available choices (default=None).
            show_choices: Flag to render choices (default=True).
            show_default: Flag to render default (default=True).
            default: The default response to fall back on (default=False).
            prompt: Flag to render a Rich `prompt` | `confirm` (default=False).

        Returns:
            Returns nothing and just displays the `profile` if no message is
        Raises:
            ValueError: If no profile is currently selected.
        """
        if rule:  # Insert line separator
            self.print(Rule(rule), width=80)
        try:
            assert profile

            # Render active profile
            table = Table(title=f"[bold magenta]{profile.name}",
                          width=50, show_header=False)
            table.add_row(json.dumps(self._drop_profile_name(profile),
                                     indent=4))
            self.print(table)

            if choices:
                METHOD = Prompt if prompt else Confirm
                return METHOD.ask(
                    message,
                    choices=choices, show_choices=show_choices,
                    show_default=show_default, default=default,
                    case_sensitive=False
                )

        except AssertionError:
            self.print("No Profile is currently [green]selected")
            sleep(0.25)
            return

    def delete_profile(self, profile: Profile) -> None:
        """
        Delete the specified profile.

        Prompts the user for confirmation before deleting the profile file from
        disk and clearing the current selection.

        Args:
            profile: The profile to delete.

        Raises:
            ValueError: If no profile is currently selected.
            FileNotFoundError: If the profile file does not exist.
        """
        try:
            # Render the selected profile
            user_choice: bool = self.show_profile(
                profile,
                rule="[bold cyan]Deleting Profile",
                # Warning message
                message=f"This will [bold red]delete[/] profile: "
                       + f"[magenta]{profile.name if profile else 'Error'}"
                       + "\n[bold red]Do you wish to continue?",
                choices=['y', 'n'],
            )
            if user_choice:
                # Delete the config file
                remove(f"{self.profile_dir}{profile.name}.json")
                self.profile = None
                self.print(f"[blue]{profile.name} has been deleted")
                sleep(0.5)
            self.print("[blue]Returning to main menu...⏳")

        except FileNotFoundError:
            self.print(f"Error finding profile: [magenta]{profile.name} 🤔")
        except Exception as e:
            print(e)

    def session(self) -> None:
        """
        Start the CLI session loop.

        Handles user input for navigating the main menu and performing actions
        such as listing, creating, updating, running, deleting, and showing
        profiles. Recursively calls itself to maintain the session until the
        user quits.
        """
        # Handle user choice
        self.main_menu()
        user_choice = Prompt.ask(
            "Enter an option ([italics]not case sensitive[/]):",
            choices=['L', 'N', 'U', 'R', 'D', 'S', 'M', 'Q'],
            default='M',
            case_sensitive=False
        )

        # Run session loop via recursion
        match user_choice.lower():
            case 'l':
                # List existing Profiles
                self.print(f"[green][{user_choice}][/] >>> Listing profiles")
                self.list_profiles(first_page=True)
                self.session()
            case 'n':
                # Create a new Profile
                self.print(f"[green][{user_choice}][/] >>> Creating profile")
                self.profile = self.create_profile() or self.profile
                sleep(0.5)
                self.session()
            case 'u':
                # Update selected Profile
                self.print(f"[green][{user_choice}][/] >>> Updating profile")
                self.update_profile(self.profile)
                sleep(0.5)
                self.session()
            case 'r':
                # Run selected Profile
                # # TODO apply to multiple devices
                self.print(f"[green][{user_choice}][/] >>> Running profile")
                self.run_profile(self.profile)
                sleep(0.5)
                self.session()
            case 'd':
                # Delete selected Profile
                self.print(f"[green][{user_choice}][/] >>> Deleting profile")
                self.delete_profile(self.profile)
                sleep(0.5)
                self.session()
            case 's':
                # Show selected Profile
                self.print(f"[green][{user_choice}][/] >>> Showing profile")
                self.show_profile(
                    profile=self.profile,
                    rule="[bold cyan]Selected Profile",
                    message="Press [green][Enter][/] to continue",
                    choices=["Enter", 'Q'], show_choices=False,
                    show_default=False, default="Enter",
                    prompt=True
                )
                self.print("[blue]Returning to main menu...⏳")
                sleep(0.5)
                self.session()
            case 'm':
                # Show the main menu
                self.print(
                    f"[bright_cyan][{user_choice}][/] >>> Returning to menu")
                sleep(0.3)
                self.session()
            case 'q':
                # Quit the program
                self.print(f"[red][{user_choice}][/] >>> Session Terminated")
                return


if __name__ == "__main__":  # bypass notice if run from here
    cli = Cli()
    cli.session()
