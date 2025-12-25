import re
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pygfunction as gt
import seaborn as sns
import xarray as xr
from PIL import Image

from geoloop.bin.SingleRunSim import SingleRun
from geoloop.constants import format_dict, units_dict
from geoloop.geoloopcore.strat_interpolator import StratInterpolator
from geoloop.utils.helpers import get_param_names


class PlotResults:
    """
    A class with functions for generating plots of simulation results. Different plots can be created for different
    types of simulations and models (e.g. single simulations, stochastic simulation, FINVOL model, ANALYTICAL model).

    """

    @staticmethod
    def create_scatterplots(
        results_df: pd.DataFrame,
        params_df: pd.DataFrame,
        y_variable: str,
        out_path: Path,
    ) -> None:
        """
        Only compatible with results and inputs of stochastic (MC) simulations.
        Generates and saves scatter plots for all parameters in the simulations results, with `y_variable` on the y-axis.
        The parameters in the list of 'y_variable' are plotted against all other parameters in the results and input
        dataframes.

        Parameters
        ----------
        results_df : pd.DataFrame
            DataFrame containing simulation result parameters as columns.
        params_df : pd.DataFrame
            DataFrame containing simulation input parameters as columns.
        y_variable : str
            The variable parameter to be plotted on the y-axis.
        out_path : Path
            Path to the directory where the plots will be saved.

        Raises
        ------
        ValueError
            If `y_variable` is not found in either `results_df` or `param_df`.

        Returns
        -------
        None
        """
        if y_variable in results_df.columns:
            y_data = results_df
        elif y_variable in params_df.columns:
            y_data = params_df
        else:
            raise ValueError(
                f"{y_variable} not found in either results_df or param_df."
            )

        # Get the list of all variables excluding the y_variable
        result_variables = [
            "Q_b",
            "flowrate",
            "T_fi",
            "T_fo",
            "T_bave",
            "dploop",
            "qloop",
            "T_b",
            "qzb",
            "T_f",
            "Re_in",
            "Re_out",
            "k_s_res",
            "k_g_res",
        ]
        variable_param_names, locked_param_names = get_param_names()

        x_variables = result_variables + variable_param_names

        # Loop through variables and create scatterplots
        for x_variable in x_variables:
            if x_variable != y_variable and x_variable in results_df.columns:
                # only plot the variables that are truly variable (stdev != 0)
                if results_df[x_variable].std().round(7) != 0:
                    title = f"{format_dict[x_variable]} ({units_dict[x_variable]}) after {results_df.loc[0, 'hours']} hours production vs. {format_dict[y_variable]} ({units_dict[y_variable]})"
                    g = sns.JointGrid(
                        results_df, x=x_variable, y=y_data[y_variable], hue="file_name"
                    )
                    g.plot_joint(
                        sns.scatterplot, alpha=0.7, edgecolor=".2", linewidth=0.5
                    )
                    g.plot_marginals(
                        sns.boxplot,
                        linewidth=0.5,
                        linecolor=".2",
                        boxprops=dict(alpha=0.9),
                    )
                    sns.set_style("whitegrid")
                    g.ax_joint.legend(bbox_to_anchor=(0.63, -0.15))

                    # Reverse y-axis if y_variable is "H"
                    if y_variable == "H":
                        g.ax_joint.invert_yaxis()

                    # Plot vertical line with turbulent Re value if x_variable is either 'Re_in' or 'Re_out'
                    if x_variable in ["Re_in", "Re_out"]:
                        g.ax_joint.axvline(
                            4000, color="red", linestyle="--", label="Re turbulent"
                        )
                        g.ax_joint.legend()  # Ensure the legend is updated
                    g.set_axis_labels(
                        xlabel=f"{format_dict[x_variable]} ({units_dict[x_variable]})",
                        ylabel=f"{format_dict[y_variable]} ({units_dict[y_variable]})",
                    )
                    g.fig.suptitle(title)
                    g.fig.tight_layout()
                    save_path = out_path.with_name(
                        out_path.name + f"_{y_variable}vs{x_variable}_scat.png"
                    )
                    plt.savefig(save_path)
                    plt.close()

            elif (
                x_variable != y_variable
                and x_variable
                in params_df.select_dtypes(include=["float64", "int64"]).columns
            ):
                if params_df[x_variable].std().round(7) != 0:
                    title = f"{format_dict[x_variable]} ({units_dict[x_variable]}) after {params_df.loc[0, 'nyear']} year production vs. {format_dict[y_variable]} ({units_dict[y_variable]})"
                    g = sns.JointGrid(
                        params_df, x=x_variable, y=y_data[y_variable], hue="file_name"
                    )
                    g.plot_joint(
                        sns.scatterplot, alpha=0.7, edgecolor=".2", linewidth=0.5
                    )
                    g.plot_marginals(
                        sns.boxplot,
                        linewidth=0.5,
                        linecolor=".2",
                        boxprops=dict(alpha=0.9),
                    )
                    sns.set_style("whitegrid")
                    g.ax_joint.legend(bbox_to_anchor=(0.63, -0.15))

                    # Reverse y-axis if y_variable is "H"
                    if y_variable == "H":
                        g.ax_joint.invert_yaxis()

                    g.set_axis_labels(
                        xlabel=f"{format_dict[x_variable]} ({units_dict[x_variable]})",
                        ylabel=f"{format_dict[y_variable]} ({units_dict[y_variable]})",
                    )
                    g.fig.suptitle(title)
                    g.fig.tight_layout()
                    save_path = out_path.with_name(
                        out_path.name + f"_{y_variable}vs{x_variable}_scat.png"
                    )
                    plt.savefig(save_path)
                    plt.close()

    @staticmethod
    def create_timeseriesplot(
        results_dfs: pd.DataFrame | list[pd.DataFrame],
        out_path: Path,
        plot_parameters: list,
    ):
        """
        Only compatible with (multiple) single simulations.
        Generates and saves a timeseries plot for various simulation results over time. Results of multiple
        single simulations can be plotted together.

        Plot shows the generated power, flowrate, fluid inlet en outlet temperatures, depth-average borehole wall temperature,
        pumping pressure and required pumping power over time.

        Parameters
        ----------
        results_dfs : Union[pd.DataFrame, List[pd.DataFrame]]
            DataFrame(s) containing simulation results.
        out_path : Path
            Directory where plots are saved.
        plot_parameters : List[str]
            List of variables to plot.

        Raises
        ------
        ValueError
            If any required parameter is missing from a DataFrame in `results_dfs`.

        Returns
        -------
        None
        """
        out_path_prefix = out_path.with_name(out_path.name + "timeplot")

        # Ensure results_dfs is a list of dataframes
        if isinstance(results_dfs, pd.DataFrame):
            results_dfs = [results_dfs]

        figsize = (11, 4)
        plt.rcParams.update({"font.size": 12})

        # Define labels for each parameter
        labels = {}
        for idx, df in enumerate(results_dfs):
            file_name = df["file_name"].iloc[0]
            labels[idx] = {
                "T_fi": f"{file_name}, $T_{{in}}$ [°C]",
                "T_fo": f"{file_name}, $T_{{out}}$ [°C]",
                "T_bave": f"{file_name}, $T_{{b,ave}}$ [°C]",
                "Delta_T": f"{file_name}, Δ Temperature (Tout - Tin)",
                "Q_b": f"{file_name}, Heat Load [W]",
                "dploop": f"{file_name}, Pump Pressure [bar]",
                "qloop": f"{file_name}, Pump Power [W]",
                "flowrate": f"{file_name}, Flowrate [kg/s]",
                "COP": f"{file_name}, Coefficient of Performance",
            }

        # Create a global color palette for consistency across dataframes
        line_colors = sns.color_palette(
            "colorblind", n_colors=len(results_dfs) * len(plot_parameters) * 3
        )
        color_iter = iter(line_colors)

        # Check if any dataframe needs COP or Delta_T calculated
        for df in results_dfs:
            if (
                "COP" in plot_parameters
                and "Q_b" in df.columns
                and "qloop" in df.columns
            ):
                mean_Q = df["Q_b"].mean()
                mean_q = df["qloop"].mean()
                mean_COP = mean_Q / mean_q
                df["COP"] = mean_COP  # abs(df['Q_b'] / df['qloop'])
                # df['COP'] = abs(df['Q_b']) / df['qloop']
                # print(df["COP"].min())
            if (
                "Delta_T" in plot_parameters
                and "T_fi" in df.columns
                and "T_fo" in df.columns
            ):
                df["Delta_T"] = df["T_fo"] - df["T_fi"]

        plots = [
            ("Q_b", "Heat Load [W]", "Q_b", None, None),
            ("flowrate", "Flowrate [kg/s]", "flowrate", None, None),
            ("COP", "Coefficient of Performance", "COP", None, None),
        ]

        plotted_params = []
        extra_artists = []
        # Plot dploop and qloop, even if only one is present
        if "dploop" in plot_parameters or "qloop" in plot_parameters:
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_xlabel(r"$t$ [hours]")
            primary_axis_used = False

            if "dploop" in plot_parameters:
                ax.set_ylabel("Pump Pressure [bar]")
                for idx, df in enumerate(results_dfs):
                    if "dploop" in df.columns:
                        sns.lineplot(
                            x="time",
                            y="dploop",
                            data=df,
                            ax=ax,
                            label=labels[idx]["dploop"],
                            color=next(color_iter),
                        )
                        primary_axis_used = True
                        plotted_params.append("dploop")

                ax.legend(loc=(-0.07, -0.35))

            ax_twin = ax.twinx()
            ax_twin.set_ylabel("Pump Power [W]")

            for idx, df in enumerate(results_dfs):
                if "qloop" in plot_parameters and "qloop" in df.columns:
                    color = next(color_iter)

                    # Plot the line
                    sns.lineplot(
                        x="time",
                        y="qloop",
                        data=df,
                        ax=ax_twin,
                        label=labels[idx]["qloop"],
                        linestyle="dotted",
                        color=color,
                    )

                    # Match axis color to line color
                    ax_twin.spines["right"].set_color(color)
                    ax_twin.yaxis.label.set_color(color)
                    ax_twin.tick_params(axis="y", colors=color)

                    plotted_params.append("qploop")
                    ax_twin.legend(loc=(0.53, -0.15 - (len(results_dfs) * 0.1)))
                    extra_artists.append(ax_twin.legend_)
                if primary_axis_used:
                    ax.legend(loc=(-0.07, -0.15 - (len(results_dfs) * 0.1)))
                    extra_artists.append(ax.legend_)

            ax.grid()
            if not primary_axis_used:
                ax.set_yticklabels([])
                ax.set_ylabel("")
                ax.grid(False, axis="y")
                ax_twin.grid(axis="both")

            file_name = out_path.with_name(
                out_path.name + f"timeplot_{'_'.join(sorted(set(plotted_params)))}.png"
            )

            fig.tight_layout()
            plt.savefig(
                file_name,
                dpi=300,
                bbox_extra_artists=(extra_artists),
                bbox_inches="tight",
            )
            plt.close()

        # Plot T_fi, T_fo, T_bave together, and Delta_T on the secondary axis if applicable
        plotted_params = []
        extra_artists = []
        if (
            any(param in plot_parameters for param in ["T_fi", "T_fo", "T_bave"])
            or "Delta_T" in plot_parameters
        ):
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_xlabel(r"$t$ [hours]")
            primary_axis_used = False

            if any(param in plot_parameters for param in ["T_fi", "T_fo", "T_bave"]):
                ax.set_ylabel("Temperature [°C]")
                for idx, df in enumerate(results_dfs):
                    if "T_fi" in plot_parameters and "T_fi" in df.columns:
                        sns.lineplot(
                            x="time",
                            y="T_fi",
                            data=df,
                            ax=ax,
                            label=labels[idx]["T_fi"],
                            color=next(color_iter),
                            linestyle="-",
                        )
                        primary_axis_used = True
                        plotted_params.append("T_fi")
                    if "T_fo" in plot_parameters and "T_fo" in df.columns:
                        sns.lineplot(
                            x="time",
                            y="T_fo",
                            data=df,
                            ax=ax,
                            label=labels[idx]["T_fo"],
                            color=next(color_iter),
                            linestyle="--",
                        )
                        primary_axis_used = True
                        plotted_params.append("T_fo")
                    if "T_bave" in plot_parameters and "T_bave" in df.columns:
                        sns.lineplot(
                            x="time",
                            y="T_bave",
                            data=df,
                            ax=ax,
                            label=labels[idx]["T_bave"],
                            color=next(color_iter),
                            linestyle=":",
                        )
                        primary_axis_used = True
                        plotted_params.append("T_bave")
                    ax.legend(
                        loc="lower left",
                        bbox_to_anchor=(
                            0.04,
                            0.02
                            - (0.05 * 1.25 * len(plotted_params) / len(results_dfs)),
                        ),
                        bbox_transform=fig.transFigure,
                    )
                    extra_artists.append(ax.legend_)

            if "Delta_T" in plot_parameters:
                color = next(color_iter)

                ax_twin = ax.twinx()
                ax_twin.set_ylabel("Δ Temperature (Tout - Tin)")
                for idx, df in enumerate(results_dfs):
                    sns.lineplot(
                        x="time",
                        y="Delta_T",
                        data=df,
                        ax=ax_twin,
                        label=labels[idx]["Delta_T"],
                        linestyle="dashdot",
                        color=color,
                    )
                    plotted_params.append("Delta_T")

                # Match axis color to line color
                ax_twin.spines["right"].set_color(color)
                ax_twin.yaxis.label.set_color(color)
                ax_twin.tick_params(axis="y", colors=color)

                ax_twin.legend(
                    loc="lower right",
                    bbox_to_anchor=(1.1, -0.25 - (0.08 * len(results_dfs))),
                )
                extra_artists.append(ax_twin.legend_)
                if primary_axis_used:
                    ax.legend(
                        loc="lower left",
                        bbox_to_anchor=(
                            0.03,
                            0.1 - (0.02 * len(plotted_params) / len(results_dfs)),
                        ),
                        bbox_transform=fig.transFigure,
                    )
                    extra_artists.append(ax.legend_)

            ax.grid()

            if not primary_axis_used:
                ax.set_yticklabels([])
                ax.set_ylabel("")
                ax.grid(False, axis="y")
                ax_twin.grid(axis="both")

            file_name = out_path.with_name(
                out_path.name
                + "timeplot_"
                + "_".join(sorted(set(plotted_params)))
                + ".png"
            )

            fig.tight_layout()
            plt.savefig(
                file_name,
                dpi=300,
                bbox_extra_artists=(extra_artists),
                bbox_inches="tight",
            )
            plt.close()

        # Plot remaining parameters
        for param, ylabel, filename, secondary_param, secondary_ylabel in plots:
            if param not in plot_parameters:
                continue

            fig, ax = plt.subplots(figsize=figsize)
            ax.set_xlabel(r"$t$ [hours]")
            ax.set_ylabel(ylabel)

            for idx, df in enumerate(results_dfs):
                if param in df.columns:
                    sns.lineplot(
                        x="time",
                        y=param,
                        data=df,
                        ax=ax,
                        label=labels[idx][param],
                        color=next(color_iter),
                    )

            ax.legend(loc=(-0.07, -0.17 - (0.08 * len(results_dfs))))
            ax.grid()
            fig.tight_layout()
            plt.savefig(f"{out_path_prefix}_{filename}.png", dpi=300)
            plt.close()

    @staticmethod
    def create_depthplot(
        plot_parameters: list,
        times: list,
        params_ds: xr.Dataset | list[xr.Dataset],
        results_ds: xr.Dataset | list[xr.Dataset],
        out_path: Path,
    ):
        """
        Only compatible with (multiple) single simulations.
        Generates and saves depth-profiles at different timesteps in the simulation results, for fluid temperatures,
        borehole wall temperature, subsurface temperature, subsurface heat flow and subsurface bulk thermal conductivity.

        Parameters
        ----------
        plot_parameters : List[str]
            List of parameters to plot.
        times : List[float]
            Simulation timesteps for which profiles are plotted.
        params_ds : Union[xr.Dataset, List[xr.Dataset]]
            Dataset(s) containing simulation input parameters.
        results_ds : Union[xr.Dataset, List[xr.Dataset]]
            Dataset(s) containing simulation results.
        out_path : Path
            Directory to save plots.

        Raises
        ------
        ValueError
            If any required parameter is missing from a DataFrame in `results_ds` or `params_ds`.

        Returns
        -------
        None
        """
        method = "nearest"
        ax_colors = sns.color_palette("pastel", n_colors=10)
        axtwin_colors = sns.color_palette("dark", n_colors=10)
        plt.rcParams.update(
            {"font.size": 16, "xtick.labelsize": 16, "ytick.labelsize": 16}
        )

        if not isinstance(params_ds, list):
            params_ds = [params_ds]
            results_ds = [results_ds]

        for time in times:
            fig1, ax1 = plt.subplots(
                figsize=(8, 10)
            )  # First plot: Temperature profiles
            fig2, ax2 = plt.subplots(
                figsize=(8, 10)
            )  # Second plot: Heat flow & conductivity
            ax2twin = ax2.twiny()

            ax1.set_xlabel("Temperature [°C]")
            ax1.set_ylabel("Depth from borehole head [m]")
            ax1.grid()

            ax2.set_xlabel("Heat flow [W/m]")
            ax2.set_ylabel("Depth from borehole head [m]")
            ax2.grid()
            ax2twin.set_xlabel("Thermal conductivity [W/mK]")

            color_iter_ax2 = iter(ax_colors)
            color_iter_ax2twin = iter(axtwin_colors)

            for param, results in zip(params_ds, results_ds):
                file_name = str(
                    param["file_name"]
                    .isel(nPipes=0, layer_k_s=0, layer_k_g=0, layer_Tg=0)
                    .item()
                )

                ptemp = results["T_f"].sel(time=time, method=method)
                Tb = results["T_b"].sel(time=time, method=method)
                Tg = results.get("Tg", None)
                qzb = results["qzb"].sel(time=time, method=method)
                k_s = results["k_s"].values
                zp = -results["z"]
                zseg = -results["zseg"]

                # Check if the parameter is in the list before plotting
                if plot_parameters == False:
                    plot_parameters = ["T_f", "Tg", "T_b"]
                else:
                    plot_parameters = plot_parameters

                model_type = param["model_type"].item()
                if "T_f" in plot_parameters:
                    for i in range(len(ptemp[0])):
                        ax1.plot(
                            ptemp[:, i], zp, label=f"{file_name}: Fluid temp Pipe {i}"
                        )
                        deltaT = ptemp[:, -1] - ptemp[:, 0]
                if "Delta_T" in plot_parameters:
                    ax1twin = ax1.twiny()
                    (deltaT_line,) = ax1twin.plot(deltaT, zp, label="Delta T")

                    # Get the color of the Delta T line
                    deltaT_color = deltaT_line.get_color()

                    # Set axis label and tick color to match the line
                    ax1twin.set_xlabel(
                        "Temperature diff. outlet-inlet [\u00b0C]", color=deltaT_color
                    )
                    ax1twin.tick_params(axis="x", colors=deltaT_color)
                    ax1twin.spines["top"].set_color(
                        deltaT_color
                    )  # For the twiny axis, 'top' is used

                if "T_b" in plot_parameters and len(Tb) == len(zseg):
                    if model_type in ["ANALYTICAL", "FINVOL"]:
                        ax1.plot(Tb, zseg, "k--", label=f"{file_name}: $T_b$")
                    elif model_type in ["PYG", "PYGFIELD"]:
                        Tb_plot = Tb * np.ones(len(zp))
                        ax1.plot(Tb_plot, zp, "k--", label=f"{file_name}: $T_b$")

                if "Tg" in plot_parameters and Tg is not None and len(Tg) == len(zseg):
                    if model_type in ["ANALYTICAL", "FINVOL"]:
                        ax1.plot(
                            Tg, zseg, ":", label=f"{file_name}: $T_g$", color="red"
                        )
                    elif model_type in ["PYG", "PYGFIELD"]:
                        Tg_plot = Tg * np.ones(len(zp))
                        ax1.plot(
                            Tg_plot, zp, ":", label=f"{file_name}: $T_g$", color="red"
                        )

                dz = zp[1] - zp[0]
                if model_type in ["ANALYTICAL"]:
                    qbzm = qzb / dz
                    ax2.plot(
                        qbzm,
                        zseg,
                        label=f"{file_name}: Heat Flow",
                        color=next(color_iter_ax2),
                    )
                elif model_type in ["FINVOL"]:
                    qbzm = qzb / dz
                    qbzm[0] *= 2
                    qbzm[-1] *= 2
                    ax2.plot(
                        -qbzm,
                        zp,
                        label=f"{file_name}: Heat Flow",
                        color=next(color_iter_ax2),
                    )
                elif model_type in ["PYG", "PYGFIELD"]:
                    # only single value for Tb, Qb etc, do not plot heat flow
                    qbzm = qzb
                    q_plot = qbzm * np.ones(len(zp))
                    # because of UBWT condition the heat flow is not linear
                    # ax2.plot(q_plot, zp, label=f'{file_name}: Heat Flow', color=next(color_iter_ax2))
                else:
                    print(f"Unrecognized model type: {model_type}")

                # zseg is depth of mid point of segments
                zseg = results.zseg.values
                zval = k_s

                if param["model_type"] == "PYG" or param["model_type"] == "PYGTILTED":
                    zp_plot = np.array([zseg[0], zseg[-1]])
                    k_s_plot = k_s * np.ones(2)
                else:
                    interp_obj = StratInterpolator(zseg, zval)

                    zz = np.linspace(
                        int(param.D),
                        int(param.D) + int(param.H),
                        int(param.nsegments) + 1,
                    )

                    zp = interp_obj.zp
                    # Interpolate basecase thermal conductivity values
                    k_s_interpolated = interp_obj.interp_plot(zz[0:-1], zz[1:])

                    # select interpolated depth values for which the thermal conductivities are
                    zp_plot = zp[(zp >= zz[0])]
                    start_index_zp_plot = np.where(zp >= zz[0])[0][0]
                    k_s_plot = k_s_interpolated[start_index_zp_plot:]

                # Plot thermal conductivity on ax2twin
                if (
                    (param["model_type"].item() == "ANALYTICAL")
                    or (param["model_type"].item() == "PYG")
                    or (param["model_type"].item() == "PYGFIELD")
                    or (param["model_type"].item() == "FINVOL")
                ):
                    ax2twin.plot(
                        k_s_plot,
                        -zp_plot,
                        label=f"{file_name}: Thermal conductivity",
                        color=next(color_iter_ax2twin),
                    )

            legend1 = ax1.legend(bbox_to_anchor=(1, 1))
            # combine the legends from the second plot primary and secondary axis
            handles2, labels2 = ax2.get_legend_handles_labels()
            handles3, labels3 = ax2twin.get_legend_handles_labels()
            all_handles = handles2 + handles3
            all_labels = labels2 + labels3
            # Create a single combined legend and define legend location
            if len(params_ds) > 1:
                legend_loc = ((1.8 - (len(params_ds) * 0.4)), 1)
            else:
                legend_loc = (1.9, 1)
            combined_legend = ax2.legend(
                all_handles, all_labels, bbox_to_anchor=legend_loc
            )

            plt.figure(fig1.number)  # Make fig1 the current active figure
            plt.savefig(
                f"{out_path}_temperature_depth_{time}.png",
                dpi=300,
                bbox_extra_artists=[legend1],
                bbox_inches="tight",
            )

            plt.figure(fig2.number)  # Make fig2 the current active figure
            plt.savefig(
                f"{out_path}_heatflow_depth_{time}.png",
                dpi=300,
                bbox_extra_artists=[combined_legend],
                bbox_inches="tight",
            )

            plt.close(fig1)
            plt.close(fig2)

    @staticmethod
    def create_borehole_temp_plot(
        segindex: list[int],
        times: list,
        params_ds: xr.Dataset | list[xr.Dataset],
        results_ds: xr.Dataset | list[xr.Dataset],
        singlerun: SingleRun,
        out_path: Path,
    ):
        """
        Only compatible with (multiple) single simulations.
        Generates and saves depth-profiles at different timesteps in the simulation results, for fluid temperatures,
        borehole wall temperature, subsurface temperature, subsurface heat flow and subsurface bulk thermal conductivity.

        Generate borehole cross-section temperature plots at different timesteps.

        Parameters
        ----------
        segindex : List[int]
            Segment indices to plot.
        times : List[float]
            Timesteps to plot.
        params_ds : Union[xr.Dataset, List[xr.Dataset]]
            Dataset(s) containing simulation input parameters.
        results_ds : Union[xr.Dataset, List[xr.Dataset]]
            Dataset(s) containing simulation results.
        singlerun : SingleRun
            SingleRun object with simulation input parameters.
        out_path : Path
            Directory to save plots.

        Raises
        ------
        ValueError
            If any required parameter is missing from a DataFrame in `results_ds` or `params_ds`.

        Returns
        -------
        None (the plots are saved directly to the specified output path).
        """
        method = "nearest"
        if not isinstance(params_ds, list):
            params_ds = [params_ds]
            results_ds = [results_ds]

        for time in times:
            for param, results in zip(params_ds, results_ds):
                pipe_temp = results["T_f"].sel(time=time, method=method)
                borehole_wall_temp = results["T_b"].sel(time=time, method=method)

                rb_scale = 1.2

                for iseg in segindex:
                    T_f = pipe_temp[iseg, :]
                    T_b = borehole_wall_temp[iseg]

                    singlerun.bh_design.m_flow = singlerun.sim_params.m_flow[0]
                    singlerun.bh_design.customPipe = (
                        singlerun.bh_design.get_custom_pipe()
                    )
                    custom_pipe = singlerun.bh_design.customPipe
                    custom_pipe.update_thermal_resistances()

                    R = custom_pipe.R[iseg]
                    Q = np.linalg.solve(R, T_f - T_b)
                    Q = np.asarray(Q).flatten()
                    N_xy = 200
                    r_b = custom_pipe.b.r_b
                    x = np.linspace(-rb_scale * r_b, rb_scale * r_b, num=N_xy)
                    y = np.linspace(-rb_scale * r_b, rb_scale * r_b, num=N_xy)
                    X, Y = np.meshgrid(x, y)

                    # Grid points to evaluate temperatures
                    position_pipes = custom_pipe.pos
                    pipe_r_out = custom_pipe.r_out
                    R_fp = custom_pipe.R_f + custom_pipe.R_p[iseg]
                    k_g = custom_pipe.k_g[iseg]
                    k_s = custom_pipe.k_s
                    T_b = np.asarray(T_b)
                    (T_f, temperature, it, eps_max) = gt.pipes.multipole(
                        position_pipes,
                        pipe_r_out,
                        r_b,
                        k_s,
                        k_g,
                        R_fp,
                        T_b,
                        Q,
                        J=3,
                        x_T=X.flatten(),
                        y_T=Y.flatten(),
                    )
                    distance = np.sqrt(X.flatten() ** 2 + Y.flatten() ** 2)
                    temperature[distance > r_b] = np.nan

                    # create figs
                    fig, ax = plt.subplots()
                    ax.set_xlabel("x (m)")
                    ax.set_ylabel("y (m)")
                    # Axis limits
                    plt.axis(
                        [
                            -rb_scale * r_b,
                            rb_scale * r_b,
                            -rb_scale * r_b,
                            rb_scale * r_b,
                        ]
                    )
                    plt.gca().set_aspect("equal", adjustable="box")
                    gt.utilities._format_axes(ax)

                    levels = np.linspace(
                        np.nanmin(temperature), np.nanmax(temperature), 10
                    )
                    cs = plt.contourf(
                        X,
                        Y,
                        temperature.reshape((N_xy, N_xy)),
                        levels=levels,
                        cmap="viridis",
                    )
                    cbar = fig.colorbar(cs)

                    # Borehole wall outline
                    borewall = plt.Circle(
                        (0.0, 0.0),
                        radius=r_b,
                        fill=False,
                        linestyle="--",
                        linewidth=2.0,
                    )
                    ax.add_patch(borewall)

                    # Pipe outlines
                    for pos, r_out_n in zip(position_pipes, pipe_r_out):
                        pipe = plt.Circle(
                            pos,
                            radius=r_out_n,
                            fill=False,
                            linestyle="-",
                            linewidth=4.0,
                        )
                        ax.add_patch(pipe)

                    # Adjust to plot window
                    plt.tight_layout()

                    # Save fig
                    filename = f"{out_path}_borehole_temp_{time}_seg{iseg}.png"
                    fig.savefig(filename)
                    plt.close(fig)

    @staticmethod
    def create_barplot(
        results_df: pd.DataFrame | list[pd.DataFrame],
        params_df: pd.DataFrame | list[pd.DataFrame],
        y_variable: str,
        outpath: Path,
    ) -> None:
        """
        Only compatible with results and inputs of stochastic (MC) simulations.
        Generates and saves a tornado bar plot, that shows the correlation of a specified simulation parameter
        with other simulation input parameters and results.

        This function merges simulation input parameters and results dataframes, calculates the correlation of
        the specified simulation parameter (y_variable) with the other parameters, and visualizes the sensitivity of
        the y_variable to changes in the other system parameters.

        Parameters
        ----------
        results_df : Union[pd.DataFrame, List[pd.DataFrame]]
            Simulation result dataframe(s), contain(s) simulation result parameters as columns.
            Each DataFrame corresponds to a single simulation. It should include the columns 'samples'
            and 'file_name' for merging purposes.
        params_df : Union[pd.DataFrame, List[pd.DataFrame]]
            Simulation input dataframe(s), contain(s) simulation input parameters as columns.
            It should include the columns 'samples' and 'file_name' for merging purposes.
            The column 'k_s' will be renamed to 'k_s_par'.
        y_variable : str
            Variable to analyze sensitivity for. The simulation parameter (either input or result) to be plotted
            on the y-axis. Correlation with this parameter is visualized in the plot.
        outpath : Path
            Directory to save the plot.

        Returns
        -------
        None (plots are saved directly to the specified output path)

        Notes
        -----
        - The function selects only the simulation (input and result) parameters with numeric values and with a non-zero
            standard deviation.
        - If the specified y_variable does not exist in the merged DataFrame, no plot is created. No error is raised.
        """

        sns.set_theme(style="whitegrid")

        # Convert single dataframe inputs to lists
        if not isinstance(params_df, list):
            params_df = [params_df]
        if not isinstance(results_df, list):
            results_df = [results_df]

        # Rename columns if needed
        params_df = [df.rename(columns={"k_s": "k_s_par"}) for df in params_df]

        # Merge the dataframes on common columns
        merged_dfs = [
            pd.merge(df1, df2, on=["samples", "file_name"])
            for df1, df2 in zip(params_df, results_df)
        ]

        # Concatenate merged dataframes if there are multiple
        merged_df = pd.concat(merged_dfs)

        # Group by 'file_name'
        grouped_df = merged_df.groupby("file_name")

        # Initialize the color palette for different groups
        palette = sns.color_palette("husl", n_colors=len(grouped_df))

        # Initialize the figure
        plt.figure(figsize=(10, 6))  # Adjust the figure size if needed

        # Iterate over each group and plot the data
        for i, (group_name, group_df) in enumerate(grouped_df):
            # Filter out columns with string values
            numeric_columns = group_df.select_dtypes(
                include=["float64", "int64"]
            ).columns
            group_numeric = group_df[numeric_columns]

            # Filter out columns with zero standard deviation
            non_constant_columns = group_numeric.columns[
                group_numeric.std().round(7) != 0
            ]
            group_numeric_filtered = group_numeric[non_constant_columns]

            sorted_sensitivity = pd.Series()
            if y_variable in non_constant_columns:
                # Calculate the correlation matrix
                correlation_matrix = group_numeric_filtered.corr()
                sensitivity_to_y_variable = correlation_matrix[y_variable].drop(
                    y_variable
                )  # Remove 'y_variable' itself from the list
                sorted_sensitivity = pd.concat(
                    (
                        sorted_sensitivity.astype(sensitivity_to_y_variable.dtypes),
                        sensitivity_to_y_variable,
                    )
                )
                sorted_sensitivity = sorted_sensitivity.sort_values(
                    ascending=False, na_position="last"
                )
                # sorted_sensitivity = sorted_sensitivity.reindex(sorted_sensitivity.abs().sort_values(ascending=False, na_position='last').index)

                # Plot covariance matrix using a bar chart with different colors for each group
                sns.barplot(
                    x=sorted_sensitivity.values,
                    y=sorted_sensitivity.index,
                    color=palette[i],
                    label=group_name,
                    alpha=0.5,
                )

        # Finalize the plot
        if y_variable in non_constant_columns:
            plt.title(f"Correlation of {y_variable} with input parameters and results")
            plt.xlabel("Correlation Coefficient")
            plt.ylabel("Input and results variables")
            plt.legend(
                bbox_to_anchor=(0, -0.1), loc="upper left"
            )  # Adjust legend position if needed

            save_path = outpath.with_name(outpath.name + f"Sensitivity_{y_variable}")
            plt.savefig(save_path, bbox_inches="tight")
            plt.close()
        else:
            plt.close()

    @staticmethod
    def plot_temperature_field(
        time: int,
        temperature_result_da: xr.DataArray,
        Tmin: float,
        Tmax: float,
        out_path: Path,
    ) -> None:
        """
        Only compatible with results and numerical (FINVOL model) simulations.
        Generates and saves a plot of the calculated 3D (z=len(1)) temperature grid around the borehole, for a specific
        timestep.

        Parameters
        ----------
        time : int
            Index of the timestep to create the plot for.
        temperature_result_da : xr.DataArray
            Temperature DataArray, containing 3D (z=len(1)) grid of
            calculated temperature values around the borehole.
        Tmin : float
            Minimum temperature in the DataArray for color scaling.
        Tmax : float
            Maximum temperature in the DataArray for color scaling.
        out_path : Path
            Directory to save the plot.

        Returns
        -------
        None (plots are saved directly to the specified output path)
        """

        temperature_data = temperature_result_da.T.isel(time=time, z=0).transpose()

        if any(i < 0 for i in temperature_result_da.x):
            ymin = min(temperature_result_da.x)
            ymax = max(temperature_result_da.x)
        else:
            ymin = max(temperature_result_da.x)
            ymax = min(temperature_result_da.x)

        # Create a figure and set size
        fig = plt.figure(figsize=(10, 5))

        # Add subplot
        ax1 = fig.add_subplot()

        # Define contour levels with even spacing every 5 degrees Celsius
        levels = range(int(Tmin), int(Tmax) + 5, 5)

        temperature_data.plot.contourf(
            ax=ax1,
            ylim=(ymin, ymax),
            cmap="magma",
            vmin=Tmin,
            vmax=Tmax,
            cbar_kwargs={"label": "Temperature [C]"},
            levels=levels,
        )

        timestep = temperature_result_da.time.isel(time=time).values  # in hours

        timestep_days = round(int(timestep) / 24, 0)

        plt.title(
            f"Temperature field over depth, in radial direction after {timestep_days} days"
        )
        plt.xlabel("Distance from well (m)")
        plt.ylabel("Depth from top of well (m)")

        plt.tight_layout()

        filename = out_path.with_name(out_path.name + f"_T_field_{timestep_days}.png")
        plt.savefig(filename)
        plt.close()

    @staticmethod
    def create_temperature_field_movie(in_path: Path) -> None:
        """
        Only compatible with results and numerical (FINVOL model) simulations.
        Generates and saves a clip of a sequence of the temperature grid plots creates using the method plot_temperature_field.

        Parameters
        ----------
        in_path : Path
            Directory containing temperature field images.

        Returns
        -------
        None (plots are saved directly to the specified output path)
        """
        # Get list of image filenames
        image_filenames = [
            f.name for f in Path(in_path).iterdir() if f.suffix == ".png"
        ]

        image_filenames.sort(key=PlotResults.extract_timestep)

        images = []
        for image in image_filenames:
            im_obj = Image.open((in_path / image), "r")
            images.append(im_obj)

        fig, ax = plt.subplots()

        ims = []
        for i in range(len(images)):
            im = ax.imshow(images[i], animated=True)
            if i == 0:
                # set initial image
                ax.imshow(images[i], animated=True)
            ims.append([im])

        ax.axis("off")

        ani = animation.ArtistAnimation(fig, ims, interval=500, repeat_delay=100)

        plt.tight_layout()
        plt.close()

        movie_name = "Tfield_animation.gif"
        ani.save(in_path / movie_name)

    @staticmethod
    def extract_timestep(filename: str) -> float:
        """
        Extracts timestep from the filename, used for the chronological ordering of temperature grid plots in the
        method create_temperature_field_movie.

        Parameters
        ----------
        filename : str
            Name of the image file.

        Returns
        -------
        float
            Extracted timestep or infinity if not found.
        """
        match = re.search(r"T_field_(\d+\.\d+)\.png", filename)
        if match:
            return float(match.group(1))
        else:
            # If no match is found, return a very large number
            return float("inf")
