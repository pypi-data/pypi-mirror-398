import typer

from geoloop.bin.Flowdatamain import main_flow_data
from geoloop.bin.Lithologymain import main_lithology
from geoloop.bin.Loadprofilemain import main_load_profile
from geoloop.bin.Plotmain import main_plotmain
from geoloop.bin.Runbatch import run_batch_from_json
from geoloop.bin.Runmain import main_runmain
from geoloop.bin.SingleRunSim import main_single_run_sim
from geoloop.cli.batch import batch_app

# Set up the main app
simulation = typer.Typer(help="Geoloop simulation CLI.")
simulation.add_typer(batch_app, name="batch")


@simulation.command(name="batch-run")
def batch_run(
    config_file_path: str = typer.Argument(
        ...,
        help="Path to the Json file with a sequence of the command scripts and configuration arguments",
    ),
) -> None:
    """
    Run a batch of scripts, in sequence, for BHE simulation.
    """
    run_batch_from_json(config_file_path)


@simulation.command(name="single-run")
def single_run(
    config_file_path: str = typer.Argument(
        ..., help="Path to the Json file with the main model configuration parameters"
    ),
) -> None:
    """
    Run main script for a single BHE simulation.
    """
    main_single_run_sim(config_file_path)


@simulation.command(name="stochastic-run")
def stochastic_run(
    config_file_path: str = typer.Argument(
        ..., help="Path to the Json file with the main model configuration parameters"
    ),
) -> None:
    """
    Run main script for a stochastic BHE simulation.
    """
    main_runmain(config_file_path)


@simulation.command(name="process-lithology")
def process_lithology(
    config_file_path: str = typer.Argument(
        ...,
        help="Path to the Json file with the subsurface model configuration parameters",
    ),
) -> None:
    """
    Run main script for calculating and plotting subsurface thermal properties.
    """
    main_lithology(config_file_path)


@simulation.command(name="calculate-loadprofile")
def calculate_loadprofile(
    config_file_path: str = typer.Argument(
        ...,
        help="Path to the Json file with the subsurface model configuration parameters",
    ),
) -> None:
    """
    Run main script for calculating a time-profile of heat load.
    """
    main_load_profile(config_file_path)


@simulation.command(name="calculate-flowdata")
def calculate_flowdata(
    config_file_path: str = typer.Argument(
        ..., help="Path to the Json file with the flow data configuration parameters"
    ),
) -> None:
    """
    Run main script for calculating a time-profile of flow rate.
    """
    main_flow_data(config_file_path)


@simulation.command(name="plot")
def plot_results(
    config_file_path: str = typer.Argument(
        ..., help="Path to the Json file with the plotting configuration parameters"
    ),
) -> None:
    """
    Run main script for plotting the simulation results.
    """
    main_plotmain(config_file_path)


if __name__ == "__main__":
    simulation()
