import matplotlib.pyplot as plt
import numpy as np
import pygfunction as gt
from matplotlib.ticker import AutoMinorLocator


def thermal_resistance_pipe(r_in: float, r_out: float, k_p: float) -> float:
    """
    Compute the conductive thermal resistance of a cylindrical pipe wall.

    Parameters
    ----------
    r_in : float
        Inner radius of the pipe (m).
    r_out : float
        Outer radius of the pipe (m).
    k_p : float
        Thermal conductivity of the pipe material (W/m·K).

    Returns
    -------
    float
        Thermal resistance of the pipe wall (m·K/W).
    """
    R_p = np.log(r_out / r_in) / (2 * np.pi * k_p)
    return R_p


def thermal_resistance_pipe_insulated(
    r_in: float, r_out: float, insu_dr: float, k_p: float, insu_k: float
) -> float:
    """
    Compute the conductive thermal resistance of a pipe with an insulated
    middle section of its wall thickness.

    The wall is divided into:
    - inner pipe material
    - insulated section
    - outer pipe material

    Parameters
    ----------
    r_in : float
        Inner radius of the pipe (m).
    r_out : float
        Outer radius of the pipe (m).
    insu_dr : float
        Fraction of the pipe wall thickness that is insulated (0–1).
    k_p : float
        Thermal conductivity of the pipe material (W/m·K).
    insu_k : float
        Thermal conductivity of the insulation (W/m·K).

    Returns
    -------
    float
        Total radial thermal resistance (m·K/W).
    """
    # Total wall thickness
    wall_thickness = r_out - r_in
    iso_thickness = wall_thickness * insu_dr

    # Locate insulation symmetrically in the wall
    r_iso_in = r_in + 0.5 * (wall_thickness - iso_thickness)
    r_iso_out = r_iso_in + iso_thickness

    # Compute resistances for each region
    R_inner = thermal_resistance_pipe(r_in, r_iso_in, k_p)
    R_iso = thermal_resistance_pipe(r_iso_in, r_iso_out, insu_k)
    R_outer = thermal_resistance_pipe(r_iso_out, r_out, k_p)

    R_p = R_inner + R_iso + R_outer

    return R_p


