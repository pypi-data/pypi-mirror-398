import sys
import time
from pathlib import Path

import pandas as pd

from geoloop.bin.SingleRunSim import SingleRun
from geoloop.configuration import (
    LithologyConfig,
    PlotInputConfig,
    SingleRunConfig,
    load_nested_config,
    load_single_config,
)
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity
from geoloop.plotting.create_plots import PlotResults
from geoloop.plotting.load_data import DataSelection, DataTotal, PlotInput


def main_plotmain(config_path: str | Path) -> None:
    """
    Main entry point for plotting BHE analysis.

    This function loads simulation parameters and results, organizes them into
    plot-ready data structures, and generates figures for multiple combinations
    of deterministic and Monte-Carlo simulation types. Supports plotting either:

    * Multiple **deterministic** (SR) runs, or
    * Multiple **stochastic** (MC) runs

    Mixed SR/MC plotting is not supported. Plotting more than two runs is possible
    but not optimally formatted.

    Parameters
    ----------
    config_path : str
        Path to a JSON configuration file.

    Returns
    -------
    None
    """

    start_time = time.time()

    config_dict = load_single_config(config_path)
    config = PlotInputConfig(**config_dict)  # validated Pydantic object

    print("Processing results and visualizing...")

    # Build data input object
    plotinput = PlotInput.from_config(config)
    plotinput.list_filenames()
    param_ds, results_ds = plotinput.load_params_result_data()

    temperature_field_da = None
    if plotinput.plot_temperature_field:
        temperature_field_da = plotinput.load_temperature_field_data()

    datatotal = DataTotal(results_ds, param_ds, temperature_field_da)
    dataselection = DataSelection.select_sub_datasets(plotinput, datatotal)

    # NEW individual run plotting
    if plotinput.newplot:
        for i in range(len(plotinput.run_names)):
            out_path = (
                plotinput.base_dir / plotinput.run_names[i] / plotinput.file_names[i]
            )

            # -------- Single Run (SR) --------
            if plotinput.run_modes[i] == "SR":
                if plotinput.plot_time_depth:
                    # Only create time and depth plots if the data is from a single run
                    PlotResults.create_timeseriesplot(
                        dataselection.timeplot_results_df[i],
                        out_path,
                        plotinput.plot_time_parameters,
                    )
                    PlotResults.create_depthplot(
                        plotinput.plot_depth_parameters,
                        plotinput.plot_times,
                        dataselection.depthplot_params_ds[i],
                        dataselection.depthplot_results_ds[i],
                        out_path,
                    )

                    if config.plot_borehole_temp:
                        run_name = plotinput.run_names[i]
                        runjson = run_name + ".json"
                        keysneeded = []
                        keysoptional = [
                            "litho_k_param",
                            "loadprofile",
                            "borefield",
                            "variables_config",
                            "flow_data",
                        ]
                        config_sim = load_nested_config(
                            runjson, keysneeded, keysoptional
                        )

                        run_config = SingleRunConfig(**config_sim)

                        run_config.lithology_to_k = None
                        if run_config.litho_k_param:
                            # in a single run always set the base case to True
                            run_config.litho_k_param["basecase"] = True
                            lithology_to_k = (
                                ProcessLithologyToThermalConductivity.from_config(
                                    LithologyConfig(**run_config.litho_k_param)
                                )
                            )
                            lithology_to_k.create_multi_thermcon_profiles()
                            run_config.lithology_to_k = lithology_to_k
                        single_run = SingleRun.from_config(run_config)
                        PlotResults.create_borehole_temp_plot(
                            plotinput.plot_borehole_temp,
                            plotinput.plot_times,
                            dataselection.depthplot_params_ds[i],
                            dataselection.depthplot_results_ds[i],
                            single_run,
                            out_path,
                        )

                # T-field movie & snapshots
                if plotinput.plot_temperature_field:
                    figure_folder = "Tfield_time"

                    out_path = plotinput.base_dir / plotinput.run_names[i]

                    # Create the figure folder if it doesn't exist
                    figure_folder_path = out_path / figure_folder
                    figure_folder_path.mkdir(parents=True, exist_ok=True)

                    # Full path for the file
                    out_path = figure_folder_path / plotinput.file_names[i]

                    Tmin = datatotal.temperature_field_da[i].values.min()
                    Tmax = datatotal.temperature_field_da[i].values.max()
                    for j in range(len(datatotal.temperature_field_da[i].time)):
                        PlotResults.plot_temperature_field(
                            j, datatotal.temperature_field_da[i], Tmin, Tmax, out_path
                        )
                    in_path = figure_folder_path
                    PlotResults.create_temperature_field_movie(in_path)

            # -------- Monte-Carlo (MC) --------
            elif plotinput.run_modes[i] == "MC":
                if plotinput.plot_crossplot_barplot:
                    # Only make scatter and bar plots is the simulation is a MC run
                    # Make plots for target parameter vs the other results and params
                    if plotinput.run_types[i] == "TIN":
                        target = "Q_b"
                    elif plotinput.run_types[i] == "POWER":
                        target = "T_fi"
                    else:
                        target = None
                        print("The run_type is not recognized")
                    plotinput.crossplot_vars.append(target)

                    for y_var_name in plotinput.crossplot_vars:
                        PlotResults.create_scatterplots(
                            dataselection.crossplot_results_df[i],
                            dataselection.crossplot_params_df[i],
                            y_var_name,
                            out_path,
                        )
                        PlotResults.create_barplot(
                            dataselection.crossplot_results_df[i],
                            dataselection.crossplot_params_df[i],
                            y_var_name,
                            out_path,
                        )

            else:
                print("Run_mode not recognized")
                pass

    # COMBINED multi-simulation plotting
    elif not plotinput.newplot:
        # below make sure that the figure name is shorter so that more than three simulations can be plotted together
        combined_fig_folder = "combined_plots"
        figure_name = "_".join([str(i) for i in plotinput.file_names])
        subfolder = figure_name

        # Build the full path
        combined_path = plotinput.base_dir / combined_fig_folder / subfolder

        # Create the folder if it doesn't exist
        combined_path.mkdir(parents=True, exist_ok=True)

        # Full output path for the figure
        out_path = combined_path / figure_name

        # Define runtype and create combined scatter and bar plots
        for run_type in plotinput.run_types:
            # Make plots for target parameter vs the other results and params
            if run_type == "TIN":
                target = "Q_b"
            elif run_type == "POWER":
                target = "T_fi"
            else:
                target = None
                print("The run_type is not recognized")
            plotinput.crossplot_vars.append(target)

        # Only create time and depth plots if the data is from a single run
        if (
            all(mode == "SR" for mode in plotinput.run_modes)
            and plotinput.plot_time_depth
        ):
            PlotResults.create_timeseriesplot(
                dataselection.timeplot_results_df,
                out_path,
                plotinput.plot_time_parameters,
            )
            PlotResults.create_depthplot(
                plotinput.plot_depth_parameters,
                plotinput.plot_times,
                dataselection.depthplot_params_ds,
                dataselection.depthplot_results_ds,
                out_path,
            )

        # Only make scatter and bar plots is the simulation is a MC run
        elif (
            all(mode == "MC" for mode in plotinput.run_modes)
            and plotinput.plot_crossplot_barplot
        ):
            # Combine dataframes for crossplots per run_name
            results_df = pd.concat(
                dataselection.crossplot_results_df, ignore_index=True
            )
            param_df = pd.concat(dataselection.crossplot_params_df, ignore_index=True)

            for y_var_name in plotinput.crossplot_vars:
                PlotResults.create_scatterplots(
                    results_df, param_df, y_var_name, out_path
                )
                PlotResults.create_barplot(results_df, param_df, y_var_name, out_path)

        else:
            print("Can not plot a single run and MC simulation together")

    # Runtime log
    print(f"Total runtime: {(time.time() - start_time) / 60.0:.2f} minutes")


if __name__ == "__main__":
    main_plotmain(sys.argv[1])
