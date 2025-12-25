import numpy as np
from scipy.integrate import odeint
from scipy.interpolate import UnivariateSpline

from geoloop.axisym.AxisymetricEL import AxiGrid
from geoloop.geoloopcore.boreholedesign import BoreholeDesign
from geoloop.geoloopcore.CoaxialPipe import CoaxialPipe
from geoloop.geoloopcore.CustomPipe import CustomPipe
from geoloop.geoloopcore.simulationparameters import SimulationParameters
from geoloop.geoloopcore.soilproperties import SoilProperties

IFLUXF = [1, 0, 0]
JFLUXF = [0, 1, 0]
KFLUXF = [0, 0, 1]


class B2G:
    """
    Class for depth dependent variation in pipe temperatures and borehole wall temperatures as well as soil properties,
    using a 2D axisymmetric finite volume model

    The model is based on a modified approach from the work of Cazorla-Marin [1, 2, 3].

    The modification is that the thermal resistance and Tb node of pygfunction is used for the borehole wall,
    and 3 additional nodes are included.

    The Tb node is subject to heat flow determined from the thermal resistance network :Rbinv @ (Tf - Tb np.ones)

    - q  = sum ( qi = Rbinv @ (Tf - Tb np.ones)).

    Currently, the model is with finite volume formulation without Lax-Wendroff explicit finite volume scheme
    (LW scheme not implemented yet).
    This is a 2nd order explicit scheme, with the thermal resistance network of the borehole wall and the fluid nodes.
    it practically limits the number of vertical nodes to ca. 10.

     Attributes
     ----------
     custom_pipe : CustomPipe
         Pipe configuration object with geometric and thermal properties.
     is_coaxial : bool
         True if the pipe is a coaxial configuration.
     ag : AxiGrid
         Axisymmetric finite volume grid (initialized later).

    References
    ----------
    [1] Cazorla Marín, A.: Modelling and experimental validation of an innovative coaxial helical borehole heat exchanger
        for a dual source heat pump system, PhD, Universitat Politècnica de València, Valencia (Spain),
        https://doi.org/10.4995/Thesis/10251/125696, 2019.
    [2] Cazorla-Marín, A., Montagud-Montalvá, C., Tinti, F., and Corberán, J. M.: A novel TRNSYS type of a coaxial borehole
        heat exchanger for both short and mid term simulations: B2G model, Applied Thermal Engineering, 164, 114500,
        https://doi.org/10.1016/j.applthermaleng.2019.114500, 2020.
    [3] Cazorla-Marín, A., Montagud-Montalvá, C., Corberán, J. M., Montero, Á., and Magraner, T.: A TRNSYS assisting tool
        for the estimation of ground thermal properties applied to TRT (thermal response test) data: B2G model, Applied
        Thermal Engineering, 185, 116370, https://doi.org/10.1016/j.applthermaleng.2020.116370, 2021.
    """

    def __init__(self, custom_pipe: CustomPipe) -> None:
        """
        Initialize the B2G model with a given custom pipe configuration.

        Parameters
        ----------
        custom_pipe : CustomPipe
            Object containing borehole geometry, pipe arrangement, and thermal properties.
        """
        self.custom_pipe = custom_pipe
        if isinstance(self.custom_pipe, CoaxialPipe):
            self.is_coaxial = True
        else:
            self.is_coaxial = False

    def runsimulation(
        self,
        bh_design: BoreholeDesign,
        soil_props: SoilProperties,
        sim_params: SimulationParameters,
    ) -> tuple:
        """
        Run the borehole-to-ground simulation using finite difference axisymmetric grid.

        Parameters
        ----------
        bh_design : BoreholeDesign
            Borehole geometry and thermal resistances.
        soil_props : SoilProperties
            Soil properties and ground temperature profile.
        sim_params : SimulationParameters
            Simulation settings: time array, inlet temperatures, flow rates, etc.

        Returns
        -------
        hours : ndarray
            Time array in hours.
        Q_b : ndarray
            Borehole thermal power [W].
        flowrate : ndarray
            Mass flow rate [kg/s].
        qsign : ndarray
            Sign of heat extraction (-1 for extraction, +1 for injection).
        T_fi : ndarray
            Fluid inlet temperatures [°C].
        T_fo : ndarray
            Fluid outlet temperatures [°C].
        T_bave : ndarray
            Average borehole wall temperature [°C].
        z : ndarray
            Depth coordinates [m].
        T_b : ndarray
            Borehole wall temperature field [°C].
        T_f : ndarray
            Pipe fluid temperature field [°C].
        qzb : ndarray
            Vertical heat flux along borehole [W/m].
        h_fpipes : ndarray
            Convective film coefficients for each pipe.
        result : ndarray
            Raw solution array from the finite difference solver.
        zstart : ndarray
            Lower boundary of each vertical cell [m].
        zend : ndarray
            Upper boundary of each vertical cell [m].
        """
        custom_pipe = self.custom_pipe
        nx = sim_params.nsegments + 1
        z = np.linspace(custom_pipe.b.D, custom_pipe.b.D + custom_pipe.b.H, nx)

        # Define vertical cell boundaries
        zstart = z * 1.0
        zend = z * 1.0
        dz = np.diff(z)
        zstart[-1] -= dz[-1]
        zend[0:-1] = zstart[0:-1] + 0.5 * dz

        # Borehole resistances
        k_g = bh_design.get_k_g(zstart, zend)
        R_p = bh_design.get_r_p(z)
        # create the right structure for thermal resistances
        self.custom_pipe.init_thermal_resistances(k_g, R_p)

        # Soil conductivity
        k_s = soil_props.get_k_s(zstart, zend, sim_params.isample)

        # Time and mass flow scaling
        hours = sim_params.time / 3600.0
        m_flow = sim_params.m_flow[0]
        qscale = sim_params.m_flow / m_flow
        h_fpipes = np.zeros((qscale.shape[0], custom_pipe.nPipes))
        h_fpipes[:] = custom_pipe.h_f

        # solve for temperature distribution
        T_f, T_b, dtf, qzb, result = self.get_temperature_depthvar(
            hours,
            qscale,
            sim_params.Tin,
            soil_props,
            nr=sim_params.nr,
            rmax=sim_params.rmax,
            nsegments=nx,
            k=k_s,
            alfa=soil_props.alfa,
        )

        T_fi = T_f[:, 0, 0]
        T_fo = T_f[:, 0, custom_pipe.nPipes - 1]
        flowrate = sim_params.m_flow
        Q_b = (T_fo - T_fi) * custom_pipe.cp_f * flowrate
        qsign = np.sign(Q_b)
        T_bave = np.average(T_b, axis=1)

        return (
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
            -qzb,
            h_fpipes,
            result,
            zstart,
            zend,
        )

    def modify_par_ag(self, ny_add: int, param: np.ndarray) -> np.ndarray:
        """
        Modify the dimension of the AxiGrid object parameter, by adding ny_add nodes in the y direction to represent
        the pipes.

        This member function is used internally to modify the original grid parameters of the AxiGrid object.

        Parameters
        ----------
        ny_add : int
            Number of additional nodes to insert in the y-direction for pipes.
        param : np.ndarray
            Original parameter array (e.g., k, vol, overcp, rcf, rcbulk, axyz).

        Returns
        -------
        np.ndarray
            Modified parameter array with added pipe nodes.
        """
        grid = self.ag
        ag_ny = grid.ny + ny_add
        grid_mesh = np.arange(self.ag.nx * ag_ny, dtype=float).reshape(
            self.ag.nx, ag_ny, 1
        )
        grid_mesh *= 0
        grid_mesh[:, ny_add + 1 :, :] = param[:, 1:, :]
        return grid_mesh

    def modify_trans_ag(self, ny_add: int, transmission: np.ndarray) -> np.ndarray:
        """
        Modify the dimension of the AxiGrid object transmission or flux (at faces), by adding ny_add nodes in the y
        direction to represent the pipes.

        This member function is used internally to modify the original grid parameters of the AxiGrid object.

        Parameters
        ----------
        ny_add : int
            Number of additional nodes to insert in the y-direction.
        transmission : np.ndarray
            Original transmission/flux array.

        Returns
        -------
        np.ndarray
            Modified transmission array with added pipe nodes.
        """
        grid = self.ag
        ag_ny = grid.ny + ny_add
        grid_transmission = np.arange(3 * self.ag.nx * ag_ny, dtype=float).reshape(
            3, self.ag.nx, ag_ny, 1
        )
        grid_transmission *= 0
        grid_transmission[:, :, ny_add + 1 :, :] = transmission[:, :, 1:, :]
        return grid_transmission

    def modify_ag(self) -> None:
        """
        Modify the axisymmetric grid to include the pipes and the borehole heat capacity.

        This member function is used internally by initAG to modify the original grid parameters of the AxiGrid object.

        Replace the heat capacity of the second node in the axisymmetric grid to take into account the borehole heat
        capacity, corrected for the pipes (which are treated by the pipe nodes).

        In addition, insert additional nodes, starting from node 0 to include the pipes
        and roll the properties of the original axisymmetric grid to include the pipes.
        """
        g = self.ag
        n_pipes = self.custom_pipe.nPipes
        ny_add = n_pipes - 1

        for i in range(g.nx):
            j = 1
            if self.is_coaxial:
                a1 = (
                    self.custom_pipe.r_in[0] ** 2 - self.custom_pipe.r_out[1] ** 2
                ) * np.pi
                a2 = self.custom_pipe.r_in[1] ** 2 * np.pi
                areapipes = a1 + a2
            else:
                rpipes = self.custom_pipe.r_in  # was r_out, but heat capacity of pipes is only fluid, rest should be connected
                # the
                areapipes = np.sum(rpipes**2 * np.pi)

            axitoparea = g.axisumdr[i][1] ** 2 * np.pi - areapipes

            g.vol[i][j][0] = axitoparea * g.dx[i].item()
            g.overcp[i][j][0] = 1.0 / (g.vol[i][j][0] * g.rcbulk[i][j][0])

        # adjust the vertical transimission coefficient, based on the new volume, using Langevin approach
        for i in range(g.nx - 1):
            j = 1
            ia = 0
            g.txyz[ia][i][j][0] = 1 / (
                0.5 * g.dx[i] ** 2 / (g.k[i][j][0] * g.vol[i][j][0])
                + 0.5 * g.dx[i + 1] ** 2 / (g.k[i + 1][j][0] * g.vol[i + 1][j][0])
            )

        # from here add new nodes (remember that the first node is corresponding to the first inlet
        # add nodes for the pipes and set properties of the first npipe nodes to 0
        g.axisumdr = self.modify_par_ag(ny_add, g.axisumdr)
        g.axidr = self.modify_par_ag(ny_add, g.axidr)
        g.axicellrmid = self.modify_par_ag(ny_add, g.axicellrmid)
        g.k = self.modify_par_ag(ny_add, g.k)
        g.vol = self.modify_par_ag(ny_add, g.vol)
        g.overcp = self.modify_par_ag(ny_add, g.overcp)
        g.rcf = self.modify_par_ag(ny_add, g.rcf)
        g.rcbulk = self.modify_par_ag(ny_add, g.rcbulk)
        g.axyz = self.modify_par_ag(ny_add, g.axyz)

        g.txyz = self.modify_trans_ag(ny_add, g.txyz)
        g.fxyz = self.modify_trans_ag(ny_add, g.fxyz)

        for i in range(g.nx):
            if self.is_coaxial:
                # modify the properties for the tubes.  Needed are the fluxes, overcp
                g.vol[i, 1, 0] = g.dx[i] * np.pi * self.custom_pipe.r_in[1] ** 2
                g.vol[i, 0, 0] = (
                    g.dx[i]
                    * np.pi
                    * (self.custom_pipe.r_in[0] ** 2 - self.custom_pipe.r_out[1] ** 2)
                )
            else:
                # modify the properties for the tubes.  Needed are the fluxes, overcp
                g.vol[i, 0:n_pipes, 0] = g.dx[i] * np.pi * self.custom_pipe.r_in**2

        for i in range(g.nx):
            g.rcf[i, 0:n_pipes, 0] = self.custom_pipe.cp_f * self.custom_pipe.rho_f
            g.rcbulk[i, 0:n_pipes, 0] = g.rcf[i, 0:n_pipes, 0]
        g.overcp[:, 0:n_pipes, :] = 1 / (
            g.vol[:, 0:n_pipes, :] * g.rcbulk[:, 0:n_pipes, :]
        )

        # Set mass flux through the pipes
        pflux = np.asarray(self.custom_pipe.m_flow_pipe / self.custom_pipe.rho_f)
        for i in range(g.nx):
            g.fxyz[0, i, 0:n_pipes, 0] = pflux

        # Adjust transmission for first pipe row
        for i in range(g.nx):
            j = 0
            ia = 1
            g.txyz[ia, i, j, 0] = g.dx[i] / self.custom_pipe._Rd[i][0][1]

        g.ny += ny_add
        g.dirichlet = g.overcp * 0 + 1

    def init_ag(
        self,
        soil_props: SoilProperties,
        nr: int = 35,
        rmax: float = 10,
        T_f_instart: float = 0,
        nsegments: int = 10,
        k: float | np.ndarray = 2,
        rcf: float | np.ndarray = 4e6,
        rcr: float | np.ndarray = 3e6,
        por: float | np.ndarray = 0.4,
    ) -> None:
        """
        Initialize the axisymmetric grid (AxiGrid) for the borehole-to-ground model.

        Sets up the radial and vertical grid, adds pipe nodes, and initializes
        ground and fluid temperatures.

        Parameters
        ----------
        soil_props : SoilProperties
            Soil properties object to obtain ground temperatures.
        nr : int, optional
            Maximum number of radial nodes (should be odd), by default 35
        rmax : float, optional
            Radius of the midpoint of the last cell, by default 10, is a constant
        T_f_instart : float, optional
            Initial fluid temperature used as default to set up the grid initial temperatures, and fluid conductivity
            and heat capacities
        nsegments : int, optional
            Number of nodes (nx) in the vertical direction, by default 10
        k : float or np.ndarray, optional
            Bulk thermal conductivity in the radial direction, by default 2.0
        rcf : float or np.ndarray, optional
            Volumetric heat capacity of fluid [J/m³·K], by default 4e6
        rcr : float or np.ndarray, optional
            Volumetric heat capacity of rock [J/m³·K], by default 3e6
        por : float or np.ndarray, optional
            Porosity of the cells, by default 0.4

        Returns
        -------
        None
        """
        cpipe = self.custom_pipe
        rw = cpipe.b.r_b
        xmin = cpipe.b.D
        xmax = xmin + cpipe.b.H

        # nr needs to be odd for rmax to scale as multiple of rwmin
        if nr % 2 == 0:
            nr += 1

        # scaling factor of cell size and spacing:  factor = size cell [i+2] / size cell [i]
        factor = 1.5
        # how much of the cell size is corresponding the left (smaller cell)  vs right (larger cell)
        ratio = factor**0.5 - 1
        rwmin = (1 - ratio**2) * rw

        nx = nsegments
        self.ag = AxiGrid(
            nx,
            nr,
            xmin,
            xmax,
            rwmin,
            rmax,
            k,
            rcf,
            rcr,
            por,
            firstwellcell=True,
            endcellbound=True,
        )

        # Modify grid to add pipe nodes
        self.modify_ag()

        # Initialize ground temperatures along vertical nodes
        tvd = self.ag.x
        Tg_profile = soil_props.getTg(tvd)
        self.ag.initTempX(Tg_profile)

        # set the inlet temperatures
        self.ag.init_vals[0, : cpipe.nInlets, 0] = T_f_instart

        return

    def get_temperature_depthvar(
        self,
        hours: np.ndarray,
        qscale: np.ndarray,
        T_f_in: np.ndarray,
        soil_props: SoilProperties,
        nr: int = 35,
        rmax: float = 10,
        nsegments: int = 10,
        k: float | np.ndarray = 2.0,
        alfa: float = 1e-6,
    ) -> tuple:
        """
        Compute the time-dependent temperature profiles for fluid and borehole wall.

        Solves the 2D axisymmetric finite difference heat transfer for a borehole
        including the thermal interaction between fluid, pipes, grout, and ground.

        Parameters
        ----------
        hours : np.ndarray
            Array of time points in hours.
        qscale : np.ndarray
            Scaling factor for mass flow / heat rate.
        T_f_in : np.ndarray
            Array of inlet fluid temperatures [°C] (takes first component as inlet temperature).
        soil_props : SoilProperties
            Soil properties object for ground temperatures.
        nr : int, optional
            Maximum number of radial nodes (should be odd), by default 35.
        rmax : float, optional
            Radius of the midpoint of the last cell, by default 10.
        nsegments : int, optional
            Number of nodes in the vertical direction, by default 10.
        k : float or np.ndarray, optional
            Thermal conductivity (radial), by default 2.0.
        alfa : float, optional
            Thermal diffusivity of soil [m²/s], by default 1e-6.

        Returns
        -------
        T_f : np.ndarray
            Fluid temperature [hours, vertical nodes, pipes].
        T_b : np.ndarray
            Borehole wall temperature [hours, vertical nodes].
        dtf : np.ndarray
            Temperature difference between outlet and inlet [hours, vertical nodes].
        qzb : np.ndarray
            Heat flux to borehole [hours, vertical nodes].
        result : np.ndarray
            Full 4D result array from the solver [hours, vertical nodes, radial nodes, axial nodes].
        """
        # initialze axisymmetrica
        self.init_ag(
            soil_props,
            nr=nr,
            rmax=rmax,
            T_f_instart=T_f_in[0],
            nsegments=nsegments,
            k=k,
            rcr=k / alfa,
            por=0.0,
        )

        dt = 3600

        # Compute derivative of inlet temperature using spline
        x = hours
        y = T_f_in
        spl = UnivariateSpline(x, y, k=4, s=0)
        T_f_in_derivs = np.asarray(spl.derivatives(x))[:, 1]

        # Run heat loop solver
        result = ode_heatloop(hours, dt, qscale, T_f_in_derivs, self)

        npipes = self.custom_pipe.nPipes
        T_f = result[:, :, 0:npipes, :].reshape(len(hours), self.ag.nx, npipes)
        T_b = result[:, :, npipes, :].reshape(len(hours), self.ag.nx)

        # Mass flow and heat capacity
        mflow = self.custom_pipe.m_flow * qscale
        dtf = T_f[:, :, npipes - 1] - T_f[:, :, 0]

        # Calculate heat flux to borehole wall
        qzb = dtf * 1.0
        for i in range(len(x)):
            qzb[i, :] *= mflow[i] * self.custom_pipe.cp_f

        for it in range(len(x)):
            for i in range(self.ag.nx):
                temppipe = T_f[it, i].reshape(npipes)
                # get the borewall temperature
                temp_b = T_b[it, i]

                if self.is_coaxial:
                    qpipe = (self.ag.dx[i] / self.custom_pipe._Rd[i][0][0]) * (
                        temppipe[0] - temp_b
                    )
                    # get the heatflow (negative is heat flow to borehole) for each of the pipes to borehole wall
                else:
                    qpipe = (
                        self.custom_pipe.R1[i]
                        @ (temppipe - np.ones(npipes) * temp_b)
                        * self.ag.dx[i]
                    )

                qsum = np.sum(qpipe)
                qzb[it, i] = qsum

        qzb *= -1

        return T_f, T_b, dtf, qzb, result