class CustomPipe(gt.pipes._BasePipe):
    """
    Pipe model with depth-dependent ambient temperatures.

    Supports U-tubes and multi-U-tubes with N inlet pipes and M outlet pipes.
    Uses pygfunction (Cimmino & Cook, 2022) for thermal resistance networks.

    Internal resistances are based on the multipole method of
    Claesson & Hellström (2011). Fluid properties are obtained via pygfunction.

    Contains information regarding the physical dimensions and thermal
    characteristics of the pipes and the grout material, as well as methods to
    evaluate fluid temperatures and heat extraction rates based on the work of
    Hellstrom [#Single-Hellstrom1991]_. Internal borehole thermal resistances
    are evaluated using the multipole method of Claesson and Hellstrom
    [#Single-Claesson2011b]_.

    The effective borehole thermal resistance is evaluated using the method
    of Cimmino [#Single-Cimmin2019]_. This is valid for any number of pipes.

    References
    ----------
    .. [#Cimmino2022]  Cimmino, M., & Cook, J.C. (2022). pygfunction 2.2: New features and improvements in accuracy and computational efficiency.
        In Research Conference Proceedings, IGSHPA Annual Conference 2022 (pp. 45-52).
        International Ground Source Heat Pump Association. DOI: https://doi.org/10.22488/okstate.22.00001
    .. [#Single-Hellstrom1991] Hellstrom, G. (1991). Ground heat storage.
       Thermal Analyses of Duct Storage Systems I: Theory. PhD Thesis.
       University of Lund, Department of Mathematical Physics. Lund, Sweden.
    .. [#Single-Claesson2011b] Claesson, J., & Hellstrom, G. (2011).
       Multipole method to calculate borehole thermal resistances in a borehole
       heat exchanger. HVAC&R Research, 17(6), 895-911.
    .. [#Single-Cimmin2019] Cimmino, M. (2019). Semi-analytical method for
       g-function calculation of bore fields with series- and
       parallel-connected boreholes. Science and Technology for the Built
       Environment, 25 (8), 1007-1022.

    """

    def __init__(
        self,
        pos,
        r_in,
        r_out,
        borehole,
        k_g,
        k_p,
        J=3,
        nInlets=1,
        m_flow=1.0,
        T_f=10,
        fluid_str="Water",
        percent=100,
        epsilon=1e-6,
        ncalcsegments=1,
        R_p=[],
    ):
        """
        Initialize a custom borehole pipe model and compute its thermal and
        hydraulic properties.

            Parameters
        ----------
        pos : list of (float, float)
            Pipe coordinates inside the borehole.
        r_in : float or array_like
            Inner radius of the pipes (m).
        r_out : float or array_like
            Outer radius of the pipes (m).
        borehole : gt.boreholes.Borehole
            Borehole geometry object.
        k_g : float
            Grout thermal conductivity (W/m·K).
        k_p : float
            Pipe thermal conductivity (W/m·K).
        J : int, optional
            Number of multipoles per pipe. Default is 3.
        nInlets : int, optional
            Number of inlet pipes. Default is 1.
        m_flow : float, optional
            Mass flow rate (kg/s). Default is 1.0.
        T_f : float, optional
            Inlet fluid temperature (°C). Default is 10.
        fluid_str : str, optional
            Fluid type. Default is "Water".
        percent : float, optional
            Fluid mixture percentage. Default is 100.
        epsilon : float, optional
            Pipe roughness. Default is 1e-6.
        ncalcsegments : int, optional
            Number of segments for thermal resistance evaluation.
        R_p : list or array, optional
            Precomputed pipe thermal resistances.

        Attributes
        ----------
        R_p : list of float
            Pipe thermal resistances (m·K/W).
        h_f : ndarray
            Convective heat transfer coefficient per pipe.
        Rd : ndarray
            Δ-circuit thermal resistance per segment.
        R : ndarray
            Thermal resistance matrix.
        R1 : ndarray
            Inverse thermal resistance matrix.
        m_flow_pipe : ndarray
            Mass flow per pipe.

        Notes
        -----
        The expected array shapes of input parameters and outputs are documented
        for each class method. `nInlets` and `nOutlets` are the number of inlets
        and outlets to the borehole, and both are equal to 1 for a single U-tube
        borehole. `nSegments` is the number of discretized segments along the
        borehole. `nPipes` is the number of pipes (i.e. the number of U-tubes) in
        the borehole, equal to 1. `nDepths` is the number of depths at which
        temperatures are evaluated.
        """
        self.pos = pos
        self.nPipes = len(pos)

        # convert to arrays if needed
        if np.isscalar(r_in):
            r_in = r_in * np.ones(self.nPipes)
        self.r_in = r_in
        if np.isscalar(r_out):
            r_out = r_out * np.ones(self.nPipes)

        self.r_out = r_out
        self.b = borehole
        self.k_s = 1.0
        self.k_g = k_g
        self.k_p = k_p

        self.J = J
        self.nInlets = nInlets
        self.nOutlets = self.nPipes - self.nInlets
        self.ncalcsegments = ncalcsegments

        # Pipe thermal resistances
        if len(R_p) == 0:
            rp = thermal_resistance_pipe(r_in, r_out, k_p)
            self.R_p = []
            for i in range(ncalcsegments):
                self.R_p.append(rp)
        else:
            self.R_p = R_p

        # Initialize  flow rate and fluid properties including fluid resistisity with pipes
        self.m_flow = m_flow
        self.m_flow_pipe = m_flow * np.ones(self.nPipes)
        self.m_flow_pipe[: self.nInlets] = m_flow / self.nInlets
        self.m_flow_pipe[self.nInlets :] = -m_flow / self.nOutlets

        # fluid
        fluid = gt.media.Fluid(fluid_str, percent, T=T_f)

        self.cp_f = fluid.cp  # Fluid specific isobaric heat capacity (J/kg.K)
        self.rho_f = fluid.rho  # Fluid density (kg/m3)
        self.mu_f = fluid.mu  # Fluid dynamic viscosity (kg/m.s)
        self.k_f = fluid.k  # Fluid thermal conductivity (W/m.K)

        self.epsilon = epsilon

        self.h_f = np.zeros(self.nPipes)
        self.Rd = []

        # initalise flow scaling
        self.update_scaleflow(1.0)

        return

    @property
    def k_g(self) -> float:
        return self._k_g

    @k_g.setter
    def k_g(self, value: float) -> None:
        self._k_g = value

    @property
    def R(self) -> np.ndarray:
        return self._R

    @R.setter
    def R(self, value: np.ndarray) -> None:
        self._R = value

    @property
    def Rd(self) -> np.ndarray:
        return self._Rd

    @Rd.setter
    def Rd(self, value: np.ndarray) -> None:
        self._Rd = value

    @property
    def ncalcsegments(self) -> int:
        return self._ncalcsegments

    @ncalcsegments.setter
    def ncalcsegments(self, value: int) -> None:
        self._ncalcsegments = value

    def create_multi_u_tube(self):
        """
        Build a standard pygfunction U-tube / multi-U-tube object
        using depth-independent pipe properties.

        Returns
        -------
        SingleUTube or MultipleUTube
            pygfunction pipe object.
        """
        pos = self.pos
        rp_in = self.r_in
        rp_out = self.r_out
        borehole = self.b

        k_s = np.average(self.k_s)
        k_g = np.average(self.k_g)
        h_f = self.h_f[0]

        R_f_ser = 1.0 / (h_f * 2 * np.pi * rp_in)
        R_p = self.R_p
        # uniform pipe and fluid resisitivty
        Rfp = R_f_ser[0] + R_p[0][0]

        if len(rp_in) == 2:
            single_u_tube = gt.pipes.SingleUTube(
                pos, rp_in[0], rp_out[0], borehole, k_s, k_g, Rfp
            )
            single_u_tube.h_f = h_f
            return single_u_tube

        else:
            utube = gt.pipes.MultipleUTube(
                pos,
                rp_in[0],
                rp_out[0],
                borehole,
                k_s,
                k_g,
                Rfp,
                nPipes=self.nInlets,
                config="parallel",
            )
            utube.h_f = h_f
            return utube

    def update_scaleflow(self, scaleflow: float = 1.0) -> None:
        """
        Update the flow scaling factor and recalculate convective and thermal
        resistances.

        Parameters
        ----------
        scaleflow : float, optional
            Scaling multiplier applied to the mass flow rate. Default is 1.0.

        Notes
        -----
        Assumes that `k_g` and `k_s` are arrays of length `ncalcsegments`,
        allowing depth-dependent thermal properties.
        """
        self.scaleflow = scaleflow

        hfnew = np.ones(self.nPipes)
        for i in range(self.nPipes):
            hfnew[i] = gt.pipes.convective_heat_transfer_coefficient_circular_pipe(
                abs(self.m_flow_pipe[i] * self.scaleflow),
                self.r_in[i],
                self.mu_f,
                self.rho_f,
                self.k_f,
                self.cp_f,
                self.epsilon,
            )

        hfdif = np.subtract(hfnew, self.h_f)
        hfdot = np.dot(hfdif, hfdif)

        # Skip update if small change and sizes match
        if (self.ncalcsegments == len(self.Rd)) and (hfdot < 1):
            return
        else:
            self.h_f = hfnew

        self.R_f = 1.0 / (self.h_f * 2 * np.pi * self.r_in)

        # Delta-circuit thermal resistances
        self.update_thermal_resistances()

    def init_thermal_resistances(self, k_g: np.ndarray, R_p: list[np.ndarray]) -> None:
        """
        Initialize depth-dependent thermal resistances using provided
        conductivity and pipe resistance arrays.

        This routine is called from the B2G.runsimulation method, in order to generate thermal resistances based
        on actual segments determined by len(k_g) and len(R_p)

        Parameters
        ----------
        k_g : array_like
            Grout thermal conductivity for each depth segment.
        R_p : list of array_like
            Pipe thermal resistance values for each segment.
        """
        self.ncalcsegments = len(k_g)
        self.k_g = k_g
        self.R_p = R_p

        self.update_scaleflow(1.0)

        # Precompute inverses of resistance matrices
        self.R1 = []
        for i in range(self.ncalcsegments):
            R1 = np.linalg.inv(self.R[i])
            self.R1.append(R1)

    def update_thermal_resistances(self, initialize_stored_coeff: bool = False) -> None:
        """
        Update the delta-circuit of thermal resistances.

        This methods updates the values of the delta-circuit thermal
        resistances based on the provided fluid to outer pipe wall thermal
        resistance.

        Its dimension corresponds to ncalcsegments (which is dictated by b2g.py (nx nodes)
        or b2g_ana (nsegments) and takes into account depth dependent effects of insulation

        Parameters
        ----------
        initialize_stored_coeff : bool, optional
            If True, also reinitialize stored coefficients. Default is False.
        """
        self.R = []
        self.Rd = []

        for k in range(self.ncalcsegments):
            R_fp = self.R_f + self.R_p[k]

            # Delta-circuit thermal resistances
            (R, Rd) = gt.pipes.thermal_resistances(
                self.pos, self.r_out, self.b.r_b, self.k_s, self.k_g[k], R_fp, J=self.J
            )

            self.R.append(R)
            self.Rd.append(Rd)

            if initialize_stored_coeff:
                self._initialize_stored_coefficients()
        return

    def get_Rs(self, nyear: float, alpha: float = 1e-6) -> float:
        """
        Approximate long-term borehole resistance Rs using an analytical estimate.
        Calculate Rs for simple approximation for  Tb-T0 = Rs  qc

        Parameters
        ----------
        nyear : float
            Duration (years) used to compute the effective thermal resistance.
        alpha : float, optional
            Soil thermal diffusivity (m²/s). Default is 1e-6.

        Returns
        -------
        float
            Approximate long-term borehole resistance Rs (m·K/W).
        """
        r_b = self.b.r_b
        ts = nyear * 3600 * 24 * 365.25

        Rs = (np.log((4 * alpha * ts) / (r_b**2)) - np.euler_gamma) / (
            4 * np.pi * self.k_s
        )
        return Rs

    def get_temperature_depthvar(
        self,
        T_f_in: float,
        signpower: float | np.ndarray,
        Rs: np.ndarray,
        soil_props,
        nsegments: int = 10,
    ) -> tuple:
        """
        Compute fully depth-dependent inlet/outlet fluid temperatures, borehole
        wall temperatures, pipe temperatures, and heat extraction along the borehole.

        Parameters
        ----------
        T_f_in : float
            Inlet fluid temperature (°C).
        signpower : float
            Sign of the thermal load direction (±1).
        Rs : array_like
            Long-term borehole resistance values for each segment, based on approximation for  Tb-T0 = Rs  qc.
        soil_props : SoilProperties
            Soil properties object.
        nsegments : int, optional
            Number of depth segments. Default is 10.

        Returns
        -------
        tuple
            (T_f_out, power, Reff, pipe_temps, borehole_temps, segment_heat_flows)
        """
        bh = self.b

        hstep = bh.H / nsegments
        zmin = bh.D + 0.5 * hstep
        zmax = bh.D + bh.H - 0.5 * hstep
        zseg = np.linspace(zmin, zmax, nsegments)

        Tg_borehole = soil_props.getTg(zseg)
        qbz = Tg_borehole * 0.0

        R1 = np.copy(self._R)
        b = np.arange(nsegments, dtype=float)

        for i in range(nsegments):
            R1[i] = np.linalg.inv(self._R[i])
            b[i] = np.sum(R1[i] @ np.ones(self.nPipes))

        # storage arrays
        ptemp = np.arange((nsegments + 1) * self.nPipes, dtype=float).reshape(
            nsegments + 1, self.nPipes
        )
        Tb = np.arange(nsegments, dtype=float)
        Tf = Tb * 0.0

        # initialize the top temperatures (inlet)
        ptemp[0, : self.nInlets] = T_f_in

        # iterate for  T_f_out such that bottom temperatures become the same
        dtfout = 0
        dtempold = 0
        dtempnew = 1
        T_f_out = T_f_in + 1e-1 * signpower
        iterate = True

        while abs(dtempnew) > 1e-4 or iterate:
            # set outlet boundary condition guess
            ptemp[0, self.nInlets :] = T_f_out

            # loop over each segment
            for i in range(nsegments):
                # Tf is only for output purposes
                Tf[i] = np.average(ptemp[i])

                # prep next segment's temperatures
                ptemp[i + 1] = ptemp[i]

                # iteration variables within the segment
                dtemp = 1
                tseg = 0.5 * (ptemp[i] + ptemp[i + 1])

                # check that Rs[i]*b is not close to 1 if so modify with small number
                if Rs[i] < 0:
                    Rs[i] = abs(Rs[i])

                # iterate until pipe temperatures converge
                while np.dot(dtemp, dtemp) > 1e-10:
                    tsegold = tseg

                    a = np.sum(R1[i] @ tseg)
                    Tb[i] = (Rs[i] * a + Tg_borehole[i]) / (1 + Rs[i] * b[i])

                    q = R1[i] @ (tseg - Tb[i])

                    ptemp[i + 1] = ptemp[i] - q * hstep / (
                        self.m_flow_pipe * self.scaleflow * self.cp_f
                    )

                    tseg = 0.5 * (ptemp[i] + ptemp[i + 1])
                    dtemp = tseg - tsegold

                qbz[i] = -np.sum(q) * hstep

            dtempnew = np.sum(
                ptemp[nsegments, self.nInlets :] * self.m_flow_pipe[self.nInlets :]
            ) + np.sum(
                ptemp[nsegments, : self.nInlets] * self.m_flow_pipe[: self.nInlets]
            )

            # Update outlet temperature guess
            if abs(dtfout) > 0:
                g = dtfout / (dtempnew - dtempold)
                dtfout = -dtempnew * g
                iterate = False
            else:
                dtfout = 1e-1
                iterate = True

            dtempold = dtempnew
            T_f_out += dtfout

        # Final power and effective resistance
        power = (T_f_out - T_f_in) * self.m_flow * self.scaleflow * self.cp_f

        if abs(np.sum(qbz) - power) > 1:
            print("power is not sumq (sumq, power):", np.sum(qbz), ",", power)

        if abs(power) > 1e-3:
            Reff = -np.average(Tf - Tb) * bh.H / power
        else:
            Reff = -1

        return T_f_out, power, Reff, ptemp, Tb, qbz

    def get_temperature_depthvar_power(
        self, power: float | np.ndarray, Rs: np.ndarray, soil_props, nsegments: int = 10
    ) -> tuple:
        """
        Compute inlet and outlet temperatures to satisfy a prescribed power extraction.

        Parameters
        ----------
        power : float
            Target borehole heat extraction rate (W).
        Rs : array_like
            Long-term borehole resistance per segment, based on approximation for  Tb-T0 = Rs  qc.
        soil_props : SoilProperties
            Soil properties object.
        nsegments : int, optional
            Number of depth segments. Default is 10.

        Returns
        -------
        tuple
            (T_f_out, T_f_in, Reff, pipe_temps, Tb, qbz)
        """
        bh = self.b

        # Initial guess for inlet temperature (assume same as soil at borehole top)
        T_f_in = soil_props.getTg(bh.D)

        # Initialize iteration variables
        dpowerold = 0
        dpowernew = 1
        dtfin = 0

        # Iteratively adjust inlet temperature to meet target power
        iterate = True
        while abs(dpowernew) > 1e-3 or iterate:
            (T_f_out, newpower, Reff, ptemp, Tb, qbz) = self.get_temperature_depthvar(
                T_f_in, np.sign(power), Rs, soil_props, nsegments=nsegments
            )

            # Compute difference between computed and target power
            dpowernew = newpower - power

            if abs(dtfin) > 0:
                # Use previous iteration to accelerate convergence (gain factor)
                gain = dtfin / (dpowernew - dpowerold)
                dtfin = -dpowernew * gain
                iterate = False
            else:
                # If first iteration, use small fixed step
                dtfin = 1e-1
                iterate = True

            dpowerold = dpowernew
            # Update inlet temperature for next iteration
            T_f_in += dtfin

        return T_f_out, T_f_in, Reff, ptemp, Tb, qbz

    def visualize_pipes(self):
        """
        Plot a cross-sectional diagram of the borehole and pipe layout.

        Returns
        -------
        matplotlib.figure.Figure
            Figure containing the visualization.
        """
        plt.rc("font", size=12)
        plt.rc("xtick", labelsize=12)
        plt.rc("ytick", labelsize=12)
        plt.rc("lines", lw=1.5, markersize=5.0)
        plt.rc("savefig", dpi=500)

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xlabel(r"$x$ [m]")
        ax.set_ylabel(r"$y$ [m]")
        ax.axis("equal")

        # Draw major and minor tick marks inwards
        ax.tick_params(
            axis="both",
            which="both",
            direction="in",
            bottom=True,
            top=True,
            left=True,
            right=True,
        )

        # Auto-adjust minor tick marks
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())

        # Color cycle
        colors = plt.cm.tab20.colors
        lw = plt.rcParams["lines.linewidth"]

        # Borehole wall outline
        ax.plot(
            [-self.b.r_b, 0.0, self.b.r_b, 0.0],
            [0.0, self.b.r_b, 0.0, -self.b.r_b],
            "k.",
            alpha=0.0,
        )
        borewall = plt.Circle(
            (0.0, 0.0), radius=self.b.r_b, fill=False, color="k", linestyle="--", lw=lw
        )
        ax.add_patch(borewall)

        # Pipes
        for i in range(self.nPipes):
            # Coordinates of pipes
            (x_in, y_in) = self.pos[i]

            # Pipe outline (inlet)
            pipe_in_in = plt.Circle(
                (x_in, y_in),
                radius=self.r_in[i],
                fill=False,
                linestyle="-",
                color=colors[i],
                lw=lw,
            )
            pipe_in_out = plt.Circle(
                (x_in, y_in),
                radius=self.r_out[i],
                fill=False,
                linestyle="-",
                color=colors[i],
                lw=lw,
            )

            ax.text(x_in, y_in, i, ha="center", va="center")
            ax.add_patch(pipe_in_in)
            ax.add_patch(pipe_in_out)

        plt.tight_layout()
        return fig
