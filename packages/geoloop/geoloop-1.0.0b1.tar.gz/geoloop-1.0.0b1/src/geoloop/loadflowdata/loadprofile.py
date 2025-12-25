import numpy as np
import pandas as pd

from geoloop.configuration import LoadProfileConfig
from geoloop.utils.helpers import apply_smoothing


class LoadProfile:
    """
    Class to generate heat load profiles for simulations. Supports constant, variable, Bernier synthetic,
    or from-file time series of heat demand.

    Attributes
    ----------
    type : str
        Type of load profile: 'BERNIER', 'CONSTANT', 'VARIABLE', 'FROMFILE'.
    base : float
        Base heat load (W) for VARIABLE type.
    peak : float
        Peak heat load (W) for VARIABLE type.
    filepath : str
        Path to CSV file if FROMFILE type is used.
    outdir : str
        Directory to save processed outputs (e.g., smoothed data).
    scale : float
        Scaling factor for loads read from file.
    minQ : float
        Minimum heat load (W) when using FROMFILE type.
    minscaleflow : float
        Minimum scaling factor for flow computation.
    inputcolumn : str
        Name of the column in CSV file containing heat demand.
    smoothing : int or str, optional
        Smoothing applied to time series: int for rolling window, 'D' or 'M' for daily/monthly.
    table : pd.DataFrame
        Loaded table when using FROMFILE type.
    """

    BERNIER = "BERNIER"  # finite volume approach, can only run with run_type TIN
    CONSTANT = "CONSTANT"  # constant load, base mis
    VARIABLE = "VARIABLE"
    FROMFILE = "FROMFILE"

    def __init__(
        self,
        type,
        base=4000,
        peak=4000,
        filepath=None,
        outdir=None,
        inputdir=None,
        scale=1,
        minQ=0,
        minscaleflow=1,
        inputcolumn="heating_demand",
        smoothing=None,
    ):
        """
        Initialize the LoadProfile object.
        """
        self.type = type
        self.peak = peak
        self.base = base
        self.filepath = filepath
        self.outdir = outdir
        self.inputdir = inputdir
        self.minscaleflow = minscaleflow
        self.smoothing = smoothing
        self.inputcolumn = inputcolumn

        if self.type == LoadProfile.FROMFILE:
            self.scale = scale
            self.minQ = minQ
            self.load_data = self.getloadtable()

            # Apply smoothing if requested
            if self.smoothing is not None and str(self.smoothing).lower() != "none":
                self.load_data = apply_smoothing(
                    self.load_data,
                    column=self.inputcolumn,
                    smoothing=self.smoothing,
                    outdir=self.outdir,
                    prefix="load",
                )

    def getloadtable(self):
        """
        Load the time-variable heat demand table from CSV file.

        Returns
        -------
        pd.DataFrame
            Data frame containing the heat demand table.
        """
        load_data = pd.read_csv(self.filepath, header=3, index_col=0, parse_dates=True)
        return load_data

    def getload(self, times: np.ndarray) -> np.ndarray:
        """
        Compute heat load for given times.

        Parameters
        ----------
        times : np.ndarray
            Array of times in hours.

        Returns
        -------
        np.ndarray
            Heat load values (W) at the specified times.
        """
        if self.type == LoadProfile.BERNIER:
            return self.bernier(times)

        if self.type == LoadProfile.CONSTANT:
            return self.constant(times)

        if self.type == LoadProfile.VARIABLE:
            return self.variable(times)

        if self.type == LoadProfile.FROMFILE:
            return self.fromfile(times)

        return np.zeros_like(times)

    def getloadflow(self, times: np.ndarray, m_flow: float) -> tuple:
        """
        Compute heat load and flow_data rate, scaling flow_data based on maximum load.

        Parameters
        ----------
        times : np.ndarray
            Times in hours.
        m_flow : float
            Maximum flow_data rate for scaling.

        Returns
        -------
        tuple
            Tuple of (heat load array, scaled flow_data rate array)
        """
        load_data = self.getload(times)
        abs_load_data = np.absolute(load_data)

        # Prevent division by zero and enforce minimum flow_data
        scaleflow = np.maximum(self.minscaleflow, abs_load_data / np.max(abs_load_data))
        flow_data = scaleflow * m_flow

        return load_data, flow_data

    def variable(self, times: np.ndarray) -> np.ndarray:
        """
        Generate a variable load profile using cosine function.

        Parameters
        ----------
        times : np.ndarray
            Times in hours.

        Returns
        -------
        np.ndarray
            Load values (W).
        """
        peak_load = self.peak
        base_load = self.base

        arg = 2 * np.pi * times / 8760
        load_data = (peak_load - base_load) * np.cos(arg) + base_load
        return load_data

    def constant(self, times: np.ndarray) -> np.ndarray:
        """
        Generate a constant load profile.

        Parameters
        ----------
        times : np.ndarray
            Times in hours.

        Returns
        -------
        np.ndarray
            Constant load array (W).
        """
        load_data = times * 0 + self.peak
        return load_data

    def bernier(self, times: np.ndarray) -> np.ndarray:
        """
        Generate synthetic load profile of Bernier et al. (2004).

        Parameters
        ----------
        times : np.ndarray
            Times in hours.

        Returns
        -------
        np.ndarray
            Synthetic Bernier load array (W).
        """
        A = 2000.0
        B = 2190.0
        C = 80.0
        D = 2.0
        E = 0.01
        F = 0.0
        G = 0.95

        pi = np.pi

        # Start with base Bernier series function
        func = (168.0 - C) / 168.0

        # Sum harmonics
        for i in [1, 2, 3]:
            func += (
                1.0
                / (i * pi)
                * (np.cos(C * pi * i / 84.0) - 1.0)
                * (np.sin(pi * i / 84.0 * (times - B)))
            )

        # Modulate with seasonal and daily terms
        func = (
            func
            * A
            * np.sin(pi / 12.0 * (times - B))
            * np.sin(pi / 4380.0 * (times - B))
        )

        # Apply Bernier sign adjustments
        load_data = (
            func
            + (-1.0) ** np.floor(D / 8760.0 * (times - B)) * abs(func)
            + E
            * (-1.0) ** np.floor(D / 8760.0 * (times - B))
            / np.sign(np.cos(D * pi / 4380.0 * (times - F)) + G)
        )

        return -load_data

    def fromfile(self, times: np.ndarray) -> np.ndarray:
        """
        Interpolate heat load from CSV table.

        Parameters
        ----------
        times : np.ndarray
            Times in hours.

        Returns
        -------
        np.ndarray
            Interpolated and scaled heat load array (W).
        """
        heatdemand = np.asarray(self.load_data[self.inputcolumn])
        hours = np.arange(len(heatdemand))

        # Periodic interpolation across full year
        load_data = np.interp(times, hours, heatdemand, period=(len(hours)))

        # Apply kW→W (1000x) and user scale
        scaled_load_data = load_data * 1000 * self.scale

        if self.minQ >= 0:
            scaled_load_data = np.where(
                scaled_load_data >= 0,
                np.maximum(self.minQ, scaled_load_data),
                np.minimum(-self.minQ, scaled_load_data),
            )
        else:
            # Replace with average if minQ flag is negative
            average_scaled_load_data = np.average(scaled_load_data)
            scaled_load_data = scaled_load_data * 0 + average_scaled_load_data

        return scaled_load_data

    @classmethod
    def from_config(cls, config: LoadProfileConfig) -> "LoadProfile":
        """
        Create LoadProfile instance from configuration dictionary.

        Parameters
        ----------
        config : LoadProfileConfig
            Configuration object containing load profile type and parameters.

        Returns
        -------
        LoadProfile
            Initialized load profile object.
        """
        if config.lp_type == LoadProfile.CONSTANT:
            base = config.lp_base
            peak = base
            return cls(config.lp_type, base=base, peak=peak, outdir=config.lp_outdir)

        elif config.lp_type == LoadProfile.VARIABLE:
            return cls(
                config.lp_type,
                base=config.lp_base,
                peak=config.lp_peak,
                minscaleflow=config.lp_minscaleflow,
                outdir=config.lp_outdir,
            )

        elif config.lp_type == LoadProfile.FROMFILE:
            inputcolumn = getattr(config, "lp_inputcolumn", "heating_demand")
            smoothing = getattr(config, "lp_smoothing", None)
            return cls(
                config.lp_type,
                filepath=config.lp_filepath,
                outdir=config.lp_outdir,
                inputdir=config.lp_inputdir,
                scale=config.lp_scale,
                minQ=config.lp_minQ,
                minscaleflow=config.lp_minscaleflow,
                inputcolumn=inputcolumn,
                smoothing=smoothing,
            )

        else:
            return cls(config.lp_type)
