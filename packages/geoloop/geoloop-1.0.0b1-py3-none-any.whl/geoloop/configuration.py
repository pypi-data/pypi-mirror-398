import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, model_validator


class LithologyConfig(BaseModel):
    """
    Configuration object for the lithology module.

    This class defines the input parameters required for processing borehole
    lithology data, scaling lithology thermal properties, and generating
    realizations used in BHE simulations.

    Attributes
    ----------
    config_file_path : str or Path
        Path to the JSON configuration file that created this object.
    out_dir_lithology : str or Path
        Directory where lithology outputs will be written.
    borehole_lithology_path : str or Path
        Path to the Excel or CSV file containing lithology data.
    borehole_lithology_sheetname : str
        Name of the sheet inside the Excel file that contains lithologic data.
    out_table : str
        Filename for the processed lithology table output.
    read_from_table : bool
        If True, bypass input processing and read from an existing table with thermal conductivity data.
    Tg : int or list of int
        Surface temperature if int, or subsurface temperature values over depth if list.
    Tgrad : int
        Geothermal gradient in °C/m.
    z_Tg : int or list of int
        Depths at which Tg values apply if list.
    phi_scale : float
        Scaling factor over depth for porosity.
    lithology_scale : float
        Depth scaling factor for lithology fractions.
    lithology_error : float
        Random noise scaling applied to lithology fractions.
    basecase : bool
        If True, disables stochasticity in subsurface properties and returns a deterministic profile.
    n_samples : int
        Number of stochastic realizations to generate.
    """

    config_file_path: str | Path
    out_dir_lithology: str | Path
    input_dir_lithology: str | Path
    borehole_lithology_path: str | Path
    borehole_lithology_sheetname: str
    out_table: str
    read_from_table: bool
    Tg: int | list
    Tgrad: int
    z_Tg: int | list
    phi_scale: float
    lithology_scale: float
    lithology_error: float
    basecase: bool
    n_samples: int

    # Resolve paths
    @model_validator(mode="after")
    def process_config_paths(self):
        """
        Resolve relative paths in the configuration and ensure output directories exist.

        Returns
        -------
        LithologyConfig
            Model with absolute, validated paths.
        """
        if not isinstance(self.config_file_path, Path):
            self.config_file_path = Path(self.config_file_path).resolve()

        base_dir_lithology = self.config_file_path.parent

        if not isinstance(self.borehole_lithology_path, Path):
            self.borehole_lithology_path = Path(self.borehole_lithology_path)
        if not self.borehole_lithology_path.is_absolute():
            self.borehole_lithology_path = (
                base_dir_lithology
                / Path(self.input_dir_lithology)
                / self.borehole_lithology_path
            ).resolve()

        if not isinstance(self.out_dir_lithology, Path):
            self.out_dir_lithology = base_dir_lithology / Path(self.out_dir_lithology)

        return self


