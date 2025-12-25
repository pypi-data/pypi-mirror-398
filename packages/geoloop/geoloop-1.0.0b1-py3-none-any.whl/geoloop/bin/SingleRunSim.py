import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pygfunction as gt
import xarray as xr
from numpy.typing import NDArray
from scipy.optimize import minimize

from geoloop.configuration import LithologyConfig, SingleRunConfig, load_nested_config
from geoloop.geoloopcore.b2g import B2G
from geoloop.geoloopcore.b2g_ana import B2G_ana
from geoloop.geoloopcore.boreholedesign import BoreholeDesign
from geoloop.geoloopcore.pyg_ana import PYG_ana
from geoloop.geoloopcore.pygfield_ana import (
    PYGFIELD_ana,
    visualize_3d_borehole_field,
    visualize_gfunc,
)
from geoloop.geoloopcore.simulationparameters import SimulationParameters
from geoloop.geoloopcore.soilproperties import SoilProperties
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity
from geoloop.utils.helpers import save_singlerun_results


def optimize_forkeys(
    config: dict,
    copcrit: float,
    optimize_keys: list[str],
    optimize_bounds: list[tuple[float, float]],
    isample: int,
) -> tuple[Any, dict]:
    """
    Optimizes selected configuration parameters based on a specified COP criterion.

    Parameters
    ----------
    config : dict
        Configuration dictionary for a single sample, modified in-place.
    copcrit : float
        Target COP value used in the optimization objective function.
    optimize_keys : list[str]
        List of configuration keys to adjust during optimization and optimize for.
    optimize_bounds : list[tuple[float, float]]
        Upper and lower value bounds for each optimization key.
    isample : int
        Index of the sampled model run.

    Returns
    -------
    tuple
        First element is the optimizer result object (`scipy.optimize.OptimizeResult`).
        Second element is the updated config dictionary.
    """
    x0 = np.zeros(len(optimize_keys))
    boundsval = []
    for i, key in enumerate(optimize_keys):
        boundsval.append((optimize_bounds[i][0], optimize_bounds[i][1]))
        x0[i] = 0.5 * sum(boundsval[i])

    method = "Nelder-Mead"
    method = "Powell"

    # ftol is tolerance for output power error of optimized point
    result = minimize(
        optimize_keys_func,
        x0,
        args=(optimize_keys, config, copcrit, isample),
        bounds=boundsval,
        method=method,
        options={"maxiter": 50, "ftol": 100},
    )

    return result, config


def optimize_keys_func(
    x: NDArray[np.float64],
    optimize_keys: list[str],
    config: dict,
    copcrit: float,
    isample: int,
) -> float:
    """
    Objective function used for parameter optimization.

    Parameters
    ----------
    x : np.ndarray
        Current optimization parameter values.
    optimize_keys : list[str]
        List of configuration keys to optimize for and identifying which config fields to modify.
    config : dict
        Current configuration dictionary that is modified in-place.
    copcrit : float
        Target COP value used in the optimization objective function.
    isample : int
        Sample index for simulation.

    Returns
    -------
    float
        Value of the objective function (to be minimized).
    """
    # Assign new values into config
    for i, key in enumerate(optimize_keys):
        if key == "r_out":
            # if coaxial optimize the inner (last) radius
            if config["type"] == "COAXIAL":
                config[key][-1] = x[i]
            else:
                # scale all tubes with radius
                config[key] = np.zeros(len(config[key])) + x[i]
        else:
            config[key] = x[i]

        print(f"Optimizing '{key}': testing value {config[key]}")

    # Create simulation instance and run
    single_run = SingleRun.from_config(SingleRunConfig(**config))
    result = single_run.run(isample)

    qb = result.Q_b
    cop = abs(qb / result.qloop)
    dploop = result.dploop

    dploopcrit = config.get("dploopcrit")

    retval = Jfunc(qb, cop, copcrit, dploop, dploopcrit=dploopcrit)

    return retval


