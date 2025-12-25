import numpy as np
import pygfunction as gt

from geoloop.geoloopcore.CustomPipe import CustomPipe, thermal_resistance_pipe
from geoloop.geoloopcore.soilproperties import SoilProperties


def Swap(arr: np.ndarray, start_index: int, last_index: int) -> None:
    """
    Swap two columns in an array, in place, from start_index to last_index.

    Parameters
    ----------
    arr : np.ndarray
        2D array where columns will be swapped.
    start_index : int
        Index of the first column to swap.
    last_index : int
        Index of the second column to swap.

    Returns
    -------
    None
        The operation is performed in place.
    """

    arr[:, [start_index, last_index]] = arr[:, [last_index, start_index]]


class CoaxialPipe(CustomPipe):
    """
    This class is used to evaluate the thermal resistance network of a Coaxial borehole.

    In its default mode the object
    is marked by depth-indepedent design properties which can be altered, and can also access other methods from its baseclass
    CustomPipe.

    It uses pygfunction of Cimmino and Cook [#Cimmino2024]
    for the determination of the thermal resistivity network of the borehole

    It contains information regarding the physical dimensions and thermal
    characteristics of the pipes and the grout material, as well as methods (through its base class) to
    evaluate fluid temperatures and heat extraction rates based on the work of
    Hellstrom [#Single-Hellstrom1991]_. Internal borehole thermal resistances
    are evaluated using the multipole method of Claesson and Hellstrom
    [#Single-Claesson2011b]_.

    References
    ----------
    .. [#Cimmino2022]  Cimmino, M., & Cook, J.C. (2022). pygfunction 2.2: New features and improvements in accuracy and computational efficiency.
        In Research Conference Proceedings, IGSHPA Annual Conference 2022 (pp. 45-52).
        International Ground Source Heat Pump Association. DOI: https://doi.org/10.22488/okstate.22.000015.
    .. [#Single-Hellstrom1991] Hellstrom, G. (1991). Ground heat storage.
       Thermal Analyses of Duct Storage Systems I: Theory. PhD Thesis.
       University of Lund, Department of Mathematical Physics. Lund, Sweden.
    .. [#Single-Claesson2011b] Claesson, J., & Hellstrom, G. (2011).
       Multipole method to calculate borehole thermal resistances in a borehole
       heat exchanger. HVAC&R Research, 17(6), 895-911.
    """

    def __init__(
        self,
        r_in: np.ndarray | float,
        r_out: np.ndarray | float,
        borehole,
        k_g: float | np.ndarray,
        k_p: float | np.ndarray,
        k_s: float = 1.0,
        J: int = 2,
        m_flow: float = 1.0,
        T_f: float = 10.0,
        fluid_str: str = "Water",
        percent: float = 100.0,
        epsilon: float = 1e-6,
        ncalcsegments: int = 1,
        R_p: list[np.ndarray] | None = None,
    ) -> None:
        """
        Initialize a coaxial borehole pipe model and compute its thermal and
        hydraulic properties.

        Parameters
        ----------
        r_in : float or ndarray
            Inner radii of the coaxial pipes (m). If scalar, copied for both
            inlet and outlet pipes. (first radius is largest as this is corresponding to the inlet)
        r_out : float or ndarray
            Outer radii of the coaxial pipes (m). If scalar, copied for both
            inlet and outlet pipes.
        borehole : gt.boreholes.Borehole
            Borehole geometry object.
        k_g : float or ndarray
            Grout thermal conductivity (W/m·K). If array-like, represents
            values per segment.
        k_p : float or ndarray
            Pipe wall thermal conductivity (W/m·K).
        k_s : float, optional
            Soil thermal conductivity (W/m·K). Default is 1.0.
        J : int, optional
            Number of multipoles used in the multipole expansion. Default is 2.
        m_flow : float, optional
            Total mass flow rate in the BHE (kg/s).
        T_f : float, optional
            Fluid temperature at inlet (°C).
        fluid_str : str, optional
            Working fluid name for thermal property lookup.
        percent : float, optional
            Concentration of glycol or other additive (%).
        epsilon : float, optional
            Relative pipe roughness for hydraulic calculations.
        ncalcsegments : int, optional
            Number of depth segments used in thermal resistance evaluation.
        R_p : list of ndarray, optional
            Precomputed pipe thermal resistances for each segment. If None,
            resistances are computed automatically. Default is empty list, and routines will calculate the resistivity based on the
            pipe dimensions and thermal conductivity.

        Notes
        -----
        - Creates a :class:`gt.pipes.Coaxial` object for use in pygfunction.
        - Computes convective coefficients, fluid properties, and initial
          delta-circuit thermal resistance matrices.
        """

        self.pos = [(0, 0), (0, 0)]
        self.nPipes = 2
        if np.isscalar(r_in):
            r_in = r_in * np.ones(self.nPipes)
        self.r_in = r_in
        if np.isscalar(r_out):
            r_out = r_out * np.ones(self.nPipes)
        self.r_out = r_out
        self.b = borehole
        self.k_s = 0.01
        self.k_g = k_g
        self.k_p = k_p
        self.J = J
        self.nInlets = 1
        self._iOuter = 0
        self._iInner = 1
        self.nOutlets = self.nPipes - self.nInlets
        self.ncalcsegments = ncalcsegments

        # Pipe thermal resistances
        # create a list of R_p if required
        if len(R_p) == 0:
            rp = thermal_resistance_pipe(r_in, r_out, k_p)
            self.R_p = []
            for i in range(ncalcsegments):
                self.R_p.append(rp)
        else:
            self.R_p = R_p

        # Initialize  flow rate and fluid properties including fluid resistivity with pipes
        self.m_flow = m_flow
        self.m_flow_pipe = m_flow * np.ones(self.nPipes)
        self.m_flow_pipe[: self.nInlets] = m_flow / self.nInlets
        self.m_flow_pipe[self.nInlets :] = -m_flow / self.nOutlets
        fluid = gt.media.Fluid(fluid_str, percent, T=T_f)
        self.cp_f = fluid.cp  # Fluid specific isobaric heat capacity (J/kg.K)
        self.rho_f = fluid.rho  # Fluid density (kg/m3)
        self.mu_f = fluid.mu  # Fluid dynamic viscosity (kg/m.s)
        self.k_f = fluid.k  # Fluid thermal conductivity (W/m.K)
        self.epsilon = epsilon

        # default Pipe thermal resistance (take from the first segment)
        # Inner pipe
        R_p_in = self.R_p[0][self._iInner]
        # Outer pipe
        R_p_out = self.R_p[0][self._iOuter]

        # Fluid-to-fluid thermal resistance
        # Inner pipe
        r_in_in = self.r_in[self._iInner]
        h_f_in = gt.pipes.convective_heat_transfer_coefficient_circular_pipe(
            m_flow, r_in_in, self.mu_f, self.rho_f, self.k_f, self.cp_f, self.epsilon
        )
        R_f_in = 1.0 / (h_f_in * 2 * np.pi * r_in_in)
        # Outer pipe
        r_in_out = self.r_out[self._iInner]
        r_out_in = self.r_out[self._iOuter]
        h_f_a_in, h_f_a_out = (
            gt.pipes.convective_heat_transfer_coefficient_concentric_annulus(
                m_flow,
                r_in_out,
                r_out_in,
                self.mu_f,
                self.rho_f,
                self.k_f,
                self.cp_f,
                self.epsilon,
            )
        )
        R_f_out_in = 1.0 / (h_f_a_in * 2 * np.pi * r_in_out)
        R_ff = R_f_in + R_p_in + R_f_out_in

        # Coaxial GHE in borehole
        R_f_out_out = 1.0 / (h_f_a_out * 2 * np.pi * r_out_in)
        R_fp = R_p_out + R_f_out_out

        r_inner = np.roll(self.r_in, 1)
        r_outer = np.roll(self.r_out, 1)

        self.coaxial = gt.pipes.Coaxial(
            (0, 0), r_inner, r_outer, self.b, k_s, k_g[0], R_ff, R_fp, J=self.J
        )

        self.h_f = np.zeros(2)

        self.Rd = []
        self.update_scaleflow(1.0, forceupdate=True)

        return

    def create_coaxial(self) -> gt.pipes.Coaxial:
        """
        Return the underlying pygfunction :class:`Coaxial` object.

        Returns
        -------
        gt.pipes.Coaxial
            The pygfunction coaxial borehole object representing the thermal
            resistance network.
        """
        return self.coaxial

    def init_thermal_resistances(self, k_g: np.ndarray, R_p: list[np.ndarray]) -> None:
        """
        Initialize pipe and grout thermal resistances for all borehole segments.

        This routine is called from the B2G.runsimulation method, in order to generate thermal resistances based
        on actual segments determined by len(k_g) and len(R_p).

        Parameters
        ----------
        k_g : ndarray
            Grout thermal conductivity values for each segment.
        R_p : list of ndarray
            Pipe thermal resistance values for each segment.
        """
        self.ncalcsegments = len(k_g)
        self.k_g = k_g
        self.update_scaleflow(1.0)
        self.R_p = R_p

    def update_scaleflow(
        self,
        scaleflow: float = 1.0,
        forceupdate: bool = False,
        initialize_stored_coeff: bool = True,
    ) -> None:
        """
        Update the scaling of flow rate and associated thermal resistance network.

        This method adjusts the flow rate scaling and updates the thermal resistance
        network based on the new flow rate. Optionally, it can force an update and
        reinitialize stored coefficients.

        Parameters
        ----------
        scaleflow : float, optional
            Scaling factor for flow rate. Default is 1.0.
        forceupdate : bool, optional
            If True, forces update of thermal resistances even if changes are small.
            Default is False.
        initialize_stored_coeff : bool, optional
            If True, reinitializes stored thermal resistance coefficients.
            Default is True.

        Returns
        -------
        None
            Updates internal state in place.
        """
        self.scaleflow = scaleflow
        m_flow = abs(self.m_flow_pipe[0] * self.scaleflow)

        # Pipe thermal resistance (the two pipes have the same thermal conductivity, k_p)
        # Fluid-to-fluid thermal resistance
        # Inner pipe
        r_in_in = self.r_in[self._iInner]
        h_f_in = gt.pipes.convective_heat_transfer_coefficient_circular_pipe(
            m_flow, r_in_in, self.mu_f, self.rho_f, self.k_f, self.cp_f, self.epsilon
        )
        R_f_in = 1.0 / (h_f_in * 2 * np.pi * r_in_in)
        # Outer pipe
        r_in_out = self.r_out[self._iInner]
        r_out_in = self.r_out[self._iOuter]
        h_f_a_in, h_f_a_out = (
            gt.pipes.convective_heat_transfer_coefficient_concentric_annulus(
                m_flow,
                r_in_out,
                r_out_in,
                self.mu_f,
                self.rho_f,
                self.k_f,
                self.cp_f,
                self.epsilon,
            )
        )

        R_f_out_in = 1.0 / (h_f_a_in * 2 * np.pi * r_in_out)
        R_f_out_out = 1.0 / (h_f_a_out * 2 * np.pi * r_out_in)

        hfnew = np.asarray([h_f_a_out, h_f_a_in])
        hfdif = np.subtract(hfnew, self.h_f)
        hfdot = np.dot(hfdif, hfdif)

        if not forceupdate and self.ncalcsegments == len(self.Rd) and (hfdot < 1):
            return

        self.h_f = np.asarray([h_f_a_out, h_f_a_in])
        self.coaxial.h_f = self.h_f

        # --- recompute segment resistances ---
        self.R = []
        self.Rd = []

        for k in range(self.ncalcsegments):
            # Delta-circuit thermal resistances
            # Inner pipe
            R_p_in = self.R_p[k][self._iInner]
            # Outer pipe
            R_p_out = self.R_p[k][self._iOuter]

            R_ff = R_f_in + R_p_in + R_f_out_in
            R_fp = R_p_out + R_f_out_out

            if k == 0:
                self.coaxial.update_thermal_resistances(R_ff, R_fp)

            R_fg = gt.pipes.thermal_resistances(
                self.pos[0:1],
                self.r_out[self._iOuter],
                self.b.r_b,
                self.k_s,
                self.k_g[k],
                R_fp,
                J=self.J,
            )[1][0]

            # Delta-circuit thermal resistances
            Rd = np.zeros((2, 2))
            Rd[self._iInner, self._iInner] = np.inf
            Rd[self._iInner, self._iOuter] = R_ff
            Rd[self._iOuter, self._iInner] = R_ff
            Rd[self._iOuter, self._iOuter] = R_fg
            self.Rd.append(Rd)

        if initialize_stored_coeff:
            self.coaxial._initialize_stored_coefficients()

    def get_temperature_depthvar(
        self,
        T_f_in: float,
        signpower: float,
        Rs: np.ndarray,
        soil_props: SoilProperties,
        nsegments: int = 10,
    ) -> tuple:
        """
        Compute outlet temperature and thermal performance for depth-variable borehole.

        This method partitions the borehole depth into segments and iteratively computes
        fluid temperatures, borehole temperatures, and heat flows based on thermal
        resistances and soil properties.

        Parameters
        ----------
        T_f_in : float
            Inlet fluid temperature (°C).
        signpower : float
            Sign and magnitude for initial power guess.
        Rs : np.ndarray
            Array of thermal resistances for each segment.
        soil_props : SoilProperties
            Object defining soil properties and temperature gradient.
        nsegments : int, optional
            Number of depth segments. Default is 10.

        Returns
        -------
        T_f_out : float
            Outlet fluid temperature (°C).
        power : float
            Heat extraction or injection power (W).
        Reff : float
            Effective thermal resistance (m·K/W).
        ptemp : np.ndarray
            Fluid temperatures per segment.
        Tb : np.ndarray
            Borehole temperatures per segment.
        qbz : np.ndarray
            Heat flow per segment (W).
        """
        bh = self.b
        hstep = bh.H / nsegments

        # Depth coordinates (mid of each segment)
        zmin = bh.D + 0.5 * hstep
        zmax = bh.D + bh.H - 0.5 * hstep
        zseg = np.linspace(zmin, zmax, nsegments)

        # soil temperature at each depth segment
        Tg_borehole = soil_props.getTg(zseg)

        # initalize arrays
        qbz = Tg_borehole * 0.0
        Tb = np.arange(nsegments, dtype=float)
        Tf = Tb * 0.0

        ptemp = np.arange((nsegments + 1) * self.nPipes, dtype=float).reshape(
            nsegments + 1, self.nPipes
        )

        # initialize the top temperatures (inlet)
        ptemp[0, : self.nInlets] = T_f_in

        # iterate for  T_f_out such that bottom temperatures become the same
        dtfout = 0
        dtempold = 0
        dtempnew = 1
        T_f_out = T_f_in + 1e-1 * signpower
        cont = True

        while abs(dtempnew) > 1e-4 or cont:
            # set outlet boundary condition guess
            ptemp[0, self.nInlets :] = T_f_out

            # loop over each segment
            for i in range(nsegments):
                Rd = self._Rd[i]
                b = 1.0 / Rd[0][0]

                # Tf is only for output purposes
                Tf[i] = np.average(ptemp[i])

                # prep next segment's temperatures
                ptemp[i + 1] = ptemp[i]

                # iteration variables within the segment
                tseg = 0.5 * (ptemp[i] + ptemp[i + 1])
                dtemp = 1
                icount = 0

                # check that Rs[i]*b is not close to 1 if so modify with small number
                if Rs[i] < 0:
                    Rs[i] = abs(Rs[i])

                # iterate until pipe temperatures converge
                while np.dot(dtemp, dtemp) > 1e-10:
                    icount += 1
                    tsegold = tseg

                    a = b * tseg[0]
                    Tb[i] = (Rs[i] * a + Tg_borehole[i]) / (1 + Rs[i] * b)

                    q1 = b * (tseg[0] - Tb[i])
                    q2 = (tseg[1] - tseg[0]) / Rd[0][1]

                    # Update fluid temperatures
                    mflow0 = self.m_flow_pipe[0] * self.scaleflow * self.cp_f
                    mflow1 = self.m_flow_pipe[1] * self.scaleflow * self.cp_f

                    ptemp[i + 1][0] = ptemp[i][0] - q1 * hstep / mflow0
                    ptemp[i + 1][0] += q2 * hstep / mflow0

                    ptemp[i + 1][1] = ptemp[i][1] - q2 * hstep / mflow1

                    tseg = 0.5 * (ptemp[i] + ptemp[i + 1])
                    dtemp = tseg - tsegold

                # segment heat flow
                qbz[i] = -q1 * hstep

            # compute temperature mismatch for iteration
            dtempnew = np.sum(
                ptemp[nsegments, self.nInlets :] * self.m_flow_pipe[self.nInlets :]
            ) + np.sum(
                ptemp[nsegments, : self.nInlets] * self.m_flow_pipe[: self.nInlets]
            )

            # Update outlet temperature guess
            if abs(dtfout) > 0:
                g = dtfout / (dtempnew - dtempold)
                dtfout = -dtempnew * g
                cont = False
            else:
                dtfout = 1e-1
                cont = True

            dtempold = dtempnew
            T_f_out += dtfout

        # Final power and effective resistance
        power = (T_f_out - T_f_in) * self.m_flow * self.scaleflow * self.cp_f

        if abs(np.sum(qbz) - power) > 1:
            print("power is not sumq (sumq, power):", np.sum(qbz), ",", power)

        Reff = -np.average(Tf - Tb) * bh.H / power

        return T_f_out, power, Reff, ptemp, Tb, qbz