class LoadProfileConfig(BaseModel):
    """
    Configuration object for the heat load profile module.

    Handles input/output directories and parameters defining the thermal load
    time-profile used in simulations.

    Attributes
    ----------
    config_file_path : str or Path
        Path to the main JSON configuration file.
    lp_outdir : str or Path, optional
        Directory for processed load-profile output.
    lp_inputdir : str or Path, optional
        Directory containing load-profile input files, if type is FROMFILE
    lp_filename : str, optional
        Name of the input file when type is FROMFILE.
    lp_filepath : str or Path, optional
        Resolved absolute path to the input file if type is FROMFILE.
    lp_inputcolumn : str, optional
        Column name to read from the input file, if type is FROMFILE. Default is heating_demand
    lp_type : {"CONSTANT", "VARIABLE", "FROMFILE", "BERNIER"}
        Type of heat load time-profile used.
    lp_base : float or int, optional
        Base value if type is VARIABLE, constant value if type is CONSTANT.
    lp_peak : float or int, optional
        Peak value if type is VARIABLE.
    lp_minscaleflow : float or int, optional
        Minimum scaling factor applied to flow if type is FROMFILE or VARIABLE.
    lp_scale : float or int, optional
        Scaling factor of the heat laod in the time-profile if type is FROMFILE.
    lp_smoothing : str, optional
        Smoothing factor applied to the heat load profile if type is FROMFILE.
    lp_minQ : float or int, optional
        Minimum heat load constraint if type is FROMFILE.
    """

    config_file_path: str | Path
    lp_outdir: str | Path | None = None
    lp_inputdir: str | Path | None = None

    lp_filename: str | None = None
    lp_filepath: str | Path | None = None
    lp_inputcolumn: str | None = None

    lp_type: Literal["CONSTANT", "VARIABLE", "FROMFILE", "BERNIER"]
    lp_base: float | int | None = None
    lp_peak: float | int | None = None
    lp_minscaleflow: float | int | None = None
    lp_scale: float | int | None = 1.0
    lp_smoothing: str | None = None
    lp_minQ: int | float | None = None

    @model_validator(mode="after")
    def validate_fields(self):
        """
        Validate required fields depending on the selected load-profile type.

        Raises
        ------
        ValueError
            If required attributes for the selected `lp_type` are missing.

        Returns
        -------
        LoadProfileConfig
            The validated configuration model.
        """
        # CONSTANT
        if self.lp_type == "CONSTANT":
            missing = []
            if self.lp_base is None:
                missing.append("lp_base")
            if missing:
                raise ValueError(
                    f"Missing required fields for lp_type='{self.lp_type}': {', '.join(missing)}"
                )

        # VARIABLE
        if self.lp_type == "VARIABLE":
            missing = []
            if self.lp_base is None:
                missing.append("lp_base")
            if self.lp_peak is None:
                missing.append("lp_peak")
            if missing:
                raise ValueError(
                    f"Missing required fields for lp_type='{self.lp_type}': {', '.join(missing)}"
                )

        # FROMFILE
        elif self.lp_type == "FROMFILE":
            required = {
                "lp_filename": self.lp_filename,
                "lp_inputdir": self.lp_inputdir,
                "lp_scale": self.lp_scale,
                "lp_minscaleflow": self.lp_minscaleflow,
                "lp_minQ": self.lp_minQ,
            }
            missing = [k for k, v in required.items() if v is None]
            if missing:
                raise ValueError(
                    f"Missing required fields for lp_type='FROMFILE': {', '.join(missing)}"
                )
        return self

    # Resolve paths
    @model_validator(mode="after")
    def process_config_paths(self):
        """
        Resolve relative paths into absolute paths and create directories as needed.

        Updates `lp_outdir`, `lp_inputdir`, and `lp_filepath` based on the location
        of the main configuration file.

        Returns
        -------
        LoadProfileConfig
            The updated instance with resolved paths.
        """
        if not isinstance(self.config_file_path, Path):
            self.config_file_path = Path(self.config_file_path).resolve()

        lp_base_dir = self.config_file_path.parent

        if self.lp_outdir:
            if not isinstance(self.lp_outdir, Path):
                self.lp_outdir = lp_base_dir / Path(self.lp_outdir)
            if not self.lp_outdir.exists():
                self.lp_outdir.mkdir(parents=True, exist_ok=True)

        if self.lp_inputdir:
            if not isinstance(self.lp_inputdir, Path):
                self.lp_inputdir = lp_base_dir / Path(self.lp_inputdir)
            if not self.lp_inputdir.exists():
                self.lp_inputdir.mkdir(parents=True, exist_ok=True)

        if self.lp_filename:
            self.lp_filepath = lp_base_dir / self.lp_inputdir / self.lp_filename

        return self


