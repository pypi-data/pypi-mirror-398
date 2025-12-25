from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from geoloop.configuration import SingleRunConfig, StochasticRunConfig


def get_param_names(
    config: SingleRunConfig | StochasticRunConfig | None = None,
) -> tuple[list[str], list[str]]:
    """
    Identify locked and variable parameter names from a configuration dictionary for Monte Carlo simulations.

    These parameters are used to organize results in HDF5 files during
    simulation post-processing.

    Parameters
    ----------
    config : SingleRunConfig, optional
        Configuration object that may contain additional optional
        parameters. If provided, certain optional keys will be added
        to the list of locked parameters.

    Returns
    -------
    tuple of (list of str, list of str)
        - `variable_param_names` : List of variable parameter names that
          can change between Monte Carlo runs.
        - `locked_param_names` : List of locked parameter names that
          remain fixed across runs. Optional parameters found in `config`
          are also included.
    """
    variable_param_names = [
        "k_s_scale",
        "k_p",
        "insu_z",
        "insu_dr",
        "insu_k",
        "m_flow",
        "Tin",
        "H",
        "epsilon",
        "alfa",
        "Tgrad",
        "Q",
        "fluid_percent",
    ]
    locked_param_names = [
        "type",
        "D",
        "r_b",
        "pos",
        "r_out",
        "SDR",
        "fluid_str",
        "nInlets",
        "Tg",
        "z_Tg",
        "k_s",
        "z_k_s",
        "model_type",
        "run_type",
        "nyear",
        "nled",
        "nsegments",
        "k_g",
        "z_k_g",
    ]

    return variable_param_names, locked_param_names


def getresultsvar_fordims(var_names_dim: list[str], results_object: Any) -> np.ndarray:
    """
    Extract an array of result values for specified variable names from a results object.

    Parameters
    ----------
    var_names_dim : list of str
        List of variable names to extract from the results object.
    results_object : SingleRunResult
        SingleRunResult object containing the results of a single model run. The function
        will attempt to access each variable as an attribute of this object.

    Returns
    -------
    np.ndarray
        Array of result values corresponding to the requested variable names.
        If a variable is not present in the object, `None` is used for that entry.

    Notes
    -----
    The resulting array preserves the order of `var_names_dim`.
    """
    # Create array of the result arrays that should be stored in the dataset based on the list of variable names
    results_list = []
    for var in var_names_dim:
        var_value = getattr(results_object, var, None)

        if var_value is not None:
            results_list.append(var_value)
        else:
            results_list.append(None)

    results_list = np.array(results_list)

    return results_list