def Jfunc(
    qb: NDArray[np.float64],
    cop: NDArray[np.float64],
    copcrit: float,
    dploop: NDArray[np.float64],
    dploopcrit: float | None = None,
) -> float:
    """
    Objective function for optimizing heat yield, used to evaluate optimization result.

    Parameters
    ----------
    qb : np.ndarray
        Heat balance result array.
    cop : np.ndarray
        COP result array.
    copcrit : float
        COP threshold criterion.
    dploop : np.ndarray
        Pumping pressure values.
    dploopcrit : float, optional
        Pumping pressure limit.

    Returns
    -------
    float
        Objective value to minimize (negative of last qb result or penalty).
    """
    retval = qb

    # COP penalty
    x = cop - copcrit
    if x[-1] < 0:
        retval = np.minimum(0, x * 1e3)

    # Pumping pressure penalty
    if dploopcrit is not None:
        x = dploopcrit - dploop
        if x[-1] < 0:
            retval = np.minimum(0, np.minimum(retval, 0) + x * 1e3)

    return -retval[-1]


class SingleRunResult:
    """
    Container class holding the results of a single BHE simulation run.

    Stores time series, depth-dependent, and spatial thermal field output data.
    """

    def __init__(
        self,
        hours: np.ndarray,
        Q_b: np.ndarray,
        flowrate: np.ndarray,
        qsign: np.ndarray,
        T_fi: np.ndarray,
        T_fo: np.ndarray,
        T_bave: np.ndarray,
        dploop: np.ndarray,
        qloop: np.ndarray,
        z: np.ndarray,
        zseg: np.ndarray,
        T_b: np.ndarray,
        T_f: np.ndarray,
        qzb: np.ndarray,
        Re_in: np.ndarray,
        Re_out: np.ndarray,
        nPipes: int,
        k_s: np.ndarray,
        k_g: np.ndarray,
        Tg: np.ndarray,
        numerical_result: np.ndarray,
        ag: object,
    ) -> None:
        """
        Initialize simulation result container.

        Parameters
        ----------
        hours : np.ndarray
            Time values of the simulation results [h].
        Q_b : np.ndarray
            Produced power over time [W].
        flowrate : np.ndarray
            Mass flow rate over time [kg/s].
        qsign : np.ndarray
            Sign of power production (-1 = extraction, +1 = injection).
        T_fi : np.ndarray
            Inlet fluid temperature over time [°C].
        T_fo : np.ndarray
            Outlet fluid temperature over time [°C].
        T_bave : np.ndarray
            Average borehole wall temperature over time [°C].
        dploop : np.ndarray
            Required pressure for loop pumping over time [bar].
        qloop : np.ndarray
            Power required to drive loop pumping over time [W].
        z : np.ndarray
            Node-based depth coordinates used for `T_f` output [m].
        zseg : np.ndarray
            Segment-based depth coordinates used for `T_b` and `qzb` [m].
        T_b : np.ndarray
            Borehole wall temperature as function of time and depth [°C].
            Shape: (n_time, n_depth_segments)
        T_f : np.ndarray
            Fluid temperature as function of time, depth and pipe index [°C].
            Shape: (n_time, n_depth_nodes, nPipes)
        qzb : np.ndarray
            Distributed heat flux at borehole wall [W/m].
            Shape: (n_time, n_depth_segments)
        Re_in : np.ndarray
            Reynolds number in inlet pipes over time [-].
        Re_out : np.ndarray
            Reynolds number in outlet pipes over time [-].
        nPipes : int
            Number of pipes considered in the simulation [-].
        k_s : np.ndarray
            Depth-interpolated subsurface thermal conductivity [W/mK].
        k_g : np.ndarray
            Depth-interpolated grout thermal conductivity [W/mK].
        Tg : np.ndarray
            Depth-interpolated ground temperature [°C].
        numerical_result : np.ndarray
            Full 4D temperature field output from a BHE simulation with the numerical finite volume model.
            Dimension order: (time, x, r, z)
        ag : object
            Axial grid object (grid properties for finite volume model).
        """

        self.hours = hours
        self.Q_b = Q_b
        self.flowrate = flowrate
        self.qsign = qsign
        self.T_fi = T_fi
        self.T_fo = T_fo
        self.T_bave = T_bave
        self.dploop = dploop
        self.qloop = qloop
        self.z = z
        self.zseg = zseg
        self.T_b = T_b
        self.T_f = T_f
        self.qzb = qzb
        self.Re_in = Re_in
        self.Re_out = Re_out
        self.nPipes = nPipes
        self.k_s = k_s
        self.k_g = k_g
        self.Tg = Tg
        self.numerical_result = numerical_result
        self.ag = ag

    def save_T_field_FINVOL(self, outpath: str | Path) -> None:
        """
        Save the full 4D temperature field to an HDF5/NetCDF file.

        The output quantity corresponds to the finite-volume radial
        temperature field stored in `self.numerical_result`.

        Parameters
        ----------
        outpath : str or pathlib.Path
            Base output file path (without `_FINVOL_T.h5` suffix).

        Returns
        -------
        None
        """
        # Create and export DataArray for the temperature results in the radial field
        time_coord = self.hours
        x_coord = self.ag.x
        r_coord = self.ag.axicellrmid[0].flatten()

        result_da = xr.DataArray(
            self.numerical_result,
            dims=["time", "x", "r", "z"],
            coords={"time": time_coord, "x": x_coord, "r": r_coord},
            name="Temperature (Deg C)",
        )

        # Export temperature field data
        outpath = Path(outpath)  # ensure it’s a Path
        result_outpath = outpath.with_name(outpath.stem + "_FINVOL_T.h5")

        result_da.to_netcdf(result_outpath, group="Temperature", engine="h5netcdf")

        return

    def get_n_pipes(self) -> int:
        """
        Return the number of pipes used in the simulation.

        Returns
        -------
        int
            Number of pipes.
        """
        return self.nPipes

    def getzseg(self) -> np.ndarray:
        """
        Return segment-based depth coordinates.

        These correspond to the depth resolution used for results such as
        borehole wall temperature (`T_b`) and borehole heat flux (`qzb`).

        Returns
        -------
        np.ndarray
            Depth values in meters, defined at segment mid-points.
        """
        return self.zseg

    def gethours(self) -> np.ndarray:
        """
        Return the simulation time coordinate.

        Returns
        -------
        np.ndarray
            Time values in hours.
        """
        return self.hours

    def getz(self) -> np.ndarray:
        """
        Return node-based depth coordinates.

        These correspond to the depth resolution used for pipe fluid
        temperature (`T_f`) results.

        Returns
        -------
        np.ndarray
            Depth values in meters, defined at nodal locations.
        """
        return self.z

    def getResultAttributesTimeseriesScalar(self) -> list[str]:
        """
        Return a list of available scalar time-series result keys.

        These correspond to simulation outputs varying only in time.

        Returns
        -------
        list of str
            Names of time-dependent scalar result variables.
        """
        return [
            "hours",
            "Q_b",
            "flowrate",
            "qsign",
            "T_fi",
            "T_fo",
            "T_bave",
            "dploop",
            "qloop",
            "Re_in",
            "Re_out",
        ]

    def getResultAttributesTimeseriesDepthseg(self) -> list[str]:
        """
        Return time-series attributes defined on depth segments.

        Returns
        -------
        list of str
            Variable names indexed by (time, depth segment).
        """
        return ["T_b", "qzb"]

    def getResultAttributesTimeserieDepth(self) -> list[str]:
        """
        Return time-series attributes defined on depth nodes.

        Returns
        -------
        list of str
            Variable names indexed by (time, depth node).
        """
        return ["T_f"]

    def getResultAttributesDepthseg(self) -> list[str]:
        """
        Return static (time-independent) depth-segment results.

        Returns
        -------
        list of str
            Variable names indexed by depth segment.
        """
        return ["k_s", "k_g", "Tg"]


