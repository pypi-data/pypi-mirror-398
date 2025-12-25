from pathlib import Path

import pandas as pd
import xarray as xr

from geoloop.configuration import PlotInputConfig


class PlotInput:
    """
    A class to handle the settings from the plotting configuration file and load the simulation dataset that requires plotting.

    Attributes
    ----------
    base_dir : str or Path object
        Base directory for simulation results.
    run_names : list
        Names of the simulation runs.
    model_types : list
        Type of Geoloop model used in the simulations (i.e., ANALYTICAL, FINVOL).
    run_types : list
        Type of simulation runs (i.e., target power (run_type=TIN) or target fluid temperatures (run_type=POWER)).
    run_modes : list
        Modes of runs (i.e., single run (SR), Monte Carlo (MC)).
    plot_names : list
        Names of simulation runs that is used in the legend of the plots. Optional.
    plot_nPipes : list
        Index for pipes dimension (nPipes) to use in the data selection for plotting of the results.
    plot_layer_k_ss : list
        Index for dimension layer_k_s to use in the data selection for plotting of the input parameters.
    plot_layer_kgs : list
        Index for dimension layer_kg to use in the data selection for plotting of the input parameters.
    plot_layer_Tgs : list
        Index for dimension layer_Tg to use in the data selection for plotting of the input parameters.
    plot_nzs : list
        Index for dimension z to use in the data selection for plotting of the results.
    plot_ntimes : list
        Index for dimension time to use in the data selection for plotting of the results.
    plot_nzsegs : list
        Index for dimension zseg to use in the data selection for plotting of the results.
    plot_times : list
        Timesteps in the simulation results for which the depth-profiles are plotted.
    plot_temperature_field : bool
        Flag to plot temperature fields in case of plotting numerical simulation.
    plot_time_depth : bool
        Flag to plot time-depth profiles.
    plot_time_parameters : list
        Parameters to plot in a timeseries plot. Options: dploop, qloop, flowrate, T_fi, T_fo, T_bave, Q_b, COP, Delta_T.
        Where Delta_T = T_fo - T_fi and COP = Q_b/qloop
    plot_depth_parameters : list
        Parameters to plot in the depth plots. Options: T_b, Tg, T_f, Delta_T
    plot_crossplot_barplot : bool
        Flag to plot scatter crossplots and bar sensitivity plot in case of a Monte Carlo simulation.
    newplot : bool
        Flag for new plot for every listed simulation in the config, or overlay the plots of the listed simulations.
    crossplot_vars : list
        Data variables to plot on the y-axis of the cross plots in case of a Monte Carlo simulation.
    """

    def __init__(
        self,
        base_dir: str | Path,
        run_names: list[str],
        model_types: list[str],
        run_types: list[str],
        run_modes: list[str],
        plot_names: list[str | None],
        plot_nPipes: list[int],
        plot_layer_k_ss: list[int],
        plot_layer_kgs: list[int],
        plot_layer_Tgs: list[int],
        plot_nzs: list[int],
        plot_ntimes: list[int],
        plot_nzsegs: list[int],
        plot_times: list[int],
        plot_temperature_field: bool,
        plot_time_depth: bool,
        plot_crossplot_barplot: bool,
        newplot: bool,
        crossplot_vars: list[str],
        plot_time_parameters: list[str] | bool,
        plot_depth_parameters: list[str] | bool,
        plot_borehole_temp: list[int],
    ):
        self.base_dir = base_dir
        self.run_names = run_names
        self.model_types = model_types
        self.run_types = run_types
        self.run_modes = run_modes
        self.plot_names = plot_names
        self.plot_nPipes = plot_nPipes
        self.plot_layer_k_ss = plot_layer_k_ss
        self.plot_layer_kgs = plot_layer_kgs
        self.plot_layer_Tgs = plot_layer_Tgs
        self.plot_nzs = plot_nzs
        self.plot_ntimes = plot_ntimes
        self.plot_nzsegs = plot_nzsegs
        self.plot_times = plot_times
        self.plot_temperature_field = plot_temperature_field
        self.plot_time_depth = plot_time_depth
        self.plot_crossplot_barplot = plot_crossplot_barplot
        self.newplot = newplot
        self.crossplot_vars = crossplot_vars
        self.plot_time_parameters = plot_time_parameters
        self.plot_depth_parameters = plot_depth_parameters
        self.plot_borehole_temp = plot_borehole_temp

    @classmethod
    def from_config(cls, config: PlotInputConfig) -> "PlotInput":
        """
        Create a PlotInput instance from a configuration dictionary.

        Parameters
        ----------
        config : PlotInputConfig
            Configuration object containing parameters for plotting.

        Returns
        -------
        PlotInput
        """
        # Handle optional plot_names
        plot_names = (
            config.plot_names
            if config.plot_names is not None
            else [False] * len(config.run_names)
        )

        return cls(
            base_dir=config.base_dir,
            run_names=config.run_names,
            model_types=config.model_types,
            run_types=config.run_types,
            run_modes=config.run_modes,
            plot_names=plot_names,
            plot_nPipes=config.plot_nPipes,
            plot_layer_k_ss=config.plot_layer_k_s,
            plot_layer_kgs=config.plot_layer_kg,
            plot_layer_Tgs=config.plot_layer_Tg,
            plot_nzs=config.plot_nz,
            plot_ntimes=config.plot_ntime,
            plot_nzsegs=config.plot_nzseg,
            plot_times=config.plot_times,
            plot_temperature_field=config.plot_temperature_field,
            plot_time_depth=config.plot_time_depth,
            plot_crossplot_barplot=config.plot_crossplot_barplot,
            newplot=config.newplot,
            crossplot_vars=config.crossplot_vars,
            plot_time_parameters=config.plot_time_parameters,
            plot_depth_parameters=config.plot_depth_parameters,
            plot_borehole_temp=config.plot_borehole_temp,
        )

    def list_filenames(self) -> None:
        """
        Construct filenames for loading the .h5 files with simulation results.
        """
        self.file_names = []
        for i in range(len(self.run_names)):
            file_name = (
                self.run_names[i]
                + "_"
                + self.model_types[i][0]
                + "_"
                + self.run_types[i][0]
                + "_"
                + self.run_modes[i]
            )
            self.file_names.append(file_name)

    def load_params_result_data(self) -> tuple:
        """
        Load the .h5 file(s) for the simulations that are plotted.

        Returns
        -------
        Tuple[List[xr.Dataset], List[xr.Dataset]]
            A tuple containing simulation input parameter dataset and simulation results dataset.
        """
        params_ds = []
        results_ds = []

        for i in range(len(self.run_names)):
            out_path = self.base_dir / self.run_names[i] / self.file_names[i]
            datasets_h5path = out_path.with_name(out_path.stem + ".h5")

            # Open and close datasets immediately after reading them
            with xr.open_dataset(
                datasets_h5path, group="parameters", engine="h5netcdf"
            ) as param_ds_i:
                params_ds.append(param_ds_i.load())  # Load into memory, then close file

            with xr.open_dataset(
                datasets_h5path, group="results", engine="h5netcdf"
            ) as results_ds_i:
                results_ds.append(results_ds_i.load())

        return (
            params_ds,
            results_ds,
        )  # Now these are fully loaded and detached from file

    def load_temperature_field_data(self) -> list[xr.DataArray]:
        """
        Only compatible with results of numerical (FINVOL model) simulations, that explicitly saved the calculated
        temperature grid around the borehole.
        Load the .h5 file(s) with temperature grid data.

        Returns
        -------
        List[xr.DataArray]
            List of temperature field DataArrays.
        """

        temperature_field_da = []

        for i in range(len(self.run_names)):
            if self.model_types[i] != "FINVOL":
                print(
                    "Model type does not allow for plotting numerical temperature field."
                )
                continue

            self.file_names_T = []
            file_name_T = f"{self.run_names[i]}_{self.model_types[0][i]}_{self.run_types[0][i]}_FINVOL_T"
            self.file_names_T.append(file_name_T)

            out_path = self.base_dir / self.run_names[i] / file_name_T
            Tfield_res_h5path = out_path.with_name(out_path.stem + ".h5")

            # Open and close the dataset immediately after reading
            with xr.open_dataarray(
                Tfield_res_h5path, group="Temperature", engine="h5netcdf"
            ) as temperature_field_da_i:
                temperature_field_da.append(
                    temperature_field_da_i.load()
                )  # Load into memory

        return temperature_field_da