class FlowDataConfig(BaseModel):
    """
    Configuration object for defining flow-rate profiles.

    Supports constant, variable, and file-based flow definitions and resolves
    directory paths automatically.

    Attributes
    ----------
    config_file_path : str or Path
        Path to the main configuration file.
    fp_type : {"CONSTANT", "VARIABLE", "FROMFILE"}
        Type of flow-rate time-profile.
    fp_outdir : str or Path, optional
        Output directory for processed flow data.
    fp_inputdir : str or Path, optional
        Input directory where flow data files reside, if type FROMFILE.
    fp_filename : str, optional
        Name of input file for file-based profiles if type FROMFILE.
    fp_filepath : Path
        Absolute file path for the input file after resolution if type FROMFILE.
    fp_base : float, optional
        Base flow value if type is VARIABLE.
    fp_peak : float, optional
        Peak flow value if type is VARIABLE, constant value if type is CONSTANT.
    fp_scale : float, optional
        Scaling factor for the flow profile if type is FROMFILE.
    fp_inputcolumn : str, optional
        Column name to read from the file, if type is FROMFILE.
    fp_smoothing : str, optional
        Smoothing method applied to the flow profile, if type is FROMFILE.
    """

    config_file_path: str | Path
    fp_type: Literal["CONSTANT", "VARIABLE", "FROMFILE"]
    fp_outdir: str | Path | None = None
    fp_inputdir: str | Path | None = None

    fp_filename: str | None = None
    fp_filepath: str | Path = None

    fp_base: float | None = None
    fp_peak: float | None = None
    fp_scale: float | None = 1.0
    fp_inputcolumn: str | None = None
    fp_smoothing: str | None = None

    @model_validator(mode="after")
    def validate_fields(self):
        """
        Ensure that required parameters are provided for the selected flow type.

        Raises
        ------
        ValueError
            If mandatory attributes for the chosen `fp_type` are missing.

        Returns
        -------
        FlowDataConfig
            The validated model instance.
        """
        # CONSTANT
        if self.fp_type == "CONSTANT":
            if self.fp_peak is None:
                raise ValueError("fp_peak is required for fp_type='CONSTANT'")

        # VARIABLE
        elif self.fp_type == "VARIABLE":
            missing = []
            if self.fp_base is None:
                missing.append("fp_base")
            if self.fp_peak is None:
                missing.append("fp_peak")
            if missing:
                raise ValueError(
                    f"Missing required fields for fp_type='VARIABLE': {', '.join(missing)}"
                )

        # FROMFILE
        elif self.fp_type == "FROMFILE":
            required = {
                "fp_filename": self.fp_filename,
                "fp_inputdir": self.fp_inputdir,
                "fp_inputcolumn": self.fp_inputcolumn,
                "fp_scale": self.fp_scale,
            }
            missing = [k for k, v in required.items() if v is None]
            if missing:
                raise ValueError(
                    f"Missing required fields for fp_type='FROMFILE': {', '.join(missing)}"
                )
        return self

    @model_validator(mode="after")
    def process_config_paths(self):
        """
        Resolve relative paths into absolute paths and create missing directories.

        Updates the resolved file path and ensures the input/output directories exist.

        Returns
        -------
        FlowDataConfig
        """
        if not isinstance(self.config_file_path, Path):
            self.config_file_path = Path(self.config_file_path).resolve()

        fp_base_dir = self.config_file_path.parent

        if self.fp_outdir:
            if not isinstance(self.fp_outdir, Path):
                self.fp_outdir = fp_base_dir / Path(self.fp_outdir)
            if not self.fp_outdir.exists():
                self.fp_outdir.mkdir(parents=True, exist_ok=True)

        if self.fp_inputdir:
            if not isinstance(self.fp_inputdir, Path):
                self.fp_inputdir = fp_base_dir / Path(self.fp_inputdir)
            if not self.fp_inputdir.exists():
                self.fp_inputdir.mkdir(parents=True, exist_ok=True)

        if self.fp_filename:
            self.fp_filepath = fp_base_dir / self.fp_inputdir / self.fp_filename

        return self