class SingleRun:
    """
    Class for parameters for running BHE model which consists of various compartments
    which can be adapted, and facilitates in creating and updating related objects.


    These include:

    A. BoreholeDesign
     - the borehole dimensions, and pipe configuration and dimensions
     - the material properties and roughness of pipes
     - the grout properties
     - the working fluid properties
     - pump efficiency
     - borehole field parameters (only for madrid/curved borehole field)
     - N number of boreholes (used to scale flow over each borehole)
     - R radius of circular arranged boreholes(only for ilted borehole field)

    B. SoilProperties
     -  surface temperature and gradient
     -  thermal properties of soil

    C. OperationalParameters
     -  inlet temperature of power timeseries
     -  mass rate
    """

    def __init__(
        self,
        borehole_design: BoreholeDesign,
        soil_properties: SoilProperties,
        simulation_parameters: SimulationParameters,
    ) -> None:
        """
        Construct a SingleRun object.

        Parameters
        ----------
        borehole_design : BoreholeDesign
            Borehole, pipe, grout, and geometry configuration.
        soil_properties : SoilProperties
            Ground temperature and thermal properties.
        simulation_parameters : SimulationParameters
            Time-dependent operational parameters and solver configuration.
        """
        self.bh_design = borehole_design
        self.soil_props = soil_properties
        self.sim_params = simulation_parameters

    @classmethod
    def from_config(cls, config: SingleRunConfig) -> "SingleRun":
        """
        Create a ``SingleRun`` instance from a configuration dictionary.

        If ``dploopcrit`` is present in the configuration, the mass flow rate
        is automatically scaled to match the allowed pumping pressure.

        Parameters
        ----------
        config : SingleRunConfig
            Configuration object (typically loaded from a JSON file).

        Returns
        -------
        SingleRun
            Configured instance of ``SingleRun``.
        """
        borehole_design = BoreholeDesign.from_config(config)
        soil_properties = SoilProperties.from_config(config)
        simulation_parameters = SimulationParameters.from_config(config)

        # if dploopcrit has been specified adjust the flowrate in based on the allowed pressure if necessary
        # the mflow is set
        if config.dploopcrit:
            dploopcrit = config.dploopcrit
            flowrate = simulation_parameters.m_flow
            tempfluid = simulation_parameters.Tin[0]

            mflowscale = borehole_design.findflowrate_dploop(
                dploopcrit, tempfluid, flowrate, simulation_parameters.eff
            )

            simulation_parameters.m_flow *= mflowscale

        single_run = cls(borehole_design, soil_properties, simulation_parameters)

        return single_run

    def run(self, isample: int) -> SingleRunResult | None:
        """
        Run a single borehole heat exchanger (BHE) simulation for one sample.

        Parameters
        ----------
        isample : int
            Index of the sample to run. Use ``-1`` for the base case.

        Returns
        -------
        SingleRunResult
            Object containing the simulation results, including:

            **Time-dependent outputs**
            - hours : ndarray of shape (nt,)
                Simulation time in hours.
            - Q_b : ndarray of shape (nt,)
                Extracted/injected borehole power [W].
            - flowrate : ndarray of shape (nt,)
                Mass flow rate [kg/s].
            - qsign : ndarray of shape (nt,)
                Sign of heat extraction/injection.
            - T_fi : ndarray of shape (nt,)
                Inlet fluid temperature [°C].
            - T_fo : ndarray of shape (nt,)
                Outlet fluid temperature [°C].
            - T_bave : ndarray of shape (nt,)
                Average borehole wall temperature [°C].
            - dploop : ndarray of shape (nt,)
                Pressure drop across the loop [bar].
            - qloop : ndarray of shape (nt,)
                Pumping power [W].
            - Re_in, Re_out : ndarray of shape (nt,)
                Reynolds numbers in inlet/outlet pipes.

            **Depth-dependent outputs**
            - z : ndarray of shape (nz,)
                Depth coordinates for fluid temperatures.
            - zseg : ndarray of shape (nseg,)
                Depth segment coordinates for wall/grout quantities.
            - T_b : ndarray of shape (nt, nseg)
                Borehole wall temperature [°C].
            - T_f : ndarray of shape (nt, npipes, nz)
                Fluid temperature in pipes [°C].
            - qzb : ndarray of shape (nt, nseg)
                Heat flux along the borehole wall [W/m].
            - k_s : ndarray of shape (nseg,)
                Soil conductivity interpolated over segments.
            - k_g : ndarray of shape (nseg,)
                Grout conductivity over segments.
            - Tg : ndarray of shape (nseg,)
                Undisturbed ground temperature [°C].

        Notes
        -----
        The executed simulation model is determined by ``operPar.model_type``.
        Supported models include:
        ``FINVOL``, ``ANALYTICAL``, ``PYG``, and ``PYGFIELD``.
        """
        # Local shortcuts for readability
        bh_design = self.bh_design
        sim_params = self.sim_params
        soil_props = self.soil_props

        # Set sample index and flow conditions
        bh_design.m_flow = sim_params.m_flow[0]
        sim_params.isample = isample

        # Custom pipe configuration
        bh_design.customPipe = bh_design.get_custom_pipe()
        custom_pipe = bh_design.customPipe

        ag = None
        result = None

        # Model selection
        if (sim_params.run_type == SimulationParameters.TIN) and (
            sim_params.model_type == SimulationParameters.FINVOL
        ):
            b2g = B2G(custom_pipe)

            (
                hours,
                Q_b,
                flowrate,
                qsign,
                T_fi,
                T_fo,
                T_bave,
                z,
                T_b,
                T_f,
                qzb,
                h_fpipes,
                result,
                zstart,
                zend,
            ) = b2g.runsimulation(bh_design, soil_props, sim_params)

            zseg = z
            ag = b2g.ag

            # calculate interpolated k_s, k_g, Tg
            k_s = soil_props.get_k_s(zstart, zend, sim_params.isample)
            k_g = bh_design.get_k_g(zstart, zend)
            Tg = soil_props.getTg(zseg)

        elif sim_params.model_type == SimulationParameters.ANALYTICAL:
            b2g_ana = B2G_ana(custom_pipe, soil_props, sim_params)

            (
                hours,
                Q_b,
                flowrate,
                qsign,
                T_fi,
                T_fo,
                T_bave,
                z,
                zseg,
                T_b,
                T_f,
                qzb,
                h_fpipes,
            ) = b2g_ana.runsimulation()

            # calculate interpolated k_s, k_g, Tg
            zz = np.linspace(
                custom_pipe.b.D,
                custom_pipe.b.D + custom_pipe.b.H,
                sim_params.nsegments + 1,
            )

            k_s = soil_props.get_k_s(zz[0:-1], zz[1:], sim_params.isample)
            k_g = bh_design.get_k_g(zz[0:-1], zz[1:])
            Tg = soil_props.getTg(zseg)

        elif sim_params.model_type == SimulationParameters.PYG:
            pyg_ana = PYG_ana(custom_pipe, soil_props, sim_params)

            (
                hours,
                Q_b,
                flowrate,
                qsign,
                T_fi,
                T_fo,
                T_bave,
                z,
                zseg,
                T_b,
                T_f,
                qzb,
                h_fpipes,
            ) = pyg_ana.runsimulation()

            zz = np.linspace(
                custom_pipe.b.D,
                custom_pipe.b.D + custom_pipe.b.H,
                sim_params.nsegments + 1,
            )

            k_s = soil_props.get_k_s(zz[0:-1], zz[1:], sim_params.isample)
            k_g = bh_design.get_k_g(zz[0:-1], zz[1:])
            Tg = soil_props.getTg(zseg)

        elif sim_params.model_type == SimulationParameters.PYGFIELD:
            pygfield_ana = PYGFIELD_ana(bh_design, custom_pipe, soil_props, sim_params)
            self.pygfield_ana = pygfield_ana

            (
                hours,
                Q_b,
                flowrate,
                qsign,
                T_fi,
                T_fo,
                T_bave,
                z,
                zseg,
                T_b,
                T_f,
                qzb,
                h_fpipes,
            ) = pygfield_ana.runsimulation()

            zz = np.linspace(
                custom_pipe.b.D,
                custom_pipe.b.D + custom_pipe.b.H,
                sim_params.nsegments + 1,
            )

            k_s = soil_props.get_k_s(zz[0:-1], zz[1:], sim_params.isample)
            k_g = bh_design.get_k_g(zz[0:-1], zz[1:])
            Tg = soil_props.getTg(zseg)

        else:
            sim_params.modelsupported()  # raises error
            return None

        # calculate the pumping pressure [bar]
        dploop, qloop = bh_design.calculate_dploop(T_f, z, flowrate, sim_params.eff)

        # build result object
        self.singlerun_result = SingleRunResult(
            hours,
            Q_b,
            flowrate,
            qsign,
            T_fi,
            T_fo,
            T_bave,
            dploop,
            qloop,
            z,
            zseg,
            T_b,
            T_f,
            qzb,
            bh_design.Re_in,
            bh_design.Re_out,
            (custom_pipe.nInlets + custom_pipe.nOutlets),
            k_s,
            k_g,
            Tg,
            result,
            ag,
        )

        return self.singlerun_result

    def visualize_pipes(self, filename: str | Path) -> None:
        """
        Visualize a cross-section of the borehole with the pipe configuration.

        Parameters
        ----------
        filename : str or Path
            Full file path (including `.png` extension) for saving the figure.

        Returns
        -------
        None
            The function saves the visualization to disk.
        """
        self.bh_design.visualize_pipes(filename)

    def plot_borefield_and_gfunc(self, filepath: str | Path) -> None:
        """
        Plot a 3D visualization of the borefield layout and its associated
        g-function, if the pygfield model is used in the simulation.

        Parameters
        ----------
        filepath : str or pathlib.Path
            Base output path. The function appends suffixes such as
            `'_borefield.png'` and `'_gfunction.png'`.

        Returns
        -------
        None
            The function saves the borefield and g-function visualizations.
        """
        if hasattr(self, "pygfield_ana"):
            # for curved boreholes use custom plotting method
            if isinstance(self.pygfield_ana.borefield, list):
                plt = visualize_3d_borehole_field(self.pygfield_ana.borefield)

            # for rectangular or circular straight boreholes use pygfunction plotting method
            else:
                plt = gt.borefield.Borefield.visualize_field(
                    self.pygfield_ana.borefield
                )

            filename = filepath.with_name(filepath.name + "_borefield.png")
            plt.savefig(filename)

            # plot g-function for borehole field
            plt = visualize_gfunc(self.pygfield_ana.gfunc)
            filename = filepath.with_name(filepath.name + "_gfunction.png")
            plt.savefig(filename)


