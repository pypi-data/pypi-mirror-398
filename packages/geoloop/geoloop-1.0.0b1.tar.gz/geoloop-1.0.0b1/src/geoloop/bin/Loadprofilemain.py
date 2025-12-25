from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from geoloop.configuration import LoadProfileConfig, load_single_config
from geoloop.loadflowdata.loadprofile import LoadProfile


def main_load_profile(config_path: str | Path):
    """
    Command-line entry point to calculate, plot and optionally save a time-profile of heat load.

    Parameters
    ----------
    config_path : str or Path
        The path to a JSON configuration file.

    Notes
    -----
    The function:
      • loads a configuration file
      • builds a LoadProfile instance
      • computes 1 year of hourly load data
      • plots instantaneous and cumulative energy
      • writes the plot to the configured output directory
    """
    # Parse the configuration file and combine with standard configuration
    config_dict = load_single_config(config_path)
    config = LoadProfileConfig(**config_dict)  # validated Pydantic object

    loadprof = LoadProfile.from_config(config)

    # Simulation parameters
    dt = 3600.0  # Time step (s)
    tmax = 1.0 * 8760.0 * 3600.0  # Maximum time (s)
    Nt = int(np.ceil(tmax / dt))  # Number of time steps
    time = dt * np.arange(1, Nt + 1)

    # Load function expects hours
    Q = loadprof.getload(time / 3600)

    # plot results
    fig, (ax1, ax2) = plt.subplots(2, figsize=(9, 9))

    # Instantaneous load
    ax1.set_xlabel(r"$t$ [hours]")
    ax1.set_ylabel(r"$Q_b$ [W]")
    hours = np.arange(1, Nt + 1) * dt / 3600.0
    ax1.plot(hours, Q)

    # Cumulative energy
    ax2.set_xlabel(r"$t$ [hours]")
    ax2.set_ylabel(r"$Q_b$ [MWh]")

    # Combined cumulative (heating + cooling)
    Qcum_all = np.cumsum(Q) * (dt / 3600) * 1e-6
    ax2.plot(hours, Qcum_all, label="Cumulative heating + cooling load")

    # Heating only
    Q_heating = Q * 1
    Q_heating[Q_heating <= 0] = 0
    Qcum_heating = np.cumsum(Q_heating) * (dt / 3600) * 1e-6
    ax2.plot(hours, Qcum_heating, label="Cumulative heating load")

    # Cooling only
    Q_cooling = Q * 1
    Q_cooling[Q_cooling > 0] = 0
    Qcum_cooling = np.cumsum(Q_cooling) * (dt / 3600) * 1e-6
    ax2.plot(hours, Qcum_cooling, label="Cumulative cooling load")

    plt.legend()
    plt.tight_layout()

    # Save figure
    plot_dir = config.lp_outdir
    if config.lp_type == "FROMFILE":
        if config.lp_smoothing is not None:
            fig_name = f"{config.lp_filename[:-4]}_{config.lp_smoothing}_smoothing"
        else:
            fig_name = config.lp_filename[:-3]
    else:
        fig_name = f"{config.lp_type}_load_profile"

    fig_path = plot_dir / fig_name
    plt.savefig(fig_path)

    # Print results summary
    print(
        "total energy consumed [MWh]:", np.sum(Q) * 1e-6
    )  # total net energy demand in one year
    print(
        "total energy heating [MWh]:", np.sum(Q[Q > 0]) * 1e-6
    )  # total heating demand in one year
    print(
        "total energy cooling [MWh]:", np.sum(Q[Q <= 0]) * 1e-6
    )  # total cooling demand in one year
    print(
        "yearly average energy consumed [W]:", np.mean(Q)
    )  # yearly average energy consumed
