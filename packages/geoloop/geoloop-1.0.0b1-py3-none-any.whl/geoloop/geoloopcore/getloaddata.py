import numpy as np

from geoloop.configuration import FlowDataConfig, LoadProfileConfig, SingleRunConfig
from geoloop.loadflowdata.flow_data import FlowData
from geoloop.loadflowdata.loadprofile import LoadProfile


class GetLoadData:
    """
    Class to generate time series of flow rates, inlet temperatures, and heat/power loads
    for simulations.

    It can use constant input values or optional time-dependent variations from either
    a FlowData object (variable flow rates) or a LoadProfile object (variable heat load).

    Attributes
    ----------
    Tin : np.ndarray
        Inlet temperature array (°C) over the simulation time (constant through time).
    m_flow : np.ndarray
        Mass flow rate array (kg/s) over the simulation time.
    Q : np.ndarray
        Heat load array (W) over the simulation time.
    time : np.ndarray
        Time array in seconds.
    data : FlowData or LoadProfile, optional
        Optional object providing time-dependent flow or load.
    """

    # model types
    FINVOL = "FINVOL"  # finite volume approach with borehole heat exchanger system, can only run with run_type TIN
    ANALYTICAL = (
        "ANALYTICAL"  # semi-analytical approach, can run with both TIN and POWER
    )
    PYG = "PYG"  # 'standard' pyg approach,

    # run types
    TIN = "TIN"  #  input temperature
    POWER = "POWER"  # input power

    def __init__(
        self,
        Tin: float,
        m_flow: float,
        Q: float,
        time: np.ndarray,
        loaddata: LoadProfile | FlowData = None,
    ):
        """
        Initialize the GetLoadData object.

        Parameters
        ----------
        Tin : float
            Constant inlet temperature (°C) if no LoadData is provided.
        m_flow : float
            Constant mass flow rate (kg/s) if no LoadData is provided.
        Q : float
            Constant heat load (W) if no LoadData is provided.
        time : np.ndarray
            Array of time points (seconds) for the simulation.
        loaddata : FlowData or LoadProfile, optional
            Optional object providing variable flow or load data.
        """
        self.data = loaddata

        if isinstance(loaddata, FlowData):
            self.Tin = np.ones_like(time) * Tin
            self.Q = np.ones_like(time) * Q
            self.m_flow = loaddata.getflow(time / 3600.0)
        elif isinstance(loaddata, LoadProfile):
            self.Tin = np.ones_like(time) * Tin
            self.Q, self.m_flow = loaddata.getloadflow(time / 3600.0, m_flow)
        elif loaddata is None:
            self.Tin = np.ones_like(time) * Tin
            self.Q = np.ones_like(time) * Q
            self.m_flow = np.ones_like(time) * m_flow

    @classmethod
    def from_config(cls, config: SingleRunConfig) -> "GetLoadData":
        """
        Factory method to create a GetLoadData object from a configuration dictionary.

        This method constructs the time array and optionally initializes either
        a FlowData or LoadProfile object depending on the run type.

        Parameters
        ----------
        config : SingleRunConfig
            Configuration object of main simulation module

        Returns
        -------
        GetLoadData
            Initialized object with time series for flow, temperature, and heat load.
        """
        # Build time array
        tmax = config.nyear * 8760 * 3600
        dt = 3600 * config.nled
        Nt = int(np.ceil(tmax / dt))
        time = dt * np.arange(1, Nt + 1)

        # Determine optional subobject
        data = None
        if config.run_type == "POWER" and config.loadprofile:
            loadprofile_config = LoadProfileConfig(**config.loadprofile)
            data = LoadProfile.from_config(loadprofile_config)
        elif config.run_type == "TIN" and config.flow_data:
            flow_data_config = FlowDataConfig(**config.flow_data)
            data = FlowData.from_config(flow_data_config)

        return cls(config.Tin, config.m_flow, config.Q, time, loaddata=data)
