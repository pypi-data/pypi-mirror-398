import numpy as np

from geoloop.configuration import SingleRunConfig
from geoloop.geoloopcore.getloaddata import GetLoadData


class SimulationParameters:
    """
    Class for simulation settings, time discretization,
    load data, and model selection for BHE simulations.
    """

    # model types
    FINVOL = "FINVOL"  # finite volume approach with borehole heat exchanger system, can only run with run_type TIN
    ANALYTICAL = (
        "ANALYTICAL"  # semi-analytical approach, can run with both TIN and POWER
    )
    PYG = "PYG"  # 'standard' pyg approach, only supports run type POWER
    PYGFIELD = (
        "PYGFIELD"  # pyg curved borehole array approach, only supports run type POWER
    )

    # run types
    TIN = "TIN"  #  input temperature
    POWER = "POWER"  # input power

    def __init__(
        self,
        nyear: int,
        nled: int,
        model_type: str,
        run_type: str,
        nsegments: int,
        nr: int = None,
        rmax: float = None,
        loaddata: GetLoadData = None,
    ) -> None:
        """
        Constructor for the SimulationParameters class.

        Parameters
        ----------
        nyear : int
            Number of simulation years.
        nled : int
            Time resolution factor (dt = 3600 * nled).
        model_type : str
            One of {FINVOL, ANALYTICAL, PYG, PYGFIELD}.
        run_type : str
            Either TIN or POWER.
        nsegments : int
            Number of depth segments used in the borehole solver.
        nr : int, optional
            Number of radial nodes (FINVOL only).
        rmax : float, optional
            Outer radius for radial simulation domain (FINVOL only).
        loaddata : GetLoadData
            Load data object providing Tin, Q, m_flow, and time arrays.
        """
        # time discretization
        self.nyear = nyear
        self.tmax = nyear * 8760.0 * 3600.0  # Maximum time (s)
        self.nled = nled
        self.dt = 3600 * nled  # Time step (s) , 100h
        self.Nt = int(np.ceil(self.tmax / self.dt))  # Number of time steps
        self.time = self.dt * np.arange(1, self.Nt + 1)  # time in seconds

        # Geometry parameters only used in the FINVOL model
        self.nr = nr
        self.rmax = rmax

        # load data
        self.loaddata = loaddata.data

        self.m_flow = loaddata.m_flow
        self.Tin = loaddata.Tin
        self.Q = loaddata.Q

        # model configuration
        self.model_type = model_type
        self.run_type = run_type
        self.nsegments = nsegments

        # set the efficency of the pump to 0.65
        self.eff = 0.65

    @property
    def isample(self):
        """Index of the current simulation timestep."""
        return self._isample

    @isample.setter
    def isample(self, value: int) -> None:
        self._isample = value

    def modelsupported(self) -> None:
        """Prints a warning for unsupported model/run combinations."""
        print("Model not supported ", self.model_type, " with mode ", self)

    @classmethod
    def from_config(cls, config: SingleRunConfig) -> "SimulationParameters":
        """
        Construct a SimulationParameters object from a configuration object.

        Parameters
        ----------
        config : SingleRunConfig
            Configuration object.

        Returns
        -------
        SimulationParameters
            Fully initialized simulation parameter object.
        """
        nr = config.nr if config.model_type == cls.FINVOL else None
        rmax = config.r_sim if config.model_type == cls.FINVOL else None

        # Build GetLoadData only if present
        load_data_obj = GetLoadData.from_config(config)

        return cls(
            nyear=config.nyear,
            nled=config.nled,
            model_type=config.model_type,
            run_type=config.run_type,
            nsegments=config.nsegments,
            nr=nr,
            rmax=rmax,
            loaddata=load_data_obj,
        )