class SingleRunConfig(BaseModel, extra="allow"):
    """
    Configuration object for a single geothermal borehole simulation run.

    This model merges sub-configurations, validates borehole-type-dependent
    parameters, numerical model requirements, and resolves base directories.

    Attributes
    ----------
    config_file_path : Path
        Path to the main configuration file.
    base_dir : str or Path
        Path to the output folder.
    run_name : str, optional
        Name of the simulation run.
    type : {"UTUBE", "COAXIAL"}
        Borehole heat-exchanger type.
    H: float or int
        Borehole length [m]
    D: float or int
        Buried depth [m].
    r_b : float
        Borehole radius [m].
    r_out : list of float
        Outer pipe radius [m].
    k_p : float or int
        Pipe thermal conductivity [W/mK].
    k_g : float or int or list of float or int
        Grout thermal conductivity (layered or uniform) [W/mK].
    nsegments : int
        Number of model segments along the borehole.
    fluid_str : str
        Fluid type. Must be included in the pygfunction.media.Fluid module.
    fluid_percent : float or int
        Mixture percentage for the fluid dissolved in water.
    m_flow : float
        Mass flow rate per pipe [kg/s].
    epsilon : float
        Pipe roughness [m].
    r_in : list of float, optional
        Inner pipe radius [m]. Used if SDR is None.
    pos : list of list of float, optional
        Pipe positions, x,y-coordinates in the borehole. Default `[[0,0][0,0]]` for type COAXIAL.
    nInlets : int, optional
        Number of inlet pipes. Default 1 for type COAXIAL.
    SDR : float, optional
        SDR index for pipe thickness. If None, then r_in is used.
    insu_z : float, optional
        Maximum depth of insulating pipe material [m].
    insu_dr : float
        Fraction of pipe wall thickness that is insulated.
    insu_k : float
        Thermal conductivity of insulation material [W/mK].
    z_k_g : list of float, optional
        Depth breakpoints corresponding to grout thermal conductivities. Used if k_g is list.
    Tin : float or int
        Inlet temperature [°C].
    Q : float or int
        Heat extraction/injection rate [W].
    Tg : int or list of int
        Surface temperature if int, or subsurface temperature values over depth if list.
    Tgrad : int
        Geothermal gradient in °C/m.
    z_Tg : int or list of int, optional
        Depths at which Tg values apply if list. If int or float then it is not used.
    k_s : list of float
        Subsurface bulk thermal conductivity layers [W/mK]. Used if litho_k_param is None.
    z_k_s : list of float
        Maximum depths for soil conductivity layers [m]. Used if litho_k_param is None.
    alfa : float
        Subsurface thermal diffusivity [m2/s].
    k_s_scale : float
        Scaling factor for k_s, uniform over depth.
    model_type : {"FINVOL", "ANALYTICAL", "PYG", "PYGFIELD"}
        Type of model used in simulation.
    run_type : {"TIN", "POWER"}
        Starting point for performance calculation (inlet temperature or heat load).
    nyear: float or int
        Nr. of simulated years [years].
    nled : float or int
        Number of hours per simulated timestep [hours].
    nr : int, optional
        Number of radial model nodes (if model_type FINVOL).
    r_sim : float, optional
        Simulation radial distance [m] (if model_type FINVOL).
    save_Tfield_res : bool
        Flag to save full 3D temperature field for every timestep, if model_type FINVOL.
    dooptimize : bool
        Flag to do optimization simulation.
    optimize_keys : list of str, optional
        Parameter names to optimize for.
    optimize_keys_bounds : list of tuple, optional
        Bounds for optimization variables.
    copcrit : float or int, optinal,
        Minimum COP of the fluid circulation pump. Used if dooptimize = true.
    dploopcrit : float, optional
        Pumping power. Adjusts flow rate accordingly.
    borefield : dict, optional
        Borefield sub-configuration. Required for borehole field simulation.
    variables_config : dict, optional
        Stochastic or optimization sub-configuration. Required for stochastic simulation.
    litho_k_param : dict, optional
        Lithology module sub-configuration.
    loadprofile : dict, optional
        Loadprofile module configuration.
    flow_data : dict, optional
        FlowData module configuration.
    """

    # Path to the configuration json
    config_file_path: Path = None

    # Base / paths
    base_dir: str | Path
    run_name: str | None = None

    # Borehole design
    # Required Parameters
    type: Literal["UTUBE", "COAXIAL"]
    H: float | int
    D: float | int
    r_b: float
    r_out: list[float]

    k_p: float
    k_g: float | list[float]

    fluid_str: Literal["water", "MEG", "MPG", "MEA", "MMA"]
    fluid_percent: float | int
    m_flow: float
    epsilon: float

    # Optional / Conditional for borehole
    r_in: list[float] | None = None
    pos: list[list[float]] = None
    nInlets: int = None

    SDR: int | float = None
    insu_z: float | int = 0
    insu_dr: float = 0.0
    insu_k: float = 0.03
    z_k_g: list[float] = None

    Tin: float | int = 10
    Q: float | int = 1000

    # Subsurface temperature parameters
    Tg: float | int | list
    z_Tg: float | int | list[float] | list[int]
    Tgrad: float

    # thermal conductivity and thermal diffusivity parameters
    k_s: list[float]
    z_k_s: list[float]
    alfa: float
    k_s_scale: float

    # model & run types
    model_type: Literal["FINVOL", "ANALYTICAL", "PYG", "PYGFIELD"]
    run_type: Literal["TIN", "POWER"]

    # time parameters
    nyear: float | int
    nled: float | int

    # borehole discretization
    nsegments: int

    # FINVOL-only parameters
    nr: int | None = None
    r_sim: float | None = None
    save_Tfield_res: bool | None = False

    # Optional optimization
    dooptimize: bool = False
    optimize_keys: list[str] | None = None
    optimize_keys_bounds: list[tuple[float, float]] | None = None
    copcrit: float | None = None
    dploopcrit: float | None = None

    # Optional linked config files with parameters for submodules
    borefield: dict | None = None
    field_N: int = 1
    field_M: int = 1
    field_R: int = 3
    field_inclination_start: float | int = 0
    field_inclination_end: float | int = 0
    field_segments: int = 1

    variables_config: dict | None = None
    litho_k_param: dict | None = None
    loadprofile: dict | None = None
    flow_data: dict | None = None

    @model_validator(mode="before")
    def merge_borefield_and_cast_subdicts(cls, data):
        """
        Merge sub-configuration dictionaries into the root configuration.

        This merges the `borefield` dictionary directly into the root namespace
        and overwrites or adds parameters from `litho_k_param`.

        Parameters
        ----------
        data : dict
            Raw configuration dictionary input.

        Returns
        -------
        dict
            Updated configuration dictionary containing merged fields.
        """
        if not isinstance(data, dict):
            return data

        # merge borefield key into root
        borefield = data.get("borefield")
        if isinstance(borefield, dict):
            # Borefield values override OR add missing optional fields
            for k, v in borefield.items():
                if k not in data or data[k] is None:
                    data[k] = v

        # Adopt litho_k_param values in root
        litho = data.get("litho_k_param")
        if isinstance(litho, dict):
            for k, v in litho.items():
                if k == "config_file_path":
                    continue
                # overwrite root if the key appears both in root and litho_k_param
                if k in data:
                    data[k] = v

        return data

    # Type-dependent validation
    @model_validator(mode="after")
    def apply_type_logic(self):
        """
        Validate and apply logic depending on the borehole heat-exchanger type.

        Raises
        ------
        ValueError
            If required fields for UTUBE configurations are missing.

        Returns
        -------
        SingleRunConfig
            Updated model with defaults or validated fields.
        """
        if self.type == "UTUBE":
            if self.pos is None:
                raise ValueError("UTUBE requires 'pos'")
            if self.nInlets is None:
                raise ValueError("UTUBE requires 'nInlets'")

        elif self.type == "COAXIAL":
            # override with defaults
            self.pos = [[0, 0], [0, 0]]
            self.nInlets = 1

        return self

    @model_validator(mode="after")
    def validate_finvol_fields(self):
        """
        Validate parameters required for FINVOL numerical model.

        Raises
        ------
        ValueError
            If `nr` or `r_sim` are missing when model_type='FINVOL'.

        Returns
        -------
        SingleRunConfig
        """
        if self.model_type == "FINVOL":
            # Ensure required fields are provided
            if self.nr is None:
                raise ValueError("nr must be provided when model_type='FINVOL'")
            if self.r_sim is None:
                raise ValueError("r_sim must be provided when model_type='FINVOL'")

        return self

    # Resolve paths
    @model_validator(mode="after")
    def process_config_paths(self):
        """
        Resolve the base directory path for the simulation run.

        Ensures that relative paths are resolved using the config file location and
        that the directory exists or is created.

        Returns
        -------
        SingleRunConfig
        """
        base_dir_path = Path(self.base_dir)

        if not base_dir_path.is_absolute():
            if self.config_file_path is None:
                raise ValueError(
                    "Cannot resolve relative base_dir: config_path not set"
                )
            elif isinstance(self.config_file_path, str):
                self.config_file_path = Path(self.config_file_path)
            base_dir_path = self.config_file_path.parent / base_dir_path

        self.base_dir = base_dir_path.resolve()

        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)

        return self


