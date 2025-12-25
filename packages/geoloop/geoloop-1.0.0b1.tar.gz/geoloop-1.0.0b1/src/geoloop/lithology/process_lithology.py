import math
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from geoloop.configuration import LithologyConfig
from geoloop.constants import lithology_properties_xlsx
from geoloop.geoloopcore.strat_interpolator import TgInterpolator

# TODO: save the config paramters (error and scaling factors) in the thermcon h5 file that now only stores the results


class ThermalConductivityCalculator:
    """
    A class to calculate subsurface thermal conductivity and porosity based on lithological and thermal parameters.

    Attributes
    ----------
    phi0 : float
        Porosity at the surface.
    kv_phi0_20 : float
        Thermal conductivity at 20°C (W/mK).
    sorting_factor : float
        Sorting factor, describing the degree of sorting in sediments.
    anisotropy : float
        Anisotropy factor, describing the anisotropy in sediments.
    c_p : float
        Specific heat capacity (J/kgK).
    rho : float
        Density (kg/m³).
    k_athy : float
        Compaction constant, used in the porosity-depth relation.
    """

    def __init__(
        self,
        phi0: float,
        kv_phi0_20: float,
        sorting_factor: float,
        anisotropy: float,
        c_p: float,
        rho: float,
        k_athy: float,
    ) -> None:
        self.phi0 = phi0
        self.kv_phi0_20 = kv_phi0_20
        self.sorting_factor = sorting_factor
        self.anisotropy = anisotropy
        self.c_p = c_p
        self.rho = rho
        self.k_athy = k_athy

    def calculate_porosity(self, depth: float) -> float:
        """
        Calculates porosity at a given depth using Athy's exponential compaction model.

        Parameters
        ----------
        depth : float
            Depth in meters.

        Returns
        -------
        float
            Porosity (fraction between 0 and 1).
        """
        phi_base = 0
        phi = phi_base + (self.phi0 - phi_base) * math.exp(-self.k_athy * depth * 0.001)

        return phi

    def calculate_k_compaction_correction(self, phi: float) -> float:
        """
        Apply a compaction correction to the reference vertical thermal conductivity at phi 0.

        Parameters
        ----------
        phi : float
            Porosity (fraction).

        Returns
        -------
        float
            Corrected vertical thermal conductivity at 20°C (W/m·K).
        """

        phi_factor = phi / self.phi0
        kv_phi_20 = self.kv_phi0_20 * math.pow(self.sorting_factor, phi_factor)

        return kv_phi_20

    def calculate_kh_rock_matrix(
        self, temperature_top: float, temperature_base: float, phi: float
    ) -> float:
        """
        Estimate the horizontal rock-matrix thermal conductivity (dimensionless kh_matrix)
        using an empirical formula that depends on compaction-corrected conductivities
        and temperature.

        Parameters
        ----------
        temperature_top : float
            Temperature at the top of the segment (°C).
        temperature_base : float
            Temperature at the base of the segment (°C).
        phi : float
            Effective porosity for the segment.

        Returns
        -------
        float
            Estimated matrix conductivity parameter kh_matrix used in bulk mixing.
        """
        # set default thermal conductivity value representative for basement lithology
        kh_matrix = 1.6

        temperature_average = 0.5 * (temperature_top + temperature_base)

        if self.sorting_factor != -1:
            # Calculate vertical bulk conductivity after compaction correction, given the porosity
            kv_phi_20 = self.calculate_k_compaction_correction(phi)

            # Calculate horizontal bulk conductivity based on corrected vertical bulk thermal conducitivty
            kh_phi_20 = 0.5 * (
                self.kv_phi0_20 + (2 * self.kv_phi0_20 * self.anisotropy) - kv_phi_20
            )

            # Calculate horizontal matrix conductivity
            kh_matrix = (358 * ((1.0227 * kh_phi_20) - 1.882)) * (
                (1 / (temperature_average + 273)) - 0.00068
            ) + 1.84
        else:
            print(
                "Error: Basement lithology used for sediments, or no sorting factor applied"
            )

        return kh_matrix

    def calculate_k_water(self, temperature_base: float) -> float:
        """
        Calculates the thermal conductivity of water at the given temperature.

        Parameters
        ----------
        temperature_base : float
            Temperature in °C at the base of the segment.

        Returns
        -------
        float
            Thermal conductivity of water (W/m·K).
        """
        temperature_base = min(temperature_base, 120)

        k_water = (
            5.62
            + (0.02022 * temperature_base)
            - (0.0000823 * (temperature_base * temperature_base))
        ) * 0.1

        return k_water

    def calculate_kh_bulk(
        self, temperature_base: float, kh_matrix: float, phi: float
    ) -> float:
        """
        Compute bulk horizontal thermal conductivity by combining matrix and pore fluid.

        Uses a geometric mixing law: k_bulk = KxRM^(1-phi) * kw^(phi).

        Parameters
        ----------
        temperature_base : float
            Temperature at segment base (°C).
        kh_matrix : float
            Horizontal thermal conductivity of the rock matrix (W/mK).
        phi : float
            Porosity (fraction).

        Returns
        -------
        float
            Bulk horizontal thermal conductivity (W/m·K).
        """
        k_water = self.calculate_k_water(temperature_base)
        phi_rev = 1 - phi
        kh_bulk = math.pow(kh_matrix, phi_rev) * (math.pow(k_water, phi))

        return kh_bulk


