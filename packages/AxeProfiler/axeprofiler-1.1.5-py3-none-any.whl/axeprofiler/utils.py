import json
from os import mkdir, path

from rich import print as rprint


def validate_config(root_path: str, config_path: str) -> dict[str, str]:
    # Check for existing config or create one
    if not path.exists(config_path):
        with open(config_path, 'w') as f:
            config = {"profile_dir": f"{root_path}.profiles/"}
            f.write(json.dumps(config, indent=4))
    else:  # Read existing config
        with open(config_path, 'r') as f:
            config = json.loads(f.read())

    return config


def validate_profile_dir(config: dict[str, str], root_path: str,
                         profile_dir: str) -> str:
    if not profile_dir:  # Add default profile_dir to config
        with open(f"{root_path}.config", 'w') as f:
            config["profile_dir"] = f"{root_path}.profiles/"
            f.write(json.dumps(config, indent=4))

        # Make and set default profile_dir
        _profile_dir = config["profile_dir"]
        if not path.exists(_profile_dir):
            mkdir(_profile_dir)
    else:  # Validate existing profile dir
        try:
            assert isinstance(profile_dir, str)
            # Ensure existing profile_dir
            if not path.exists(profile_dir):
                mkdir(profile_dir)

            _profile_dir = profile_dir
        except AssertionError:
            msg = "[red]Invalid profile directory configuration"
            rprint(msg)
            raise AssertionError("**Program terminated**")  # Exit program
    return _profile_dir