class StochasticRunConfig(BaseModel):
    """
    Configuration object for defining stochastic or optimization variable distributions.

    Each parameter is described by a tuple specifying the distribution type
    and its numeric bounds.

    Attributes
    ----------
    n_samples : int, optional
        Number of Monte-Carlo samples.
    k_s_scale, k_p, insu_z, insu_dr, insu_k, m_flow, Tin, H,
    epsilon, alfa, Tgrad, Q, fluid_percent, r_out : tuple(str, float, float)
        Triplets defining: [dist_type, dist1, dist2, (optional dist3)] where dist_type ∈
        {"normal", "uniform", "lognormal", "triangular"}.

    Notes
    -----
    if dist_name == "normal":
    mean, std_dev = dist[1], dist[2]

    elif dist_name == "uniform":
        min, max = dist[1], dist[2]

    elif dist_name == "lognormal":
        mu, sigma = dist[1], dist[2]

    elif dist_name == "triangular":
        min, peak, max = dist[1], dist[2], dist[3]
    """

    n_samples: int | None = None
    k_s_scale: tuple[str, float, float] = None
    k_p: tuple[str, float, float] = None
    insu_z: tuple[str, float, float] = None
    insu_dr: tuple[str, float, float] = None
    insu_k: tuple[str, float, float] = None
    m_flow: tuple[str, float, float] = None
    Tin: tuple[str, float, float] = None
    H: tuple[str, float, float] = None
    epsilon: tuple[str, float, float] = None
    alfa: tuple[str, float, float] = None
    Tgrad: tuple[str, float, float] = None
    Q: tuple[str, float, float] = None
    fluid_percent: tuple[str, float, float] = None
    r_out: tuple[str, float, float] = None