class ThermalConductivityResults:
    """
    Class that stores the results of thermal conductivity calculations, including depth profiles of lithology fraction,
    porosity, and bulk thermal conductivity.

    Attributes
    ----------
    sample : int
        Sample number or identifier.
    depth : np.ndarray
        Array of depth values corresponding to the intervals with different subsurface properties.
    lithology_a_fraction : np.ndarray
        Array of lithology fraction values for the first lithology in each depth-interval.
    phi : np.ndarray
        Array of porosity values corresponding to the depth intervals.
    kx : np.ndarray
        Array of bulk thermal conductivity values corresponding to the depth intervals.
    """

    def __init__(self, sample, depth, lithology_a_fraction, phi, kh_bulk):
        self.sample = sample
        self.depth = depth
        self.lithology_a_fraction = lithology_a_fraction
        self.phi = phi
        self.kh_bulk = kh_bulk


class ProcessLithologyToThermalConductivity:
    """
    Handles the calculation procedure of subsurface thermal conductivities based on lithological data.

    Attributes
    ----------
    lithology_props_df : pd.DataFrame
        DataFrame containing physical properties and thermal parameters for different lithologies, adopted from Hantschel & Kauerauf (2009).
    borehole_df : pd.DataFrame
        DataFrame containing borehole lithological description (depth and lithology data).
    Tg : float
        Surface temperature (in °C).
    Tgrad : float
        Average geothermal gradient (in °C/km).
    z_Tg : float
        Depth at which the (sub)surface temperature `Tg` is measured.
    phi_scale : float
        Scaling factor for porosity over depth. Induces uniform variation in porosity values during sampling of different porosity-depth profiles in a stochastic (MC) simulation.
    lithology_scale : float
        Scaling factor for lithology fraction over depth. Induces uniform variation in lithology fraction values during sampling of different porosity-depth profiles in a stochastic (MC) simulation.
    lithology_error : float
        Depth-independent error applied to lithology fraction during sampling of different porosity-depth profiles in a stochastic (MC) simulation.
    nsamples : int
        Number of thermal conductivity-depth profiles to generate and store.
    basecase : bool
        Whether to run the simulation in "base case" mode. In base case mode, no scaling and/or error values are applied to the porosity and lithology profiles in the thermal conductivity calculation.
    out_dir : str
        Path to the directory where files with subsurface properties are saved.
    out_table : str
        Name of the file (.h5) for storing the table with subsurface properties.
    read_from_table : bool
        Whether to read precomputed results of subsurface thermal conductivities from an existing file or compute real-time.

    Raises
    ------
    ValueError
        If any required input is missing or incompatible.
    """

    def __init__(
        self,
        borehole_df: pd.DataFrame,
        Tg: float,
        Tgrad: float,
        z_Tg: float,
        phi_scale: float,
        lithology_scale: float,
        lithology_error: float,
        nsamples: int,
        basecase: bool,
        out_dir: Path,
        out_table: str,
        read_from_table: bool,
    ) -> None:
        # Read lithology properties reference table (Excel)
        self.lithology_props_df = pd.read_excel(lithology_properties_xlsx)

        self.borehole_df = borehole_df
        self.lithology_props_dict = self.create_lithology_props_dict()
        self.borehole_lithology_props = (
            self.create_borehole_lithology_props_classification()
        )

        self.Tg = Tg
        self.Tgrad = Tgrad
        self.z_Tg = z_Tg
        self.interpolator_Tg = TgInterpolator(self.z_Tg, self.Tg, self.Tgrad)

        # Sampling/stochastic options
        self.phi_scale = phi_scale
        self.lithology_scale = lithology_scale
        self.lithology_error = lithology_error
        self.nsamples = nsamples
        self.basecase = basecase
        if self.basecase:
            self.nsamples = 1
        self.samples = np.arange(self.nsamples)

        # Directory paths and output file name
        self.out_dir = out_dir
        self.out_table = out_table
        self.read_from_table = read_from_table

    def create_lithology_props_dict(self) -> dict[int, "ThermalConductivityCalculator"]:
        """
        Creates a dictionary of physical and thermal properties for different lithologies, in the correct format for
        the thermal conductivity calculations. Property values are adopted from the Hantschel & Kauerauf (HK) database.

        Dictionary maps the physical and thermal properties from the HK classification to the corresponding
        variables in the thermal conductivity calculations.

        Returns
        -------
        dict
            Mapping `lithology ID -> ThermalConductivityCalculator`.
        """

        lithology_props_dict = {}
        for _, row in self.lithology_props_df.iterrows():
            obj_key = row["ID"]
            # map columns in HK table to constructor arguments (preserve original semantics)
            obj_values = {
                "kv_phi0_20": row["K [W/mK]"],
                "anisotropy": row["anisotropy"],
                "c_p": row["cp [J/kgK]"],
                "sorting_factor": row["sorting (-1 = 0 sorting)"],
                "rho": row["rho [kg/m3]"],
                "phi0": row["phi0 [%/100]"],
                "k_athy": row["k_athy (compaction par.) [1/km]"],
            }

            # create calculator instance
            lithology_props_dict[obj_key] = ThermalConductivityCalculator(**obj_values)

        return lithology_props_dict

    def create_borehole_lithology_props_classification(self) -> pd.DataFrame:
        """
        Merge borehole lithology sheet with HK classification table and create
        columns with HK IDs for lithology a and b.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing lithological classification along borehole, with thermal properties and added columns 'Lithology_ID_a' and 'Lithology_ID_b'.
        """
        # Merge borehole description data with HK classification for formation along borehole
        # Merge for lithology a
        borehole_lithology_a = pd.merge(
            self.borehole_df,
            self.lithology_props_df[["Lithology", "ID"]],
            left_on="Lithology_a",
            right_on="Lithology",
            how="left",
        )
        borehole_lithology_a.rename(columns={"ID": "Lithology_ID_a"}, inplace=True)
        borehole_lithology_a = borehole_lithology_a.drop("Lithology", axis=1)

        # Merge for lithology b
        borehole_lithology_ab = pd.merge(
            borehole_lithology_a,
            self.lithology_props_df[["Lithology", "ID"]],
            left_on="Lithology_b",
            right_on="Lithology",
            how="left",
        )
        borehole_lithology_ab.rename(columns={"ID": "Lithology_ID_b"}, inplace=True)
        borehole_lithology_ab = borehole_lithology_ab.drop("Lithology", axis=1)

        return borehole_lithology_ab

    @classmethod
    def from_config(
        cls, config: LithologyConfig
    ) -> "ProcessLithologyToThermalConductivity":
        """
        Create a ProcessLithologyToThermalConductivity instance from a configuration dict.

        Parameters
        ----------
        config : LithologyConfig
            Configuration dictionary with required keys.

        Returns
        -------
        ProcessLithologyToThermalConductivity
            Initialized instance.
        """

        borehole_path = config.borehole_lithology_path
        borehole_df = pd.read_excel(
            borehole_path, sheet_name=config.borehole_lithology_sheetname
        )

        return cls(
            borehole_df=borehole_df,
            Tg=config.Tg,
            Tgrad=config.Tgrad,
            z_Tg=config.z_Tg,
            phi_scale=config.phi_scale,
            lithology_scale=config.lithology_scale,
            lithology_error=config.lithology_error,
            nsamples=config.n_samples,
            basecase=config.basecase,
            out_dir=config.out_dir_lithology,
            out_table=config.out_table,
            read_from_table=config.read_from_table,
        )

    def create_single_thermcon_profile(
        self, isample: int
    ) -> ThermalConductivityResults:
        """
        Calculates depth-dependent subsurface properties, for a specific sample of the loaded or calculated subsurface
        properties table.

        Parameters
        ----------
        isample : int
            Sample index (0 is basecase).

        Returns
        -------
        ThermalConductivityResults
            Object with arrays depth, lithology fraction, porosity and kh_bulk.
        """

        borehole_lithology_df = self.borehole_lithology_props
        depth = np.asarray(borehole_lithology_df["Depth"])

        # map HK IDs to calculators (lists aligned with depth)
        lithology_to_k_a = [
            self.lithology_props_dict[litho]
            for litho in borehole_lithology_df["Lithology_ID_a"]
        ]
        lithology_to_k_b = [
            self.lithology_props_dict[litho]
            for litho in borehole_lithology_df["Lithology_ID_b"]
        ]

        # Lists to store bulk thermal conductivity values for each version
        kh_bulk = []
        phi_samples = []
        lithology_a_fraction_samples = []

        # Choose whether to sample the depth-scaling error or use basecase lithology fractions
        if self.basecase or (isample == 0):
            # For single run use basecase porosity and lithology fraction
            lithology_a_fraction = self.borehole_lithology_props["Lithology_a_fraction"]
            phi_scale_error = 0
        else:
            # Else sample within scaling error
            lithology_a_fraction = np.clip(
                np.random.uniform(
                    self.borehole_lithology_props["Lithology_a_fraction"]
                    - self.lithology_scale,
                    self.borehole_lithology_props["Lithology_a_fraction"]
                    + self.lithology_scale,
                ),
                a_min=0,
                a_max=1,
            )

            # Implement a uniform error for phi
            phi_scale_error = np.random.uniform(-self.phi_scale, self.phi_scale)

        # For every depth segment
        for i in range(len(depth)):
            # Choose whether to sample the depth-random error or use basecase lithology fractions
            if self.basecase or (isample == 0):
                # For single run use basecase lithology fraction
                lithology_a_fraction_sampled = lithology_a_fraction[i]
            else:
                # Sample values for every depth segment within the error ranges for lithology
                lithology_a_fraction_sampled = np.clip(
                    np.random.uniform(
                        lithology_a_fraction[i] - self.lithology_error,
                        lithology_a_fraction[i] + self.lithology_error,
                    ),
                    a_min=0,
                    a_max=1,
                )

            # Calculate porosity per lithology with uniform error applied
            phi_litho_a = np.clip(
                lithology_to_k_a[i].calculate_porosity(depth[i]) + phi_scale_error,
                a_min=0,
                a_max=1,
            )
            phi_litho_b = np.clip(
                lithology_to_k_b[i].calculate_porosity(depth[i]) + phi_scale_error,
                a_min=0,
                a_max=1,
            )

            # Calculate effective porosity for the combined lithology, weighted by lithology fraction
            phi_sampled = (phi_litho_a * lithology_a_fraction_sampled) + (
                phi_litho_b * (1 - lithology_a_fraction_sampled)
            )

            # Append sampled values to lists
            phi_samples.append(phi_sampled)
            lithology_a_fraction_samples.append(lithology_a_fraction_sampled)

            # Calculate temperature for the current depth segment
            if i == 0:
                temperature_top = self.interpolator_Tg.getTg(depth[0])
            else:
                temperature_top = self.interpolator_Tg.getTg(depth[i - 1])
            temperature_base = self.interpolator_Tg.getTg(depth[i])

            # Calculate horizontal matrix thermal conductivity of lithology a and lithology b
            kh_matrix_lithology_a = lithology_to_k_a[i].calculate_kh_rock_matrix(
                temperature_top, temperature_base, phi_sampled
            )
            kh_matrix_lithology_b = lithology_to_k_b[i].calculate_kh_rock_matrix(
                temperature_top, temperature_base, phi_sampled
            )

            # geometric mixing by lithology fraction (geometric mean)
            if lithology_a_fraction_sampled == 0:
                kh_matrix_segment = kh_matrix_lithology_b
            elif lithology_a_fraction_sampled == 1:
                kh_matrix_segment = kh_matrix_lithology_a
            else:
                kh_matrix_segment = math.pow(
                    kh_matrix_lithology_a, lithology_a_fraction_sampled
                ) * (
                    math.pow(kh_matrix_lithology_b, (1 - lithology_a_fraction_sampled))
                )

            # Calculate horizontal bulk thermal conductivity from porosity and combined matrix thermal conductivity
            kh_bulk_segment = lithology_to_k_a[i].calculate_kh_bulk(
                temperature_base, kh_matrix_segment, phi_sampled
            )

            # Append the calculated value of the bulk thermal conductivity to the list for each segment
            kh_bulk.append(kh_bulk_segment)

        # Convert lists to numpy arrays
        kh_bulk = np.asarray(kh_bulk)
        lithology_a_fraction_samples = np.asarray(lithology_a_fraction_samples)
        phi_samples = np.asarray(phi_samples)

        # Create and return a ThermalConductivityResults object
        k_calc_results = ThermalConductivityResults(
            isample, depth, lithology_a_fraction_samples, phi_samples, kh_bulk
        )

        return k_calc_results

    def create_multi_thermcon_profiles(self) -> None:
        """
        Create thermal conductivity profiles for all requested (stochastic) samples (or read from .h5 file).

        If `read_from_table` is True, read data from `out_dir/out_table`. Otherwise compute samples in run time.

        Returns
        -------
        None (results are stored internally).
        """
        if self.read_from_table:
            path = self.out_dir / self.out_table
            lithology_k_ds = xr.open_dataset(path, group="litho_k", engine="h5netcdf")
            kh_bulk_da = lithology_k_ds["kh_bulk"]

            kh_bulk_results = []
            for sample in range(len(kh_bulk_da.isel({"depth": 0}))):
                depth = kh_bulk_da.depth.values
                kh_bulk = kh_bulk_da.isel({"n_samples": sample}).values
                kh_bulk_i = ThermalConductivityResults(
                    depth=depth,
                    kh_bulk=kh_bulk,
                    sample=sample,
                    phi=None,
                    lithology_a_fraction=None,
                )
                kh_bulk_results.append(kh_bulk_i)

        else:
            kh_bulk_results = []
            for s in self.samples:
                ssres = self.create_single_thermcon_profile(int(s))
                kh_bulk_results.append(ssres)

        self.kh_bulk_results = kh_bulk_results

    def get_thermcon_sample_profile(self, isample: int) -> ThermalConductivityResults:
        """
        Retrieves depth-dependent subsurface properties for a specific sample in the precomputed table.

        Parameters
        ----------
        isample : int
            Sample index (use -1 to request basecase which is index 0).

        Returns
        -------
        ThermalConductivityResults
            Results container for the requested sample.
        """
        if self.basecase | isample == -1:
            return self.kh_bulk_results[0]
        else:
            return self.kh_bulk_results[isample]

    def save_thermcon_sample_profiles(self) -> None:
        """
        Save the computed sample profiles to a NetCDF (.h5) file using xarray.

        The dataset will contain variables:
        - kh_bulk (depth x n_samples)
        - phi (depth x n_samples)
        - lithology_a_fraction (depth x n_samples)

        Returns
        -------
        None (results are saved directly to the specified output file).
        """
        # build empty dataset and coordinates
        if not self.kh_bulk_results:
            raise RuntimeError(
                "No results available to save. Run create_multi_thermcon_profiles() first."
            )

        lithology_k_ds = xr.Dataset()

        # Add 'depth' coordinate
        depth_values = self.get_thermcon_sample_profile(
            0
        ).depth  # Assuming all samples have the same depth values
        lithology_k_ds = lithology_k_ds.assign_coords(depth=depth_values)

        # Add lithology a and b
        lithology_k_ds["lithology_a"] = xr.DataArray(
            self.borehole_df["Lithology_a"],
            dims=("depth"),
            coords={"depth": depth_values},
        )
        lithology_k_ds["lithology_b"] = xr.DataArray(
            self.borehole_df["Lithology_b"],
            dims=("depth"),
            coords={"depth": depth_values},
        )

        for isample in range(self.nsamples):
            ssres = self.get_thermcon_sample_profile(isample)

            # Create variables if they don't exist
            if "kh_bulk" not in lithology_k_ds:
                lithology_k_ds["kh_bulk"] = xr.DataArray(
                    np.nan,
                    dims=("depth", "n_samples"),
                    coords={"depth": depth_values, "n_samples": range(self.nsamples)},
                )
            if "phi" not in lithology_k_ds:
                lithology_k_ds["phi"] = xr.DataArray(
                    np.nan,
                    dims=("depth", "n_samples"),
                    coords={"depth": depth_values, "n_samples": range(self.nsamples)},
                )
            if "lithology_a_fraction" not in lithology_k_ds:
                lithology_k_ds["lithology_a_fraction"] = xr.DataArray(
                    np.nan,
                    dims=("depth", "n_samples"),
                    coords={"depth": depth_values, "n_samples": range(self.nsamples)},
                )

            # Assign variables to the dataset
            lithology_k_ds["kh_bulk"].loc[{"n_samples": isample}] = ssres.kh_bulk
            lithology_k_ds["phi"].loc[{"n_samples": isample}] = ssres.phi
            lithology_k_ds["lithology_a_fraction"].loc[{"n_samples": isample}] = (
                ssres.lithology_a_fraction
            )

        # Save results to HDF5 file using xarray
        out_path = self.out_dir / self.out_table
        lithology_k_ds.to_netcdf(out_path, group="litho_k", engine="h5netcdf")

    def get_start_end_depths(self):
        """
        Retrieves the start and end depths for all intervals with different subsurface properties.

        Returns
        -------
        (zstart, zend) : tuple of numpy arrays
            zstart: start depth of each segment (first element 0)
            zend: end depth array taken from results
        """
        if not self.kh_bulk_results:
            raise RuntimeError(
                "No results available. Run create_multi_thermcon_profiles() first."
            )
        zend = self.kh_bulk_results[0].depth
        zstart = np.roll(zend, 1)
        zstart[0] = 0
        return zstart, zend