def save_singlerun_results(config: SingleRunConfig, result: Any, outpath: Path) -> None:
    """
    Saves the results from a single model run into an HDF5 file. Results and input parameters are grouped into datasets
    based on their dimensions, ensuring compatibility with HDF5 storage formats.

    The function organizes results by:
    - Time series (scalar variables)
    - Time and depth segment
    - Time, depth, and pipe
    - Depth segment only

    Input parameters are grouped by:
    - Scalar parameters
    - Pipe-specific parameters
    - Depth-segment parameters (e.g., `k_s`)
    - Depth-specific parameters (e.g., `k_g`, `Tg`)

    All datasets are saved into an HDF5 file with groups "results" and "parameters".

    Parameters
    ----------
    config : SingleRunConfig
        Configuration object containing all input parameters from the JSON configuration file.

    result : SingleRunSim object
        Results object from a single model run.

    outpath : pathlib.Path
        Filepath for saving the output HDF5 file. The file will be named
        `{stem}_SR.h5` based on `outpath`.

    Returns
    -------
    None
        Saves the results and input parameters to an HDF5 file on disk.

    """
    # ==================================================================
    # Results grouped by time dimension
    # ==================================================================

    # Retrieve variable names for timeseries scalar results
    var_names_t = result.getResultAttributesTimeseriesScalar()

    # Retrieve time coordinate values
    time_coord = result.gethours()

    # Extract result arrays for timeseries variables
    results_t = getresultsvar_fordims(var_names_t, result)

    # Create DataArray for timeseries results and convert to dataset
    Results_da_t = xr.DataArray(
        results_t,
        coords={"variables": var_names_t, "time": time_coord},
        dims=["variables", "time"],
    )
    Results_da_t = Results_da_t.rename("Results_t")
    Results_ds_t = Results_da_t.to_dataset(dim="variables")

    # ==================================================================
    # Results grouped by time and depth segment dimensions
    # ==================================================================

    # Retrieve variable names for timeseries depth-segment results
    var_names_tzseg = result.getResultAttributesTimeseriesDepthseg()

    # Retrieve depth-segment coordinate values
    zseg_coord = result.getzseg()

    # Extract result arrays for timeseries depth-segment variables
    results_tzseg = getresultsvar_fordims(var_names_tzseg, result)

    # Create DataArray for timeseries depth-segment results and convert to dataset
    Results_da_tzseg = xr.DataArray(
        results_tzseg,
        coords={"variables": var_names_tzseg, "time": time_coord, "zseg": zseg_coord},
        dims=["variables", "time", "zseg"],
    )
    Results_da_tzseg = Results_da_tzseg.rename("Results_tzseg")
    Results_ds_tzseg = Results_da_tzseg.to_dataset(dim="variables")

    # ==================================================================
    # Results grouped by time, depth, and pipe dimensions
    # ==================================================================

    # Retrieve variable names for timeseries depth-pipe results
    var_names_tzp = result.getResultAttributesTimeserieDepth()

    # Retrieve depth and pipe coordinate values
    z_coord = result.getz()
    pipes_coord = range(result.get_n_pipes())

    # Extract result arrays for timeseries depth-pipe variables
    results_tzp = getresultsvar_fordims(var_names_tzp, result)

    # Create DataArray for timeseries depth-pipe results and convert to dataset
    Results_da_tzp = xr.DataArray(
        results_tzp,
        coords={
            "variables": var_names_tzp,
            "time": time_coord,
            "z": z_coord,
            "nPipes": pipes_coord,
        },
        dims=["variables", "time", "z", "nPipes"],
    )
    Results_da_tzp = Results_da_tzp.rename("Results_tzp")
    Results_ds_tzp = Results_da_tzp.to_dataset(dim="variables")

    # ==================================================================
    # Results grouped by depth segment dimension
    # ==================================================================

    # Retrieve variable names for depth-segment results
    var_names_zseg = result.getResultAttributesDepthseg()

    # Extract result arrays for depth-segment variables
    results_zseg = getresultsvar_fordims(var_names_zseg, result)

    # Create DataArray for depth-segment results and convert to dataset
    Results_da_zseg = xr.DataArray(
        results_zseg,
        coords={"variables": var_names_zseg, "zseg": zseg_coord},
        dims=["variables", "zseg"],
    )
    Results_da_zseg = Results_da_zseg.rename("Results_zseg")
    Results_ds_zseg = Results_da_zseg.to_dataset(dim="variables")

    # ==================================================================
    # Input parameters grouped by various dimensions
    # ==================================================================

    # Combine variable and locked parameter names
    variable_param_names, locked_param_names = get_param_names(config)
    param_names = variable_param_names + locked_param_names

    # Create dictionary of input parameters
    param_dict = {
        key: (
            [getattr(config, key)]
            if isinstance(getattr(config, key), np.ndarray)
            else getattr(config, key)
        )
        for key in param_names
    }

    # Create dataset for scalar parameters
    param = {
        key: value for key, value in param_dict.items() if not isinstance(value, list)
    }
    param_da = xr.DataArray(
        list(param.values()), coords={"param": list(param.keys())}, dims=["param"]
    )
    param_ds = param_da.to_dataset(dim="param")

    # Create dataset for pipe-specific parameters
    param_x = {
        key: value
        for key, value in param_dict.items()
        if isinstance(value, list) and len(value) == len(pipes_coord)
    }

    pipe_pos = np.asarray(param_x["pos"])
    r_out = param_x["r_out"]

    pipe_pos_ds = xr.Dataset(
        data_vars=dict(pipe_pos=(["nPipes", "xy"], pipe_pos)),
        coords=dict(nPipes=(["nPipes"], pipes_coord)),
    )
    r_out_ds = xr.Dataset(
        data_vars=dict(r_out=(["nPipes"], r_out)),
        coords=dict(nPipes=(["nPipes"], pipes_coord)),
    )

    # Create dataset for depth-segment specific parameters (k_s)
    param_z_k_s = {
        key: value
        for key, value in param_dict.items()
        if "k_s" in key and key not in param
    }
    param_z_k_s_da = xr.DataArray(
        list(param_z_k_s.values()),
        coords={
            "param": (list(param_z_k_s.keys())),
            "layer_k_s": range(len(param_z_k_s["k_s"])),
        },
        dims=["param", "layer_k_s"],
    )
    param_z_k_s_ds = param_z_k_s_da.to_dataset(dim="param")

    # Create dataset for depth-specific parameters (k_g)
    param_z_k_g = {
        key: value
        for key, value in param_dict.items()
        if key not in param and "k_g" in key
    }
    param_z_da = xr.DataArray(
        list(param_z_k_g.values()),
        coords={
            "param": (list(param_z_k_g.keys())),
            "layer_k_g": range(len(param_z_k_g["k_g"])),
        },
        dims=["param", "layer_k_g"],
    )
    param_z_k_g_ds = param_z_da.to_dataset(dim="param")

    # Create dataset for depth-specific temperature parameters (Tg)
    param_z_Tg = {
        key: value
        for key, value in param_dict.items()
        if key not in param and "Tg" in key
    }

    if "Tg" in param_z_Tg:
        param_z_da = xr.DataArray(
            list(param_z_Tg.values()),
            coords={
                "param": (list(param_z_Tg.keys())),
                "layer_Tg": range(len(param_z_Tg["Tg"])),
            },
            dims=["param", "layer_Tg"],
        )
        param_z_Tg_ds = param_z_da.to_dataset(dim="param")
    else:
        param_z_Tg_ds = None

    # ==================================================================
    # Merging datasets and saving to HDF5
    # ==================================================================

    # Merge parameter datasets, excluding None values
    datasets_to_merge = [
        ds
        for ds in [
            param_ds,
            pipe_pos_ds,
            r_out_ds,
            param_z_k_s_ds,
            param_z_k_g_ds,
            param_z_Tg_ds,
        ]
        if ds
    ]
    param_ds_fromds = xr.merge(datasets_to_merge)

    # Merge results datasets
    Results_ds_fromds = xr.merge(
        [Results_ds_t, Results_ds_tzseg, Results_ds_tzp, Results_ds_zseg]
    )

    results_file = outpath.with_name(outpath.stem + "_SR.h5")

    # Save merged datasets to HDF5 file
    Results_ds_fromds.to_netcdf(results_file, group="results", engine="h5netcdf")
    param_ds_fromds.to_netcdf(
        results_file, group="parameters", engine="h5netcdf", mode="a"
    )