class PlotInputConfig(BaseModel):
    """
    Configuration object for plotting simulation results.

    Controls which simulations to plot, source and output directories, and which
    quantities or layers to visualize.

    Attributes
    ----------
    config_file_path : Path
        Path to the main configuration file.
    base_dir : str or Path
        Directory where results are located that are plotted.
    run_names : list of str
        Names of simulation runs to include in plots.
    model_types : list of str
        List of model types (ANALYTICAL or FINVOL) corresponding to each simulation.
    run_types : list of str
        Run modes(TIN or POWER) for selected simulations.
    run_modes : list of str
        Type of simulations to plot (SR for single run or MC for stochastic run).
    plot_names : list of str, optional
        Name(s) of simulation(s) that is used in the legend of the plot(s).
    plot_nPipes : list of int
        Index of pipe for dataselection to plot.
    plot_layer_k_s : list of int
        Index of thermal conductivity layer for dataselection of input parameters to plot.
    plot_layer_kg : list of int
        Index of grout thermal conductivity layer for dataselection of input parameters to plot.
    plot_layer_Tg : list of int
        Index of subsurface temperature layer for dataselection of input parameters to plot.
    plot_nz : list of int
        Index of depth layer for dataselection of results to plot.
    plot_ntime : list of int
        Index of timestep for dataselection of results to plot.
    plot_nzseg : list of int
        Index of depth segment for dataselection of results to plot.
    plot_times : list of float
        Timesteps at which plots should be generated.
    plot_time_depth : bool
        Flag that determines whether to generate time– and depth-plots.
    plot_time_parameters : list of str, optional
        Time-dependant parameters to plot. Optional. Only used if plot_time_depth is true. Options: dploop; qloop; flowrate;
        T_fi; T_fo; T_bave; Q_b; COP; Delta_T. With Delta_T = T_fo - T_fi and COP = Q_b/qloop
    plot_depth_parameters : list of str, optional
        Depth-dependant parameters to plot. Optional. Only used if plot_time_depth is true. Options: T_b;
        Tg; T_f; Delta_T
    plot_borehole_temp : list of int, optional
        List of depth-segment slice indices to plot borehole temperature for.
        Only used if plot_time_depth is true. index 0 always works
    plot_crossplot_barplot : bool
        Flag that determines whether to create crossplots and barplots.
        Only compatible with stochastic simulations
    newplot : bool
                Flag to plot the simulation(s) listed in run_names seperately or together.
                Only simulations with the same run_modes can be plot together
    crossplot_vars : list of str
                Variable input parameters and results to target in crossplots and tornado plots.
                Only used if plot_crossplot_barplot is true
    plot_temperature_field : bool
        Flag that determines whether to plot full 3D temperature fields. Only used if model_type is FINVOL.
    """

    config_file_path: Path = None

    base_dir: str | Path
    run_names: list[str]
    model_types: list[str]
    run_types: list[str]
    run_modes: list[str]

    plot_names: list[str] = None
    plot_nPipes: list[int]
    plot_layer_k_s: list[int]
    plot_layer_kg: list[int]
    plot_layer_Tg: list[int]
    plot_nz: list[int]
    plot_ntime: list[int]
    plot_nzseg: list[int]
    plot_times: list[float]
    plot_time_depth: bool
    plot_time_parameters: list[str] | None = None
    plot_depth_parameters: list[str] | None = None
    plot_borehole_temp: list[int] | None = None
    plot_crossplot_barplot: bool
    newplot: bool
    crossplot_vars: list[str]
    plot_temperature_field: bool = False

    @model_validator(mode="after")
    def process_config_paths(self):
        """
        Resolve the base plotting directory.

        Uses the config file path to resolve relative paths and ensures the
        directory exists.

        Returns
        -------
        PlotInputConfig
        """
        base_dir_path = Path(self.base_dir)

        if not base_dir_path.is_absolute():
            if self.config_file_path is None:
                raise ValueError(
                    "Cannot resolve relative base_dir: config_path not set"
                )
            elif isinstance(self.config_file_path, str):
                self.config_file_path = Path(self.config_file_path)
            base_dir_path = self.config_file_path.parent / base_dir_path

        self.base_dir = base_dir_path.resolve()

        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)

        return self