def main_single_run_sim(config_file_path: Path | str) -> None:
    """
    Execute a complete SingleRun borehole heat exchanger (BHE) simulation,
    including optional optimization, result saving, and visualization.

    Parameters
    ----------
    config_file_path: str | Path
        The path to the `.json` configuration file.

    Workflow
    --------
    1. Parse and load the configuration file.
    2. Apply optional lithology-to-conductivity preprocessing.
    3. Optionally perform flow-rate or parameter optimization.
    4. Initialize a ``SingleRun`` simulation from the config.
    5. Execute the simulation.
    6. Save results into structured output directories.
    7. Generate visualizations:
        - Pipe cross-section
        - Borefield layout (for PYGFIELD)
        - Optional T-field (for FINVOL)

    Returns
    -------
    None
        The function writes outputs to disk and prints status information.
    """
    # Start time
    start_time = time.time()
    np.seterr(all="raise")

    # Load configuration
    keysneeded = []
    keysoptional = [
        "litho_k_param",
        "loadprofile",
        "borefield",
        "flow_data",
        "variables_config",
    ]
    config_dict = load_nested_config(config_file_path, keysneeded, keysoptional)

    config = SingleRunConfig(**config_dict)  # validated Pydantic object

    config.lithology_to_k = None
    # lithology to conductivity (optional)
    if config.litho_k_param:
        # in a single run always set the base case to True
        config.litho_k_param["basecase"] = True
        lithology_to_k = ProcessLithologyToThermalConductivity.from_config(
            LithologyConfig(**config.litho_k_param)
        )
        lithology_to_k.create_multi_thermcon_profiles()
        config.lithology_to_k = lithology_to_k

    # Optional optimization
    isample = -1

    if config.dooptimize:
        config_dump = config.model_dump()

        cop_crit = config.copcrit
        optimize_keys = config.optimize_keys
        optimize_bounds = config.optimize_keys_bounds

        print(f"Optimizing flow rate for COP: {cop_crit}")
        if config.dploopcrit:
            print(f"Maximum pressure constraint: {config.dploopcrit}")
        print(f"Optimizing keys: {optimize_keys}")
        print(f"Bounds: {optimize_bounds}")

        _, config_new = optimize_forkeys(
            config_dump, cop_crit, optimize_keys, optimize_bounds, isample
        )
        config = SingleRunConfig(**config_new)

    # run simulation
    single_run = SingleRun.from_config(config)
    result = single_run.run(isample)

    # output directory setup
    if config.run_name:
        runfolder = config.run_name
    else:
        runfolder = Path(config_file_path).stem
        config.run_name = runfolder

    out_dir = (
        config.base_dir / runfolder
    )  # Check if the runfolder already exists, and create it if not
    out_dir.mkdir(parents=True, exist_ok=True)  # creates all missing directories

    basename = f"{runfolder}_{config.model_type[0]}_{config.run_type[0]}"
    outpath = out_dir / basename

    # Save results
    save_singlerun_results(config, result, outpath)

    if config.model_type == "FINVOL":
        save_Tfield_res = config.save_Tfield_res
        if save_Tfield_res:
            if result.ag is not None:
                # Only save Tfield results if FINVOL model is used, so ag != None
                result.save_T_field_FINVOL(outpath)

    # visualizations
    pipe_image = out_dir / f"{basename}_bhdesign.png"
    single_run.visualize_pipes(pipe_image)

    if config.model_type == "PYGFIELD":
        single_run.plot_borefield_and_gfunc(outpath)

    # wrap up
    print("Calculation complete")

    elapsed = time.time() - start_time
    print(f"Elapsed time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main_single_run_sim(sys.argv[1])
