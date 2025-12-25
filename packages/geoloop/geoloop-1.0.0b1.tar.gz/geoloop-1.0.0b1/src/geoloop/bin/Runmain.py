import sys
import time
from pathlib import Path

from geoloop.configuration import (
    LithologyConfig,
    SingleRunConfig,
    StochasticRunConfig,
    load_nested_config,
)
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity
from geoloop.utils.helpers import save_MCrun_results
from geoloop.utils.RunManager import run_models


def main_runmain(config_file_path: str | Path) -> None:
    """
    Run a **stochastic BHE analysis** and write results to disk.

    This function loads a combined configuration, optionally generates
    lithology-based thermal conductivity samples, executes stochastic BHE
    model runs, and stores output files.

    Parameters
    ----------
    config_file_path : str or Path
        The path to a JSON configuration file.

    Notes
    -----
    Expected JSON configuration fields (minimum):
        `variables_config`
            Defines parameter distributions for stochastic evaluation.

    Returns
    -------
    None
    """
    start_time = time.time()

    # Load configuration
    keysneeded = ["variables_config"]
    keysoptional = ["litho_k_param", "loadprofile", "borefield", "flow_data"]
    config_dict = load_nested_config(config_file_path, keysneeded, keysoptional)

    config = SingleRunConfig(**config_dict)
    # load configuration for variable parameters
    config.variables_config = StochasticRunConfig(**config.variables_config)

    # Optional lithology-based thermal conductivity sample generation
    config.lithology_to_k = None
    if config.litho_k_param:
        lithology_to_k = ProcessLithologyToThermalConductivity.from_config(
            LithologyConfig(**config.litho_k_param)
        )
        lithology_to_k.create_multi_thermcon_profiles()
        config.lithology_to_k = lithology_to_k

    # Model execution
    parameters, results = run_models(config)

    print("Saving results and visualizing...")

    # output directory setup
    if config.run_name:
        runfolder = config.run_name
    else:
        runfolder = Path(config_file_path).stem
        config.run_name = runfolder

    out_dir = (
        config.base_dir / runfolder
    )  # Check if the runfolder already exists, and create it if not
    out_dir.mkdir(parents=True, exist_ok=True)  # creates all missing directories

    basename = f"{runfolder}_{config.model_type[0]}_{config.run_type[0]}"
    outpath = out_dir / basename

    # Write results to disk
    save_MCrun_results(config, parameters, results, outpath)

    print(f"Total runtime: {(time.time() - start_time) / 60.0:.2f} minutes")


if __name__ == "__main__":
    main_runmain(sys.argv[1])
