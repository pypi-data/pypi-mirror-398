import json
import sys
from pathlib import Path

from geoloop.bin.Flowdatamain import main_flow_data
from geoloop.bin.Lithologymain import main_lithology
from geoloop.bin.Loadprofilemain import main_load_profile
from geoloop.bin.Plotmain import main_plotmain
from geoloop.bin.Runmain import main_runmain
from geoloop.bin.SingleRunSim import main_single_run_sim

command_dict = {
    "SingleRunSim": main_single_run_sim,
    "Runmain": main_runmain,
    "Plotmain": main_plotmain,
    "Loadprofile": main_load_profile,
    "Lithology": main_lithology,
    "FlowData": main_flow_data,
}


def run_batch_from_json(config_file: str) -> None:
    """
    Execute internal registered command functions defined in a JSON batch file.

    Parameters
    ----------
    config_file : str
        Path to a JSON file specifying commands to be executed.

    Notes
    -----
    Expected JSON format::

        {
            "commands": [
                {"command": "Plotmain", "args": ["config.json"]},
                ...
            ]
        }

    Raises
    ------
    ValueError
        If an unknown command is encountered.

    Returns
    -------
    None
    """
    with open(config_file) as file:
        config_path = Path(config_file).resolve()
        base_dir = config_path.parent  # directory of the batch file

        config = json.load(file)

    for command_spec in config["commands"]:
        command = command_spec["command"]
        args_json = Path(command_spec.get("args", []))

        if args_json.is_absolute():
            command_config_path = args_json
        else:
            command_config_path = base_dir / args_json

        if command in command_dict:
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            print("Running command", command)
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            command_dict[command](command_config_path)
        else:
            raise ValueError(f"Command {command} not recognized")


def main(args):
    config_file = args[0]
    run_batch_from_json(config_file)


if __name__ == "__main__":
    main(sys.argv[1:])