def process_variable_values(
    results: Any, var_names: list[str], sample_da_shape: np.ndarray
) -> np.ndarray:
    """
    Process variable values from Monte Carlo simulation results into a structured sample array.

    This function extracts variables from a results object and constructs a
    NumPy array that conforms to a given sample shape. Each variable's values
    are expanded and stacked to ensure consistent dimensionality.

    Parameters
    ----------
    results : object
        Results from a Monte Carlo simulation run, containing attributes
        corresponding to variable names.
    var_names : list of str
        List of variable names to extract from the results object. These
        will form one dimension of the output array.
    sample_da_shape : np.ndarray
        Template array specifying the desired shape of the sample. Used to
        ensure consistency in the output array dimensions.

    Returns
    -------
    np.ndarray
        Array containing variable values stacked according to the template
        shape. Missing variables are filled with `None` entries.

    Notes
    -----
    - Each variable is expanded along new axes if needed to match the sample array's dimensionality.
    - Variables are stacked along the first axis in the order of `var_names`.
    """
    # Initialize the sample array with the desired shape.
    # This will be used to ensure all extracted data conforms to the same structure.
    sample_da = sample_da_shape

    # Iterate over each variable name to extract corresponding values from the results.
    for var in var_names:
        var_values = []  # List to store values for the current variable across Monte Carlo runs.

        # Extract values for the current variable from the results object.
        # If the variable is not present, append None.
        singlerun = results
        var_value = getattr(singlerun, var, None)

        if var_value is not None:
            var_values.append(var_value)  # Append the variable's value if found.
        else:
            var_values.append(None)  # Append None if the variable is not found.

        # Convert the list of values to a numpy array for consistent processing.
        var_values = np.array(var_values)

        # Expand dimensions of the variable values array to match the dimensions of the sample array.
        while var_values.ndim < sample_da.ndim:
            var_values = np.expand_dims(var_values, axis=0)

        # Stack the variable values into the sample array.
        # If the sample array is empty, initialize it with the current variable values.
        if sample_da.size == 0:
            sample_da = var_values
        else:
            sample_da = np.vstack((sample_da, var_values))

    return sample_da


