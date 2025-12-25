import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from geoloop.configuration import FlowDataConfig, load_single_config
from geoloop.loadflowdata.flow_data import FlowData


def main_flow_data(config_path: str | Path):
    """
    Command-line entry point to calculate, plot and optionally save a time-profile of flow rate.

    Parameters
    ----------
    config_path : str or Path
        Path to a JSON config file.

    Notes
    -----
    This function:
      • Loads a FlowData configuration file
      • Builds a FlowData instance
      • Computes 1 year of hourly flow data
      • Plots instantaneous and cumulative flow
      • Saves the plot in the configured output directory
    """

    # 1. Load configuration
    config_dict = load_single_config(config_path)
    config = FlowDataConfig(**config_dict)

    flow = FlowData.from_config(config)

    # 2. Simulation time setup (1 hour step)
    dt = 3600.0  # seconds
    tmax = 8760.0 * 3600  # one year in seconds
    Nt = int(np.ceil(tmax / dt))

    time = dt * np.arange(1, Nt + 1)
    hours = time / 3600

    # Compute flow data
    Q_flow = flow.getflow(hours)

    # 3. Plotting
    fig, (ax1, ax2) = plt.subplots(2, figsize=(9, 9))

    # Instantaneous flow
    ax1.set_xlabel(r"$t$ [hours]")
    ax1.set_ylabel(r"$\dot{m}$ [kg/s]")
    ax1.plot(hours, Q_flow)
    ax1.set_title("Instantaneous Flow Rate")

    # Cumulative flow (kg)
    Qcum = np.cumsum(Q_flow) * dt  # dt is seconds → sum(kg/s * s) = kg
    ax2.set_xlabel(r"$t$ [hours]")
    ax2.set_ylabel(r"Cumulative flow [kg]")
    ax2.plot(hours, Qcum)
    ax2.set_title("Cumulative Flow")

    plt.tight_layout()

    # 4. Save figure
    plot_dir = Path(config.fp_outdir)

    if config.fp_type == "FROMFILE":
        if config.fp_smoothing is not None:
            fig_name = f"{config.fp_filename[:-4]}_{config.fp_smoothing}_flow"
        else:
            fig_name = f"{config.fp_filename[:-4]}_flow"
    else:
        fig_name = f"{config.fp_type}_flow_profile"

    fig_path = plot_dir / fig_name
    plt.savefig(fig_path)

    # 5. Print summary
    print("Flow profile summary:")
    print("---------------------")
    print("Mean flow rate [kg/s]:", np.mean(Q_flow))
    print("Min flow rate  [kg/s]:", np.min(Q_flow))
    print("Max flow rate  [kg/s]:", np.max(Q_flow))
    print("Total cumulative flow [kg]:", Qcum[-1])


if __name__ == "__main__":
    main_flow_data(sys.argv[1])