def load_json(path: str | Path) -> dict:
    """
    Open a JSON configuration file and load parameters into a dictionary.

    Parameters
    ----------
    path: str | Path
        Path to the JSON configuration file.

    Returns
    -------
    dict
        Dictionary with parameters and values defined in the JSON file.
    """
    with open(path) as f:
        return json.load(f)


def load_single_config(main_config_path: str | Path) -> dict:
    """
    Load main JSON as dictionary.

    Parameters
    ----------
    main_config_path : str
        Path to the main JSON configuration file.

    Returns
    -------
    dict
        Configuration dictionary.
    """
    main_path = Path(main_config_path).resolve()

    # Load top-level config file
    config = load_json(main_path)

    config["config_file_path"] = main_path

    return config


def load_nested_config(
    main_config_path: str, keys_needed: list[str] = [], keys_optional: list[str] = []
) -> dict:
    """
    Load main JSON and inject referenced sub-configs as nested dictionaries.

    Parameters
    ----------
    main_config_path : str
        Path to the main JSON configuration file.
    keys_needed : list[str]
        Keys that must point to valid JSON files.
    keys_optional : list[str]
        Keys that may optionally point to JSON files.

    Returns
    -------
    dict
        Nested configuration dictionary.
    """
    main_path = Path(main_config_path).resolve()
    base_dir = main_path.parent

    # Load top-level config file
    config = load_json(main_path)

    config["config_file_path"] = main_path

    # required sub-configs
    for key in keys_needed:
        if key not in config:
            raise KeyError(f"Required subconfig key missing: {key}")

        subpath = base_dir / config[key]
        subconfig = load_json(subpath)
        subconfig["config_file_path"] = subpath
        # Replace file path with actual nested dictionary
        config[key] = subconfig

    # optional sub-configs
    for key in keys_optional:
        if key in config and config[key]:
            subpath = base_dir / config[key]

            try:
                subconfig = load_json(subpath)
                subconfig["config_file_path"] = subpath
                config[key] = subconfig  # replace path with nested dict
            except FileNotFoundError:
                print(f"Optional config file not found: {subpath}, skipping.")

    return config