def ode_heatloop(
    time: np.ndarray, dt: float, qscale: np.ndarray, T_f_in_derivs: np.ndarray, b2g: B2G
) -> np.ndarray:
    """
    Integrates the borehole heat transfer equations over time using an ODE solver.

    Solves the transient 2D axisymmetric heat transfer between fluid, pipes, borehole, and ground.
    Uses a simple explicit upwind scheme and Dirichlet boundary conditions for the inlet temperatures.

    Parameters
    ----------
    time : np.ndarray
        Array of time points [h] for integration.
    dt : float
        Timestep scaling in seconds.
    qscale : np.ndarray
        Time array of scaling factors of the reference flow (time dimension)
    T_f_in_derivs : np.ndarray
        Time derivative of inlet fluid temperature [°C/h].
    b2g : B2G
        Borehole-to-ground model containing pipe and axisymmetric grid information.

    Returns
    -------
    np.ndarray
        Temperature array of shape (len(time), nx, ny, nz), where nx, ny, nz are
        the dimensions of b2g.ag (grid).
    """
    grid = b2g.ag

    class ScaleFunc:
        """Interpolates a time-dependent scaling factor or derivative."""

        def __init__(self, scale: np.ndarray, time: np.ndarray):
            self.scale = scale
            self.time = time

        def get_scale(self, t: float) -> float:
            return np.interp(t, self.time, self.scale)

    # Create interpolation function for time-dependent quantities
    qscale_t = ScaleFunc(qscale, time)
    T_f_in_derivs_t = ScaleFunc(T_f_in_derivs, time)

    def ode(
        y: np.ndarray, t: float, dt: float, g: AxiGrid, custom_pipe: CustomPipe
    ) -> np.ndarray:
        """
        Compute dT/dt for the grid at time t.

        Parameters
        ----------
        y : np.ndarray
            Flattened temperature array of shape (nx*ny*nz).
        t : float
            Current simulation time.
        dt : float
            Timestep scaling.
        g : AxiGrid
            Axisymmetric grid.
        custom_pipe : CustomPipe
            Pipe configuration with flow and thermal resistance information.

        Returns
        -------
        np.ndarray
            Flattened array of temperature derivatives (dT/dt * dt).
        """
        # use npipes in ny direction to set the fluid fluxes. This is all arranged with the
        s = y.reshape(g.nx, g.ny, g.nz)
        dsdt = np.zeros_like(s)

        nPipes = custom_pipe.nPipes
        nInlets = custom_pipe.nInlets

        qscale = qscale_t.get_scale(t)
        Tf_der = T_f_in_derivs_t.get_scale(t)

        for k in range(g.nz):
            for i in range(g.nx):
                # get for the depth segment the pipe temperatures
                temppipe = s[i, 0:nPipes, :].reshape(nPipes)

                # get the borewall temperature
                temp_b = s[i, nPipes, 0]
                # get the heatflow (negative is heat flow to borehole) for each of the pipes to borehole wall
                if isinstance(custom_pipe, CoaxialPipe):
                    qpipe = temppipe * 0
                    qpipe[0] = (1.0 / custom_pipe._Rd[i][0][0]) * (temppipe[0] - temp_b)
                else:
                    qpipe = custom_pipe.R1[i] @ (temppipe - np.ones(nPipes) * temp_b)
                # get the
                qsum = np.sum(qpipe)
                # if (i == 5):
                #     # print("qsum", qsum)

                for j in range(g.ny):
                    # dsdt[i][j][k] = 0.0
                    # in boundary condtion list?

                    # else do diffusion and fluxes
                    for ia in range(2):
                        ii = i + IFLUXF[ia]
                        jj = j + JFLUXF[ia]
                        kk = k
                        if isinstance(custom_pipe, CoaxialPipe):
                            usecpipe = (ia == 1) and (j == 0)
                        else:
                            usecpipe = (ia == 1) and (j < nPipes)
                        if usecpipe:
                            jj = nPipes
                        ok = g.checkindex(ii, jj, kk)
                        if ok:
                            dtemp = s[i][j][k] - s[ii][jj][kk]
                            # diffusion, for the pipe nodes g.txyz[1][i][j=0..npipe-1][k] should not be used instead ,
                            # handled with the heatflux condition from  the cpipe R matrix

                            if usecpipe:
                                dsdt[i][j][k] -= g.overcp[i][j][k] * qpipe[j] * g.dx[i]
                                dsdt[ii][jj][kk] += (
                                    g.overcp[ii][jj][kk] * qpipe[j] * g.dx[ii]
                                )
                            else:
                                dsdt[i][j][k] -= (
                                    g.overcp[i][j][k] * g.txyz[ia][i][j][k] * dtemp
                                )
                                dsdt[ii][jj][kk] += (
                                    g.overcp[ii][jj][kk] * g.txyz[ia][i][j][k] * dtemp
                                )

                            if usecpipe and isinstance(custom_pipe, CoaxialPipe):
                                # j ==0
                                dtemp = s[i][j][k] - s[ii][1][kk]
                                dsdt[i][j][k] -= (
                                    g.overcp[i][j][k] * g.txyz[ia][i][j][k] * dtemp
                                )
                                dsdt[ii][1][kk] += (
                                    g.overcp[ii][1][kk] * g.txyz[ia][i][j][k] * dtemp
                                )

                            # fluxes [m3/s]  upwind scheme, this does not implement LAX-WENDROF
                            # these fluxes are used in the pipe  nodes, and should be set
                            # in the correct way , i.e.
                            #   -  they correspond to downward (positive) and upward flowrates (negative) (ia==0)
                            #   -  the correponding overcp agrees with pipe fluid volume density and heat capacity
                            flux = g.fxyz[ia][i][j][k] * qscale

                            if (ia == 0) and (j < nInlets) and (i == g.nx - 2):
                                if j == 0:
                                    enthsum = 0
                                    cpsum = 0
                                    for m in range(nInlets):
                                        flux = g.fxyz[ia][i][m][k] * qscale
                                        dtemp = s[i][m][k] - s[ii][m][k]
                                        # for an inlet pipe the flux should always be >=0
                                        if flux > 0:
                                            enthsum += dtemp * flux * g.rcf[ii][m][k]
                                            cpsum += 1 / g.overcp[ii][m][k]
                                    if cpsum > 0:
                                        for m in range(nInlets):
                                            dsdt[ii][m][k] += enthsum / cpsum
                            else:
                                if flux > 0:
                                    dsdt[ii][jj][kk] += (
                                        dtemp
                                        * flux
                                        * g.rcf[ii][jj][kk]
                                        * g.overcp[ii][jj][kk]
                                    )
                                elif flux < 0:
                                    dsdt[i][j][k] += (
                                        dtemp
                                        * flux
                                        * g.rcf[i][j][k]
                                        * g.overcp[i][j][k]
                                    )

        # correct the bottom nodes
        i = g.nx - 1
        hsum = 0
        cpsum = 0
        for j in range(nPipes):
            hsum += dsdt[i][j][0] / g.overcp[i][j][0]
            cpsum += 1.0 / g.overcp[i][j][0]
        for j in range(nPipes):
            dsdt[i][j][0] = hsum / cpsum

        # set the inlet temeratures to change according to the inpu derivatives
        dsdt[0, 0:nInlets, 0] = Tf_der / dt

        # overrule nodal changes which have fixed (dirichlet) boundary condition
        dsdt *= g.dirichlet
        dsdt_scaled = dsdt * dt
        dydt = dsdt_scaled.reshape(g.nx * g.ny * g.nz)

        return dydt

    init_vals = grid.init_vals.reshape(grid.nx * grid.ny * grid.nz)
    resultode = odeint(ode, init_vals, time, args=(dt, grid, b2g.custom_pipe))

    return resultode.reshape(len(time), grid.nx, grid.ny, grid.nz)
