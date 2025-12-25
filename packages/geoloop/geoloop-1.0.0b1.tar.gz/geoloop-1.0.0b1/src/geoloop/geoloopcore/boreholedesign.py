from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pygfunction as gt
from pygfunction.media import Fluid
from scipy import optimize

from geoloop.configuration import SingleRunConfig
from geoloop.geoloopcore.CoaxialPipe import CoaxialPipe
from geoloop.geoloopcore.CustomPipe import (
    CustomPipe,
    thermal_resistance_pipe,
    thermal_resistance_pipe_insulated,
)
from geoloop.geoloopcore.strat_interpolator import StratInterpolator


class BoreholeDesign:
    COAXIAL: str = "COAXIAL"
    """Configuration type for coaxial pipes."""

    UTUBE: str = "UTUBE"
    """Configuration type for U-tube pipes."""

    """
    Representation of a borehole heat exchanger (BHE) design, including
    geometric properties, pipe configuration, and material parameters.

    The class supports two configurations:

    **COAXIAL**
        - One inlet (outer pipe) and one outlet (inner pipe).
        - Pipes are concentric and centered at (0, 0).
        - No `pos` specification is needed.

    **UTUBE**
        - One or more inlet and outlet pipes.
        - Pipes are arranged radially symmetric around the borehole center.
        - Inlets are assumed connected to outlets at the borehole bottom.
        - Radial positions must be constant for all inlets and constant for
          all outlets.

    Notes
    -----
    - Depth-dependent grout conductivity is supported via interpolation.
    - Optional thermal insulation can be applied to the outlet pipe(s).
    - For PYGFIELD models, additional parameters define field layout and
      borehole inclination.
    """

    def __init__(
        self,
        type: str,
        H: float,
        D: float,
        r_b: float,
        r_in: list[float],
        r_out: list[float],
        k_p: float | list[float],
        k_g: float | list[float],
        pos: list[list[float]] = [[0.0, 0.0], [0.0, 0.0]],
        J: int = 3,
        nInlets: int = 1,
        m_flow: float = 1.0,
        T_f: float = 10.0,
        fluid_str: str = "Water",
        fluid_percent: float = 100.0,
        epsilon: float = 1e-6,
        z_k_g: list[float] | None = None,
        ncalcsegments: int = 1,
        insu_z: float = 0.0,
        insu_dr: float = 0.0,
        insu_k: float = 0.03,
        N: int = 1,
        M: int = 1,
        R: float = 3.0,
        inclination_start: float = 0.0,
        inclination_end: float = 0.0,
        num_tiltedsegments: int = 1,
    ) -> None:
        """
        Initialize a borehole design with geometry, pipe configuration, and material
        properties.

        Parameters
        ----------
        type : {"COAXIAL", "UTUBE"}
            Borehole configuration type.
        H : float
            Borehole length (m).
        D : float
            Buried depth of borehole top (m).
        r_b : float
            Borehole radius (m).
        r_in : array_like
            Inner radii of pipe(s) (m).
        r_out : array_like
            Outer radii of pipe(s) (m).
        k_p : float or array_like
            Thermal conductivity of the pipe material (W/m·K).
        k_g : float or array_like
            Grout thermal conductivity. If array-like, depth-dependent values
            must be supplied along with `z_k_g`.
        pos : tuple of float, optional
            Radial position of pipe(s) for UTUBE layouts. Ignored for COAXIAL.
        J : int, optional
            Number of segments used in `pygfunction` internal pipe discretization.
        nInlets : int, optional
            Number of inlet pipes (UTUBE).
        m_flow : float, optional
            Mass flow rate of circulating fluid (kg/s).
        T_f : float, optional
            Initial fluid temperature (°C).
        fluid_str : {"Water", "MPG", "MEG", "MMA", "MEA"}, optional
            Fluid type for hydraulic and thermal properties.
        fluid_percent : float, optional
            Percentage of the working fluid relative to water.
        epsilon : float, optional
            Pipe roughness for hydraulic calculations (m).
        z_k_g : array_like, optional
            Depth breakpoints corresponding to grout thermal conductivities.
        ncalcsegments : int, optional
            Number of vertical discretization segments for thermal calculations.
        insu_z : float, optional
            Depth up to which outlet pipes are insulated (m).
        insu_dr : float, optional
            Fraction of pipe wall thickness that is insulated.
        insu_k : float, optional
            Insulation thermal conductivity (W/m·K).
        N, : int, optional
            Total nr of boreholes in borehole field for PYGFIELD models.
        M : int, optional
            Boreholes per side of the borehole field for PYGFIELD models (only equally sided fields are supported).
        R : float, optional
            Borefield radius or spacing parameter.
        inclination_start : float, optional
            Start angle of borehole inclination (degrees).
        inclination_end : float, optional
            End angle of borehole inclination (degrees).
        num_tiltedsegments : int, optional
            Number of segments for inclined/tilted borehole discretization.

        Notes
        -----
        - The thermal resistance of insulated pipes is computed in `getR_p`.
        - Depth-dependent grout conductivity is evaluated via `StratInterpolator`.
        - A `CustomPipe` or `CoaxialPipe` object is created automatically.
        """
        self.D = D
        self.H = H
        self.r_b = r_b
        self.r_in = np.asarray(r_in)
        self.r_out = np.asarray(r_out)
        self.n_p = len(r_out)
        self.nInlets = nInlets
        self.k_p = k_p * np.ones(self.n_p)
        self.pos = np.asarray(pos)
        self.ncalcsegments = ncalcsegments

        dz = H / ncalcsegments
        zmin = D + 0.5 * dz
        zmax = D + H - 0.5 * dz
        self.zseg = np.linspace(zmin, zmax, ncalcsegments)

        self.k_g = np.atleast_1d(k_g)
        if z_k_g == None:
            self.z_k_g = np.ones_like(k_g)
        else:
            self.z_k_g = np.asarray(z_k_g)

        self.interpolatorKg = StratInterpolator(self.z_k_g, self.k_g, stepvalue=True)

        self.type = type
        self.J = J
        self.m_flow = m_flow
        self.T_f = T_f
        self.fluid_str = fluid_str
        self.fluid_percent = fluid_percent
        self.epsilon = epsilon

        self.insu_z = insu_z
        self.insu_k = insu_k
        self.insu_dr = insu_dr

        # (JDvW) I think these can be set to None creating the borehole design object, only created from config with None
        self.Re_in = None
        self.Re_out = None

        self.N = N
        self.M = M
        self.R = R
        self.inclination_start = inclination_start
        self.inclination_end = inclination_end
        self.num_tiltedsegments = num_tiltedsegments

        # modify the R_p for the insulated part assume the thickness of the r_in/r_out constant

        self.customPipe = self.get_custom_pipe()

    def get_r_p(self, z: np.ndarray) -> list[np.ndarray]:
        """
        Compute pipe thermal resistance at specific depths.

        Insulation is applied only to outlet pipes (i.e., pipes with index
        ``>= nInlets``) and only for depths shallower than `insu_z`.

        Parameters
        ----------
        z : array_like of float
            Depth values (m) at which pipe resistances are evaluated.

        Returns
        -------
        list of ndarray
            List containing pipe resistances for each depth.
            Each entry contains an array of size ``n_p``.
        """
        npipes = len(self.r_out)

        R_p = []
        for i in range(len(z)):
            rp = thermal_resistance_pipe(self.r_in, self.r_out, self.k_p)
            if (self.insu_z > 0) and (z[i] < self.insu_z):
                for ip in range(self.nInlets, npipes):
                    if self.insu_dr > 0:
                        rp[ip] = thermal_resistance_pipe_insulated(
                            self.r_in[ip],
                            self.r_out[ip],
                            self.insu_dr,
                            self.k_p[ip],
                            self.insu_k,
                        )
            R_p.append(rp)

        return R_p

    def get_k_g(self, zstart: Sequence[float], zend: Sequence[float]) -> np.ndarray:
        """
        Interpolate grout conductivity for a list of vertical intervals.

        Parameters
        ----------
        zstart : sequence of float
            Lower bounds of intervals.
        zend : sequence of float
            Upper bounds of intervals.

        Returns
        -------
        np.ndarray
            Grout conductivity per interval.
        """
        k_g = self.interpolatorKg.interp(zstart, zend)

        return k_g

    def get_custom_pipe(self) -> CustomPipe:
        """
        Construct and return the appropriate pipe model instance (CoaxialPipe or CustomPipe).

        Returns
        -------
        CoaxialPipe | CustomPipe
            Constructed pipe representation compatible with the rest of the code.
        """
        # create pygfunction borehole
        self.borehole = gt.boreholes.Borehole(self.H, self.D, self.r_b, x=0.0, y=0.0)

        # compute grout thermal conductivity with depth
        zz = np.linspace(self.D, self.D + self.H, self.ncalcsegments + 1)
        k_g = self.get_k_g(zz[:-1], zz[1:])

        # compute pipe resistances
        R_p = self.get_r_p(self.zseg)

        custom_pipe = None
        if self.type == BoreholeDesign.COAXIAL:
            custom_pipe = CoaxialPipe(
                self.r_in,
                self.r_out,
                self.borehole,
                k_g,
                self.k_p,
                J=self.J,
                m_flow=self.m_flow,
                fluid_str=self.fluid_str,
                percent=self.fluid_percent,
                epsilon=self.epsilon,
                ncalcsegments=self.ncalcsegments,
                R_p=R_p,
                T_f=self.T_f,
            )
        elif self.type == BoreholeDesign.UTUBE:
            custom_pipe = CustomPipe(
                self.pos,
                self.r_in,
                self.r_out,
                self.borehole,
                k_g,
                self.k_p,
                J=self.J,
                nInlets=self.nInlets,
                m_flow=self.m_flow,
                fluid_str=self.fluid_str,
                percent=self.fluid_percent,
                epsilon=self.epsilon,
                ncalcsegments=self.ncalcsegments,
                R_p=R_p,
            )
        else:
            print(
                "error in BoreholeDesign:getCustomPipe type of boreholedesign not recognized ",
                self.type,
            )

        return custom_pipe

    @classmethod
    def from_config(cls, config: SingleRunConfig) -> "BoreholeDesign":
        """
        Create a BoreholeDesign instance from a configuration object.

        The configuration object should contain keys consistent with the
        `BoreholeDesign` constructor arguments.

        Parameters
        ----------
        config : SingleRunConfig
            Object containing borehole design parameters.

        Returns
        -------
        BoreholeDesign
            Configured instance.
        """
        if config.r_in is None:
            # Example: derive inner radius from r_out using SDR
            r_out = np.asarray(config.r_out)
            if config.SDR:
                config.r_in = r_out - ((2 * r_out) / config.SDR)
            else:
                raise ValueError("r_in missing and no SDR provided.")

        return cls(
            type=config.type,
            H=config.H,
            D=config.D,
            r_b=config.r_b,
            r_in=config.r_in,
            r_out=config.r_out,
            k_p=config.k_p,
            k_g=config.k_g,
            pos=config.pos,
            nInlets=config.nInlets,
            m_flow=config.m_flow,
            T_f=config.Tin,
            fluid_str=config.fluid_str,
            fluid_percent=config.fluid_percent,
            epsilon=config.epsilon,
            z_k_g=config.z_k_g,
            ncalcsegments=config.nsegments,
            insu_z=config.insu_z,
            insu_dr=config.insu_dr,
            insu_k=config.insu_k,
            N=config.field_N,
            M=config.field_M,
            R=config.field_R,
            inclination_start=config.field_inclination_start,
            inclination_end=config.field_inclination_end,
            num_tiltedsegments=config.field_segments,
        )

    def visualize_pipes(self, filename: str | Path) -> None:
        """
        Vsualize the borehole design, including pipe layout and create a figure.

        Parameters
        ----------
        filename : str
            Output path for the saved figure.

        Returns
        -------
        None

        """
        fig = self.customPipe.visualize_pipes()
        fig.savefig(filename)

    def fluid_friction_factor(
        self,
        ipipe: int,
        m_flow_pipe: float,
        mu_f: float,
        rho_f: float,
        epsilon: float,
        tol: float = 1e-6,
    ) -> tuple[float, float, float]:
        """
        Evaluate the Darcy-Weisbach friction factor. It calculates the hydraulic diameter D, and the cross_section flow
        area, depending on the pipe configuration.

        Parameters
        ----------
        m_flow_pipe : float
            Fluid mass flow rate (in kg/s) into the pipe.
        mu_f : float
            Fluid dynamic viscosity (in kg/m-s).
        rho_f : float
            Fluid density (in kg/m3).
        epsilon : float
            Pipe roughness (in meters).
        tol : float
            Relative convergence tolerance on Darcy friction factor.
            Default is 1.0e-6.

        Returns
        -------
        fDarcy : float
            Darcy friction factor.
        dpdl: float
            Pressure loss
        Re : float
            Reynolds number.
        """
        if (self.type == BoreholeDesign.UTUBE) or (ipipe == 1):
            # Hydraulic diameter
            D_h = 2.0 * self.r_in[ipipe]
            A_cs = np.pi * self.r_in[ipipe] ** 2
        else:
            # hydraulic parameters for coaxial
            A_cs = np.pi * (self.r_in[0] ** 2 - self.r_out[1] ** 2)
            D_h = 2 * (self.r_in[0] - self.r_out[1])

        # Relative roughness
        E = epsilon / D_h
        # Fluid velocity
        V_flow = m_flow_pipe / rho_f
        V = V_flow / A_cs
        # Reynolds number
        Re = rho_f * V * D_h / mu_f

        if Re == 0:
            fDarcy = np.nan
        elif Re < 2.3e3:
            # Darcy friction factor for laminar flow
            fDarcy = 64.0 / Re
        else:
            # Colebrook-White equation for rough pipes
            fDarcy = 0.02
            df = 1.0e99
            while abs(df / fDarcy) > tol:
                one_over_sqrt_f = -2.0 * np.log10(
                    E / 3.7 + 2.51 / (Re * np.sqrt(fDarcy))
                )
                fDarcy_new = 1.0 / one_over_sqrt_f**2
                df = fDarcy_new - fDarcy
                fDarcy = fDarcy_new

        dpdl = fDarcy * 0.5 * rho_f * V * V / D_h

        return fDarcy, dpdl, Re

    def dploop_nosyphon(
        self, tempfluid: np.ndarray, flowrate: np.ndarray, effpump: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute loop pressure drop (no syphon) and pumping power.

        Parameters
        ----------
        tempfluid : ndarray
            Fluid temperature time series (°C).
        flowrate : ndarray
            Mass flow rate time series (kg/s).
        effpump : float
            Pump efficiency (0–1).

        Returns
        -------
        dpsumtime : ndarray
            Pressure drop time series (bar).
        qpump : ndarray
            Power [W] required to drive the pumping
        """
        qpump = flowrate * 0
        dpsumtime = flowrate * 0
        f = Fluid(self.fluid_str, self.fluid_percent, T=tempfluid)

        ipipes = [0, self.n_p - 1]
        npipes = [self.nInlets, self.n_p - self.nInlets]

        Re_in_out = np.ones((len(ipipes), len(flowrate)))

        for itime in range(len(flowrate)):
            dpsum = 0

            for ip in range(len(ipipes)):
                ipipe = ipipes[ip]  # Index of the current pipe
                mflow = flowrate / npipes[ip]  # Distribute flowrate across pipes

                # Get dynamic viscosity and density for the fluid at the current temperature
                mu_f = f.dynamic_viscosity()
                rho_f = f.density()

                # Calculate friction factor, pressure drop, and Reynolds number
                fDarcy, dpdl, Re = self.fluid_friction_factor(
                    ipipe, mflow[itime], mu_f, rho_f, self.epsilon
                )

                # Sum the pressure drop over the borehole height
                dpsum += dpdl * self.borehole.H

                # Store the Reynolds nr. for the different pipes over time in one array
                Re_in_out[ip, itime] = Re

            # Calculate the required pumping power for this time step
            qpump[itime] = dpsum * (flowrate[itime] / rho_f) / effpump

            # Store the pressure drop at this time step
            dpsumtime[itime] = dpsum

            # store the reynolds nr. over time for the inlet and outlet pipes separately
            self.Re_in = Re_in_out[0]
            self.Re_out = Re_in_out[1]

        # Return the total pressure drop (converted to bar) and pumping power (W)
        return dpsumtime / 1e5, qpump

    def findflowrate_dploop(
        self,
        dplooptarget: float,
        tempfluid: np.ndarray,
        flowrate: float,
        effpump: float,
    ) -> float:
        """
        Calculate flowrate matching with dplooptarget based on root finding algorithm
        (brentq is used with a scaling of the given flowrate, in range 0.01-10).

        Parameters
        ----------
        dplooptarget : float
            Target pumping pressure (bar).
        tempfluid : ndarray
            Fluid temperatures (°C).
        flowrate : float
            Initial flow rate (kg/s) used as scale reference.
        effpump : float
            Pump efficiency.

        Returns
        -------
        float
            Mass flow rate (kg/s) that results in the desired pumping pressure.
        """

        sol = optimize.root_scalar(
            self.root_func_dploop,
            args=(dplooptarget, tempfluid, flowrate, effpump),
            bracket=[0.01, 100],
            method="brentq",
        )
        return sol.root

    def root_func_dploop(
        self,
        mflowscale: float,
        dplooptarget: float,
        tempfluid: np.ndarray,
        flowrate: float,
        effpump: float,
    ) -> float:
        """
        Objective function used by ``findflowrate_dploop`` for root finding function.

        Parameters
        ----------
        mflowscale : float
            Scaling factor applied to nominal flow rate.
        dplooptarget : float
            Target pumping pressure (bar).
        tempfluid : ndarray
            Fluid temperatures (°C).
        flowrate : float
            Nominal mass flow rate (kg/s).
        effpump : float
            Pump efficiency.

        Returns
        -------
        float
            Difference between actual and target pumping pressure.
        """
        dploop, _ = self.dploop_nosyphon(tempfluid, flowrate * mflowscale, effpump)

        return max(dploop) - dplooptarget

    def calculate_dploop(
        self, T_f: np.ndarray, z: np.ndarray, flowrate: np.ndarray, effpump: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Pumping pressure, pumping power and the Reynolds number are calculated for the in- and outlets in the loop. Assumption is that the flow and temperature are
        divided equally and symmetrically over the pipes. (i.e. the pipe diameters of respectively the inlet and outlet
        pipes is the same and the in- and oulet pipes alternate in the pipe design).
        Re_in, Re_uit are stored over time (Re_in represents the Reynolds number that is the same in all inlets, Re_out represents the Reynolds number that represents all outlets)

        Parameters
        ----------
        T_f : ndarray
            Fluid temperature profile [ntime, nz, npipes] (°C).
        z : ndarray
            Along hole depth discretization (m).
        flowrate : ndarray
            Mass flow rate time series (kg/s).
        effpump : float
            Pump efficiency.

        Returns
        -------
        dpsumtime : ndarray
            Pumping pressure (bar) for each time.
        qpump : ndarray
            Pumping power (W) for each time.
        """
        nz = len(z)
        qpump = flowrate * 0
        dpsumtime = flowrate * 0

        ipipes = [0, self.n_p - 1]
        npipes = [self.nInlets, self.n_p - self.nInlets]
        rhosum = [0, 0]

        Re_meanz = np.ones(
            (len(ipipes), len(flowrate))
        )  # Store average Re for each time step

        for itime in range(len(flowrate)):
            dpsum = 0

            for ip in range(len(ipipes)):
                ipipe = ipipes[ip]
                mflow = flowrate / (npipes[ip])
                tz = T_f[itime, :, ipipe].reshape(nz)
                Resum = 0
                rhosum[ip] = 0

                for k in range(nz):
                    try:
                        f = Fluid(self.fluid_str, self.fluid_percent, T=tz[k])
                    except:
                        print("Error in def dploop")
                        return

                    mu_f = f.dynamic_viscosity()
                    rho_f = f.density()
                    fDarcy, dpdl, Re = self.fluid_friction_factor(
                        ipipe, mflow[itime], mu_f, rho_f, self.epsilon
                    )
                    Resum += Re

                    if k > 0:
                        dpsum += 0.5 * dpdl * (z[k] - z[k - 1])
                        rhosum[ip] += rho_f * (z[k] - z[k - 1])
                    if k < len(tz) - 1:
                        dpsum += 0.5 * dpdl * (z[k + 1] - z[k])
                        rhosum[ip] += rho_f * (z[k + 1] - z[k])

                # Store the depth-average reynold nr over depth for the different pipes over time in one array
                Re_meanz[ip, itime] = Resum / nz

            dprho = (rhosum[1] - rhosum[0]) * 9.81

            dpsum += dprho
            qpump[itime] = dpsum * (flowrate[itime] / rho_f) / effpump
            dpsumtime[itime] = dpsum

        # Store Re values for in- and outlet pipes separately
        self.Re_in = Re_meanz[0]
        self.Re_out = Re_meanz[1]

        return dpsumtime / 1e5, qpump  # Return pressure in bar
