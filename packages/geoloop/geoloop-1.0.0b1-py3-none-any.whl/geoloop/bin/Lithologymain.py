from pathlib import Path

import numpy as np
import xarray as xr

from geoloop.configuration import LithologyConfig, load_single_config
from geoloop.geoloopcore.strat_interpolator import StratInterpolator
from geoloop.lithology.plot_lithology import plot_lithology_and_thermcon
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


def main_lithology(config_path: str | Path) -> None:
    """
    Command-line entry point to calculate and optionally save lithology to thermal conductivity
    conversions and produce and save plots.

    Parameters
    ----------
    config_path : str
        Path to a JSON configuration file.

    Notes
    -----
    Expected JSON configuration fields (minimum):
    ``litho_k_param``
        Defines parameter distributions for stochastic evaluation.

    Returns
    -------
    None
    """
    config_dict = load_single_config(config_path)
    config = LithologyConfig(**config_dict)  # validated Pydantic object

    # initiate object for lithology_to_k simulation and create (stochastic) thermcon-depth profiles
    lithology_to_k = ProcessLithologyToThermalConductivity.from_config(config)
    if lithology_to_k.read_from_table:
        pass
    else:
        lithology_to_k.create_multi_thermcon_profiles()
        lithology_to_k.save_thermcon_sample_profiles()

    # Create plots
    # load in the h5 dataset again for convenient plotting
    lithology_h5path = lithology_to_k.out_dir / lithology_to_k.out_table

    lithology_k_ds = xr.open_dataset(
        lithology_h5path, group="litho_k", engine="h5netcdf"
    )
    # select only basecase
    lithology_k_base_case = lithology_k_ds.sel(n_samples=0)

    z = lithology_k_base_case.depth.values
    zval = lithology_k_base_case.kh_bulk.values

    zend = z
    zstart = z[:-1] * 1

    # Append 0 at the beginning of zstart
    zstart = np.insert(zstart, 0, 0)

    # Interpolate basecase thermal conductivity values
    interp_obj = StratInterpolator(zend, zval)
    kh_bulk_plotting_base_case = interp_obj.interp_plot(zstart, zend)

    # Extract max and min thermal conductivity profiles and interpolate
    kh_bulk_max = lithology_k_ds.kh_bulk.max(dim="n_samples").values
    interp_obj.zval = kh_bulk_max
    kh_bulk_plotting_max = interp_obj.interp_plot(zstart, zend)

    kh_bulk_min = lithology_k_ds.kh_bulk.min(dim="n_samples").values
    interp_obj.zval = kh_bulk_min
    kh_bulk_plotting_min = interp_obj.interp_plot(zstart, zend)

    # Create the layer cake plot
    plot_lithology_and_thermcon(
        lithology_k_base_case,
        kh_bulk_plotting_base_case,
        interp_obj,
        kh_bulk_plotting_max,
        kh_bulk_plotting_min,
        lithology_h5path,
        lithology_to_k.out_dir,
    )