def save_MCrun_results(
    config: SingleRunConfig, param_dict: dict, results: list[Any], outpath: Path
) -> None:
    """
    Save the results of a Monte Carlo model run to an HDF5 file.

    The function organizes the results and input parameters into
    structured xarray datasets, grouped by their dimensions, and
    writes them to the specified HDF5 file.

    Parameters
    ----------
    config : SingleRunConfig
        Configuration object containing model settings and metadata.
    param_dict : dict
        Dictionary containing locked and variable input parameters
        along with their values, as specified in the configuration.
    results : list[Any]
        List of results from Monte Carlo simulation runs. Each element
        is a results object containing simulation outputs for one run.
    outpath : Path
        Path to the directory and file name for saving the HDF5 output.

    Returns
    -------
    None
        The function writes the datasets to an HDF5 file and does not return any value.

    Notes
    -----
    - Each Monte Carlo sample is processed individually, and results are
      concatenated along a 'samples' dimension.
    - Input parameters are grouped into variable and locked parameters,
      and datasets are created for parameters with special dimensions
      such as pipe-specific or layer-specific values.
    - The final HDF5 file contains two main groups: "results" and "parameters".
    """
    # List to store datasets for all Monte Carlo samples
    Results_datasets = []

    # Create sample and time coordinate values for all DataArrays
    n_samples = len(results)
    sample_coord = range(n_samples)
    time_coord = results[0].gethours()

    for sample in sample_coord:
        # ================================================================
        # Results: Variables with [variables, samples, time] dimensions
        # ================================================================
        var_names = results[sample].getResultAttributesTimeseriesScalar()

        # Create DataArray for the above defined var_names
        # Sample_da array shape must be the same shape as the one that will be created from var values, except for the first dim
        sample_da_shape = np.empty((0, sample, 0), dtype=object)
        sample_da = process_variable_values(results[sample], var_names, sample_da_shape)
        Results_da_st = xr.DataArray(
            sample_da,
            coords={"variables": var_names, "samples": [sample], "time": time_coord},
            dims=["variables", "samples", "time"],
        )
        Results_da_st = Results_da_st.rename("Results_st")

        Results_ds_st = Results_da_st.to_dataset(dim="variables")

        # ================================================================
        # Results: Variables with [variables, samples, time, zseg] dimensions
        # ================================================================
        var_names = results[sample].getResultAttributesTimeseriesDepthseg()

        # Create coordinate values for the DataArray
        zseg_coord = results[sample].getzseg()

        # Create DataArray for the above defined var_names
        # Sample_da array shape must be the same shape as the one that will be created from var values, except for the first dim
        sample_da_shape = np.empty((0, sample, len(time_coord), 0), dtype=object)
        sample_da = process_variable_values(results[sample], var_names, sample_da_shape)
        Results_da_stzseg = xr.DataArray(
            sample_da,
            coords={"variables": var_names, "samples": [sample], "time": time_coord},
            dims=["variables", "samples", "time", "zseg"],
        )
        Results_da_stzseg = Results_da_stzseg.rename("Results_stzseg")
        Results_ds_stzseg = Results_da_stzseg.to_dataset(dim="variables")

        # Create coordinate values for the DataArray
        pipes_coord = range(results[sample].get_n_pipes())

        # ================================================================
        # Results: Variables with [variables, samples, time, z, nPipes] dimensions
        # ================================================================
        var_names = results[sample].getResultAttributesTimeserieDepth()

        # Create coordinate values for the DataArray
        z_coord = results[sample].getz()

        # Create DataArray for the above defined var_names
        # Sample_da array shape must be the same shape as the one that will be created from var values, except for the first dim
        sample_da_shape = np.empty((0, sample, len(time_coord), 0, 0), dtype=object)
        sample_da = process_variable_values(results[sample], var_names, sample_da_shape)
        Results_da_stz = xr.DataArray(
            sample_da,
            coords={
                "variables": var_names,
                "samples": [sample],
                "time": time_coord,
                "nPipes": pipes_coord,
            },
            dims=["variables", "samples", "time", "z", "nPipes"],
        )
        Results_da_stz = Results_da_stz.rename("Results_stz")
        Results_ds_stz = Results_da_stz.to_dataset(dim="variables")

        # ================================================================
        # Interpolated subsurface variables with [variables, samples, zseg] dimensions
        # ================================================================
        # create dataset from results with dim(len(resnames2), nsamples, zseg)
        # Variables with zseg dims
        var_names = results[sample].getResultAttributesDepthseg()

        # Create DataArray for the above defined var_names
        # Sample_da array shape must be the same shape as the one that will be created from var values, except for the first dim
        sample_da_shape = np.empty((0, sample, 0), dtype=object)
        sample_da = process_variable_values(results[sample], var_names, sample_da_shape)

        Results_da_zsegk = xr.DataArray(
            sample_da,
            coords={"variables": var_names, "samples": [sample]},
            dims=["variables", "samples", "zseg"],
        )
        Results_da_zsegk = Results_da_zsegk.rename("Results_zsegk")
        Results_ds_zsegk = Results_da_zsegk.to_dataset(dim="variables")

        # ==================================================================
        # Ceate datasets for the coordinates that have a variable length over the samples
        # These coordinates are not stored for the variables themselves (they have dimensions without coordinates) but are stored here seperately
        # ==================================================================

        # dim nresnames, nsamples, zseg
        sample_da_shape = np.empty((0, sample, len(zseg_coord)), dtype=object)
        sample_da = process_variable_values(results[sample], ["zseg"], sample_da_shape)
        Results_da_zseg = xr.DataArray(
            sample_da,
            coords={"variables": ["zseg_coord"], "samples": [sample]},
            dims=["variables", "samples", "zseg"],
        )
        Results_da_zseg = Results_da_zseg.rename("Results_zseg")
        Results_ds_zseg = Results_da_zseg.to_dataset(dim="variables")

        # dim nresnames, nsamples, z
        sample_da_shape = np.empty((0, sample, len(z_coord)), dtype=object)
        sample_da = process_variable_values(results[sample], ["z"], sample_da_shape)
        Results_da_z = xr.DataArray(
            sample_da,
            coords={"variables": ["z_coord"], "samples": [sample]},
            dims=["variables", "samples", "z"],
        )
        Results_da_z = Results_da_z.rename("Results_z")
        Results_ds_z = Results_da_z.to_dataset(dim="variables")

        # ================================================================
        # Merge all datasets for the current sample
        # ================================================================
        Results_ds_fromds = xr.merge(
            [
                Results_ds_st,
                Results_ds_stzseg,
                Results_ds_stz,
                Results_ds_zseg,
                Results_ds_z,
                Results_ds_zsegk,
            ]
        )
        Results_datasets.append(Results_ds_fromds)

    # Concatenate datasets from all samples along the 'samples' dimension
    Results_ds_total = xr.concat(Results_datasets, dim="samples")

    # ================================================================
    # Process input parameters
    # ================================================================

    # Retrieve input parameters names, split in locked and variable parameters
    variable_param_names, locked_param_names = get_param_names(config)

    # Create two dictionaries with the parameter values, one with the locked_param and one with the variable_param
    variable_param_dict = {key: param_dict[key] for key in variable_param_names}
    locked_param_dict = {key: param_dict[key] for key in locked_param_names}

    # Variable parameters: Create dataset with [param, samples] dimensions
    variable_param_da = xr.DataArray(
        list(variable_param_dict.values()),
        coords={"param": list(variable_param_dict.keys()), "samples": sample_coord},
        dims=["param", "samples"],
    )
    variable_param_ds = variable_param_da.to_dataset(dim="param")

    # Locked parameters: Extract the first value for each parameter (assumes constant values)
    locked_param_values = list(locked_param_dict.values())
    single_locked_param_values = [sublist[0] for sublist in locked_param_values]
    locked_param_single_dict = dict(
        zip(locked_param_dict.keys(), single_locked_param_values)
    )

    # Convert ndarray values to lists in locked_param_single_dict
    for key, value in locked_param_single_dict.items():
        if isinstance(value, np.ndarray):
            locked_param_single_dict[key] = value.tolist()

    locked_param = {
        key: value
        for key, value in locked_param_single_dict.items()
        if not isinstance(value, list)
    }
    locked_param_ds = xr.Dataset(locked_param)

    # Third, create a dataset from locked parameters with dim(len(parnames), npipes)
    # Param below stored in seperate datasets with pipe dimensions and x,y dimensions in the borehole
    # These datasets will further on be merged together for all parameters
    locked_param_x = {
        key: value
        for key, value in locked_param_single_dict.items()
        if isinstance(value, list) and (len(value) == len(pipes_coord))
    }

    pipe_pos = np.asarray(locked_param_x["pos"])
    r_out = locked_param_x["r_out"]

    pipe_pos_ds = xr.Dataset(
        data_vars=dict(pipe_pos=(["nPipes", "xy"], pipe_pos)),
        coords=dict(nPipes=(["nPipes"], pipes_coord)),
    )
    r_out_ds = xr.Dataset(
        data_vars=dict(r_out=(["nPipes"], r_out)),
        coords=dict(nPipes=(["nPipes"], pipes_coord)),
    )

    # Then, create dataset from locked parameters with dim(len(parnames), nlayers_k_s)
    locked_param_z_k_s = {
        key: value
        for key, value in locked_param_single_dict.items()
        if key not in locked_param and "k_s" in key
    }
    locked_param_z_k_s_da = xr.DataArray(
        list(locked_param_z_k_s.values()),
        coords={
            "param": (list(locked_param_z_k_s.keys())),
            "layer_k_s": range(len(locked_param_z_k_s["k_s"])),
        },
        dims=["param", "layer_k_s"],
    )
    locked_param_z_k_s_ds = locked_param_z_k_s_da.to_dataset(dim="param")

    # Ceate dataset from locked parameters with dim(len(parnames), nlayers_k_g)
    locked_param_z_k_g = {
        key: value
        for key, value in locked_param_single_dict.items()
        if key not in locked_param and "k_g" in key
    }
    locked_param_z_k_g_da = xr.DataArray(
        list(locked_param_z_k_g.values()),
        coords={
            "param": (list(locked_param_z_k_g.keys())),
            "layer_k_g": range(len(locked_param_z_k_g["k_g"])),
        },
        dims=["param", "layer_k_g"],
    )
    locked_param_z_k_g_ds = locked_param_z_k_g_da.to_dataset(dim="param")

    # Create dataset from locked parameters with dim(len(parnames), nlayers_Tg)
    locked_param_z_Tg = {
        key: value
        for key, value in locked_param_single_dict.items()
        if key not in locked_param and "Tg" in key
    }

    if "Tg" in locked_param_z_Tg:
        locked_param_z_Tg_da = xr.DataArray(
            list(locked_param_z_Tg.values()),
            coords={
                "param": (list(locked_param_z_Tg.keys())),
                "layer_Tg": range(len(locked_param_z_Tg["Tg"])),
            },
            dims=["param", "layer_Tg"],
        )
        locked_param_z_Tg_ds = locked_param_z_Tg_da.to_dataset(dim="param")
    else:
        locked_param_z_Tg_ds = None

    # ==================================================================
    # Merge different results and parameter dataset and convert to h5 files
    # ==================================================================
    # Merge datasets, excluding None values
    datasets_to_merge = [
        ds
        for ds in [
            variable_param_ds,
            locked_param_ds,
            pipe_pos_ds,
            r_out_ds,
            locked_param_z_k_s_ds,
            locked_param_z_k_g_ds,
            locked_param_z_Tg_ds,
        ]
        if ds
    ]
    param_ds_fromds = xr.merge(datasets_to_merge)

    # ================================================================
    # Save datasets to HDF5 file
    # ================================================================
    results_file = outpath.with_name(outpath.name + "_MC.h5")

    Results_ds_total.to_netcdf(results_file, group="results", engine="h5netcdf")
    param_ds_fromds.to_netcdf(
        results_file, group="parameters", engine="h5netcdf", mode="a"
    )

    return