class DataTotal:
    """
    A class to store simulation input parameter and result datasets.

    Attributes
    ----------
    results_ds : xarray.Dataset or list of xarray.Dataset
        Dataset (or list of Datasets) containing simulation results.
    params_ds : xarray.Dataset or list of xarray.Dataset
        Dataset (or list of Datasets) containing simulation input parameters.
    Tresult_da : xarray.Dataset or list of xarray.Dataset
        DataArray containing 3D (z=len(1)) grid of calculated temperature values around the borehole.
    """

    def __init__(self, results_ds, params_ds, temperature_field_da):
        self.results_ds = results_ds
        self.params_ds = params_ds
        self.temperature_field_da = temperature_field_da


class DataSelection:
    """
    A class to select datasets required for plotting. It stores subsets of simulation input parameters and simulation
    results for the different plot types.

    Attributes
    ----------
    crossplot_params_df : pd.DataFrame or list of pd.DataFrame
        DataFrame (or list of DataFrames) of simulation input parameters for the cross-plots.
    crossplot_results_df : pd.DataFrame or list of pd.DataFrame
        DataFrame (or list of DataFrames) of simulation results for the cross-plots.
    timeplot_results_df : pd.DataFrame or list of pd.DataFrame
        DataFrame (or list of DataFrames) of simulation results for the time-plots.
    depthplot_params_ds : xarray.Dataset or list of xarray.Dataset
        Datasets (or list of Datasets) of simulation input parameters for the depth-plots.
    depthplot_results_ds : xarray.Dataset or list of xarray.Dataset
        Datasets (or list of Datasets) of simulation results for the depth-plots.
    """

    def __init__(
        self,
        crossplot_params_df: list[pd.DataFrame],
        crossplot_results_df: list[pd.DataFrame],
        timeplot_results_df: list[pd.DataFrame],
        depthplot_params_ds: list[xr.Dataset],
        depthplot_results_ds: list[xr.Dataset],
    ):
        self.crossplot_params_df = crossplot_params_df
        self.crossplot_results_df = crossplot_results_df
        self.timeplot_results_df = timeplot_results_df
        self.depthplot_params_ds = depthplot_params_ds
        self.depthplot_results_ds = depthplot_results_ds

    @classmethod
    def select_sub_datasets(
        cls, plotinput: PlotInput, datatotal: DataTotal
    ) -> "DataSelection":
        """
        Selects and aggregates subsets of datasets for plotting, based on PlotInput settings.

        Parameters
        ----------
        plotinput : PlotInput
            Plotting configuration.
        datatotal : DataTotal
            Object containing simulation datasets (including simulation results and input parameters).

        Returns
        -------
        DataSelection
            Object containing selected subsets of datasets ready for plotting.
        """
        crossplot_params_df_total = []
        crossplot_results_df_total = []
        timeplot_results_df_total = []
        depthplot_params_ds_total = []
        depthplot_results_ds_total = []

        for i in range(len(plotinput.run_names)):
            plot_nPipe = plotinput.plot_nPipes[i]
            plot_layer_k_s = plotinput.plot_layer_k_ss[i]
            plot_layer_kg = plotinput.plot_layer_kgs[i]
            plot_layer_Tg = plotinput.plot_layer_Tgs[i]
            plot_nz = plotinput.plot_nzs[i]
            plot_ntime = plotinput.plot_ntimes[i]
            plot_nzseg = plotinput.plot_nzsegs[i]
            file_name = plotinput.file_names[i]
            plot_name = plotinput.plot_names[i]

            param_ds = datatotal.params_ds[i]
            results_ds = datatotal.results_ds[i]

            # For plotting, add run_name dummy in all dims to the results and param datasets
            # Use plot_name if defined, otherwise fallback to file_name
            name_to_use = plot_name if plot_name else file_name

            # Add to param_ds
            param_ds["file_name"] = xr.DataArray(
                data=name_to_use,
                dims=("samples", "nPipes", "layer_k_s", "layer_k_g", "layer_Tg"),
                coords=param_ds.coords,
            )

            # Add to results_ds based on run mode
            if plotinput.run_modes[i] == "SR":
                results_ds["file_name"] = xr.DataArray(
                    data=name_to_use,
                    dims=("samples", "time", "nPipes", "zseg", "z"),
                    coords=results_ds.coords,
                )
            elif plotinput.run_modes[i] == "MC":
                results_ds["file_name"] = xr.DataArray(
                    data=name_to_use,
                    dims=("samples", "time", "nPipes"),
                    coords=(results_ds.samples, results_ds.time, results_ds.nPipes),
                )

            # Select crossplot datasets
            # Parameters
            crossplot_params_ds = param_ds.isel(
                layer_k_s=plot_layer_k_s,
                layer_k_g=plot_layer_kg,
                layer_Tg=plot_layer_Tg,
                xy=-1,
                nPipes=plot_nPipe,
            )
            crossplot_params_df = crossplot_params_ds.to_dataframe(["samples"])
            crossplot_params_df["samples"] = crossplot_params_df.index
            crossplot_params_df = crossplot_params_df.reset_index(drop=True)
            crossplot_params_df_total.append(crossplot_params_df)

            # Results
            # for cross-plotting, calculate average of the results over all dimensions except samples and time
            crossplot_k_s_avg = results_ds.isel(
                time=plot_ntime, z=plot_nz, nPipes=plot_nPipe
            )["k_s"].mean(dim="zseg")
            if "z" in results_ds["k_g"].dims:
                crossplot_k_g_avg = results_ds.isel(
                    time=plot_ntime, zseg=plot_nzseg, nPipes=plot_nPipe
                )["k_g"].mean(dim="z")
            else:
                crossplot_k_g_avg = results_ds.isel(time=plot_ntime, nPipes=plot_nPipe)[
                    "k_g"
                ].mean(dim="zseg")
            crossplot_T_b_avg = results_ds.isel(
                time=plot_ntime, z=plot_nz, nPipes=plot_nPipe
            )["T_b"].mean(dim="zseg")
            crossplot_qzb_avg = results_ds.isel(
                time=plot_ntime, z=plot_nz, nPipes=plot_nPipe
            )["qzb"].mean(dim="zseg")
            crossplot_results_ds = results_ds.isel(
                time=plot_ntime, zseg=plot_nzseg, z=plot_nz, nPipes=plot_nPipe
            )
            crossplot_results_df = crossplot_results_ds.to_dataframe(["samples"])

            # Add calculated averages over depth to the datafame for plotting
            crossplot_results_df["k_s_res"] = crossplot_k_s_avg.values
            crossplot_results_df["k_g_res"] = crossplot_k_g_avg.values
            crossplot_results_df["T_b"] = crossplot_T_b_avg.values
            crossplot_results_df["qzb"] = crossplot_qzb_avg.values
            crossplot_results_df["samples"] = crossplot_results_df.index
            crossplot_results_df = crossplot_results_df.reset_index(drop=True)
            crossplot_results_df_total.append(crossplot_results_df)

            # Select timeplot datasets
            # Select the desired dimensions from the param dataset to convert to a dataframe for plotting
            timeplot_results_ds = results_ds.isel(
                samples=-1, zseg=plot_nzseg, z=plot_nz, nPipes=plot_nPipe
            )
            timeplot_results_df = timeplot_results_ds.to_dataframe(["time"])
            timeplot_results_df["time"] = timeplot_results_df.index
            timeplot_results_df = timeplot_results_df.reset_index(drop=True)
            timeplot_results_df_total.append(timeplot_results_df)

            # Selects depthplot datasets
            # For MC runs, select here another sample to plot a depth plot with another thermal conductivity profile
            # than the basecase
            depthplot_params_ds = param_ds.isel(samples=-1)
            depthplot_results_ds = results_ds.isel(samples=-1)
            depthplot_results_ds_total.append(depthplot_results_ds)
            depthplot_params_ds_total.append(depthplot_params_ds)

        dataselection = cls(
            crossplot_params_df_total,
            crossplot_results_df_total,
            timeplot_results_df_total,
            depthplot_params_ds_total,
            depthplot_results_ds_total,
        )

        return dataselection
