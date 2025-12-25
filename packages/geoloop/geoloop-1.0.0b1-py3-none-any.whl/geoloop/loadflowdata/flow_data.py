from pathlib import Path

import numpy as np
import pandas as pd

from geoloop.configuration import FlowDataConfig
from geoloop.utils.helpers import apply_smoothing


class FlowData:
    """
    Class to handle flow rate data for simulations, either as constant, variable, or from a CSV file.

    This class provides time-dependent flow data (in kg/s) for simulations. It supports
    three types of flow profiles:

    - CONSTANT: fixed flow rate over time.
    - VARIABLE: synthetic sinusoidal variation over the year.
    - FROMFILE: flow rates read from a CSV file, optionally smoothed.

    Parameters
    ----------
    type : str
        Flow type: "CONSTANT", "VARIABLE", or "FROMFILE".
    base_flow : float, optional
        Base flow rate (kg/s), default is 1.0.
    peak_flow : float, optional
        Peak flow rate (kg/s) for VARIABLE type, default is 1.0.
    filepath : str, optional
        Path to CSV file with flow data, required for FROMFILE type.
    outdir : str, optional
        Directory where smoothed CSVs are saved.
    scale : float, optional
        Scaling factor for flow data, default is 1.0.
    inputcolumn : str, optional
        Column name in CSV with flow data, default is "m_flow".
    smoothing : int or str, optional
        Smoothing for FROMFILE data:
        - int: rolling average window in samples.
        - "D": daily average (requires 'local_time' column).
        - "M": monthly average (requires 'local_time' column).
        - None or "none": no smoothing.

    """

    CONSTANT = "CONSTANT"
    VARIABLE = "VARIABLE"
    FROMFILE = "FROMFILE"

    def __init__(
        self,
        type: str,
        base_flow: float = 1.0,
        peak_flow: float = 1.0,
        filepath: str | Path | None = None,
        outdir: str | Path | None = None,
        inputdir: str | Path | None = None,
        scale: float = 1.0,
        inputcolumn: str = "m_flow",
        smoothing: int | str | None = None,
    ) -> None:
        """
        Initialize the FlowData object.
        """
        self.type = type
        self.base_flow = base_flow
        self.peak_flow = peak_flow
        self.filepath = filepath
        self.outdir = outdir
        self.inputdir = inputdir
        self.scale = scale
        self.inputcolumn = inputcolumn
        self.smoothing = smoothing

        # Load CSV if needed
        if self.type == FlowData.FROMFILE:
            self.flow_data = pd.read_csv(filepath)
            if self.smoothing is not None:
                self.flow_data = apply_smoothing(
                    self.flow_data,
                    column=self.inputcolumn,
                    smoothing=self.smoothing,
                    outdir=self.outdir,
                    prefix="flow",
                )

    def getflow(self, x: np.ndarray) -> np.ndarray:
        """
        Return flow values at specified times.

        Parameters
        ----------
        x : array-like
            Array of time points in hours at which to get flow values.

        Returns
        -------
        np.ndarray
            Flow rates (kg/s) (interpolated or analytically computed) at the requested time points.
        """
        if self.type == FlowData.CONSTANT:
            return np.ones_like(x) * self.peak_flow

        elif self.type == FlowData.VARIABLE:
            # One-year sinusoidal fluctuation (period = 8760 hours)
            arg = 2 * np.pi * x / 8760
            return (self.peak_flow - self.base_flow) / 2 * (
                1 + np.cos(arg)
            ) + self.base_flow

        elif self.type == FlowData.FROMFILE:
            flowdata = np.asarray(self.flow_data[self.inputcolumn])
            hours = np.arange(len(flowdata))
            return np.interp(x, hours, flowdata, period=len(hours)) * self.scale

        else:
            raise ValueError(f"Unsupported FlowData type: {self.type}")

    @classmethod
    def from_config(cls, config: FlowDataConfig) -> "FlowData | None":
        """
        Create a FlowData instance from a configuration dictionary.

        The configuration dictionary must include keys defining the flow type
        and file paths if applicable.

        Parameters
        ----------
        config : FlowDataConfig
            Configuration object with keys.

        Returns
        -------
        FlowData
            Initialized FlowData object.
        """
        if config.fp_type == "CONSTANT":
            return cls(
                config.fp_type, peak_flow=config.fp_peak, outdir=config.fp_outdir
            )

        elif config.fp_type == "VARIABLE":
            return cls(
                config.fp_type,
                base_flow=config.fp_base,
                peak_flow=config.fp_peak,
                outdir=config.fp_outdir,
            )

        elif config.fp_type == "FROMFILE":
            return cls(
                config.fp_type,
                filepath=config.fp_filepath,
                outdir=config.fp_outdir,
                inputdir=config.fp_inputdir,
                scale=config.fp_scale,
                inputcolumn=config.fp_inputcolumn,
                smoothing=config.fp_smoothing,
            )
        else:
            print("No type of flow data profile not supported")