def apply_smoothing(
    df: pd.DataFrame,
    column: str,
    smoothing: int | str | None = None,
    outdir: Path | None = None,
    prefix: str = "data",
) -> pd.DataFrame:
    """
    Apply smoothing to a timeseries column in a dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe (must contain `column`, may contain `local_time`).
    column : str
        Column name to smooth (e.g. "m_flow" or "Q").
    smoothing : int | str | None
        - int: rolling average window (in samples, e.g. hours).
        - "D": daily average (requires `local_time`).
        - "M": monthly average (requires `local_time`).
        - "none" or None: no smoothing.
    outdir : Path, optional
        Directory to save smoothed CSV (for "D" or "M").
    prefix : str
        Prefix for the output filename ("flow" or "load").

    Returns
    -------
    pd.DataFrame
        DataFrame with smoothed column.

    Raises
    ------
    ValueError
        If `smoothing` is "D" or "M" and `local_time` column is missing.
        If `smoothing` is an unsupported string.
    """
    if smoothing is None or str(smoothing).lower() == "none":
        return df  # nothing to do

    df = df.copy()

    # Rolling smoothing by numeric window
    if isinstance(smoothing, int):
        df[column] = (
            df[column].rolling(window=smoothing, min_periods=1).mean().ffill().bfill()
        )
        return df

    # Daily / Monthly smoothing → requires local_time
    if isinstance(smoothing, str):
        if "local_time" not in df.columns:
            raise ValueError(
                f"Smoothing='{smoothing}' requires a 'local_time' column in the input table."
            )

        df["date"] = pd.to_datetime(df["local_time"], format="mixed", dayfirst=True)
        df["day"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year

        if smoothing.upper() == "M":
            df[column] = df[column].groupby(df["month"]).transform("mean")
            if outdir:
                df.to_csv(outdir / f"{prefix}_monthly.csv", index=False)

        elif smoothing.upper() == "D":
            df[column] = (
                df[column]
                .groupby([df["year"], df["month"], df["day"]])
                .transform("mean")
            )
            if outdir:
                df.to_csv(outdir / f"{prefix}_daily.csv", index=False)

        else:
            raise ValueError(
                f"Unsupported smoothing option '{smoothing}'. "
                "Use int (hours), 'D' (daily), 'M' (monthly), or None."
            )

    return df
