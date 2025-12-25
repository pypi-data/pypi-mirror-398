import matplotlib.pyplot as plt
import numpy as np


def check_asarray(rmin: float | np.ndarray, nr: int) -> np.ndarray:
    """
    Ensure the input is a NumPy array.

    If `rmin` is already a NumPy array, it is returned as is.
    Otherwise, a NumPy array of length `nr` filled with `rmin` is created.

    Parameters
    ----------
    rmin : float or np.ndarray
        Input value or array to be converted/checked.
    nr : int
        Length of the array to create if `rmin` is not an array.

    Returns
    -------
    np.ndarray
        NumPy array with values from `rmin` or filled with `rmin`.
    """

    if isinstance(rmin, np.ndarray):
        res = rmin
    else:
        res = np.full([nr], rmin)
    return res


class SimGridRegular:
    """
    A regular 3D grid for simulation.

    This class sets up a grid with `nx` cells in x, `ny` cells in y, and `nz` cells in z.
    It can handle transmissivity and fluxes in x, y, z directions, volumetric specific
    heat of fluid and rock, and heat production.
    """

    def __init__(
        self,
        nx: int,
        ny: int,
        nz: int,
        txyz: np.ndarray,
        fxyz: np.ndarray,
        rcf: float,
        rcbulk: float,
        axyz: np.ndarray,
    ):
        """
        Constructor for SimGridRegular.

        Parameters
        ----------
        nx : int
            Number of grid cells in x-direction.
        ny : int
            Number of grid cells in y-direction.
        nz : int
            Number of grid cells in z-direction.
        txyz : np.ndarray
            Transmissivity array in x, y, z directions (shape: 3 x nx x ny x nz).
        fxyz : np.ndarray
            Flux array in x, y, z directions (shape: 3 x nx x ny x nz).
        rcf : float
            Fluid volumetric specific heat [J m^-3 K^-1].
        rcbulk : float
            Bulk volumetric specific heat [J m^-3 K^-1].
        axyz : np.ndarray
            Heat production integrated over cell volume [W].
        """

        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.txyz = txyz
        self.fxyz = fxyz
        self.rcf = rcf
        self.rcbulk = rcbulk
        self.axyz = axyz

    def set_initvalues(self, temp: np.ndarray) -> None:
        """
        Set the initial values of the grid.

        Parameters
        ----------
        temp : np.ndarray
            Initial values to assign to the grid.
        """
        self.init_vals = temp

    def checkindex(self, ii: int, jj: int, kk: int) -> bool:
        """
        Check if the given indices are within the grid bounds.

        Parameters
        ----------
        ii : int
            Index along x-axis.
        jj : int
            Index along y-axis.
        kk : int
            Index along z-axis.

        Returns
        -------
        bool
            True if the indices are within bounds, False otherwise.
        """
        ok = (
            (ii >= 0)
            and (jj >= 0)
            and (kk >= 0)
            and (ii < self.nx)
            and (jj < self.ny)
            and (kk < self.nz)
        )
        return ok

    def clearDirichlet(self) -> None:
        """
        Reset Dirichlet boundary conditions.

        All nodes are set to have no fixed (Dirichlet) boundary condition.
        """
        self.dirichlet = np.arange(self.nx * self.ny * self.nz, dtype=float).reshape(
            self.nx, self.ny, self.nz
        )
        self.dirichlet *= 0
        self.dirichlet += 1.0

    def addDirichlet(self, indexlist: list[list[int]], value: float) -> None:
        """
        Apply Dirichlet boundary conditions to specified cells.

        Adds a list of cell indices as dirichlet boundary conditions with the value specified.

        Parameters
        ----------
        indexlist : list of list of int
            List of cell indices, each as [i, j, k]. ([ [i,j,k], [i,j,k], ..])
        value : float
            Value to apply to the specified cells.
        """
        for i, index in enumerate(indexlist):
            self.dirichlet[index[0]][index[1]][index[2]] = (
                0.0  # causing the cell not be changed
            )
            self.init_vals[index[0]][index[1]][index[2]] = value  # value of the cell


class AxiGrid(SimGridRegular):
    """
    Axisymmetric grid following Langevin (2009).

    The grid has `nx` cells along the axis, `ny=nr` radial cells, and `nz=1` in tangential direction.
    Radial direction corresponds to the y-axis, axial direction to x, and tangential to z.

    x[0] = rmin is first cell wall //  rmax midpoint of last cell
    x[1]
    """

    def __init__(
        self,
        nx: int,
        nr: int,
        xmin: float,
        xmax: float,
        rmin: float | np.ndarray,
        rmax: float,
        k: float | np.ndarray,
        rcf: float | np.ndarray,
        rcr: float | np.ndarray,
        por: float | np.ndarray,
        firstwellcell: bool = True,
        kwf: float = 0.6,
        rcwf: float = 4.2e6,
        drmin: float = 0,
        endcellbound: bool = False,
    ):
        """
        Constructor for the AxiGrid class.

        Parameters
        ----------
        nx : int
            Number of grid cells along the axis.
        nr : int
            Number of radial cells.
        xmin : float
            Location of the first cell along the axis.
        xmax : float
            Location of the last cell along the axis.
        rmin : float or np.ndarray
            Radius of the first cell face near the radial axis (>0).
        rmax : float
            Radius at the midpoint of the last cell.
        k : float or np.ndarray
            Bulk conductivity in the radial direction (dimension nx).
        rcf : float or np.ndarray
            Volumetric heat capacity of fluid [J m^-3 K^-1] (dimension nx).
        rcr : float or np.ndarray
            Volumetric heat capacity of rock [J m^-3 K^-1] (dimension nx).
        por : float or np.ndarray
            Porosity of cells (dimension nx).
        firstwellcell : bool, optional
            Whether the first cell is a well cell with modified properties (default: True).
        kwf : float, optional
            Well fluid thermal conductivity (used if firstwellcell is True, default: 0.6).
        rcwf : float, optional
            Well fluid volumetric heat capacity [J m^-3 K^-1] (used if firstwellcell is True, default: 4.2e6).
        drmin : float, optional
            Minimum radial increase for cells (default: 0).
        endcellbound : bool, optional
            Apply end cell boundary condition (default: False).
        """
        self.nx = nx
        self.ny = nr
        self.nz = 1
        # x is cell node locations along the x axis
        self.x = np.linspace(xmin, xmax, self.nx)

        self.initGrid(
            rmin, rmax, k, rcf, rcr, por, firstwellcell, kwf, rcwf, drmin, endcellbound
        )

    def initfrom_xarray(
        self,
        x_array: np.ndarray,
        nr: int,
        rmin: float | np.ndarray,
        rmax: float,
        k: np.ndarray,
        rcf: np.ndarray,
        rcr: np.ndarray,
        por: np.ndarray,
        firstwellcell: bool = True,
        kwf: float = 0.6,
        rcwf: float = 4.2e6,
        drmin: float = 0,
        endcellbound: bool = False,
    ) -> None:
        """
        Initialize the grid using specified x-array positions.

        Parameters
        ----------
        x_array : np.ndarray
            Cell midpoint positions along the x-axis.
        nr : int
            Number of cells in radial direction.
        rmin : float or np.ndarray
            Minimum cell face radius closest to the radial axis (>0). Can be an array of size nx.
        rmax : float
            Maximum cell midpoint radius (furthest from radial axis). Constant.
        k : np.ndarray
            Bulk conductivity in radial direction (dimension nx).
        rcf : np.ndarray
            Volumetric heat capacity of fluid [J m^-3 K^-1] (dimension nx).
        rcr : np.ndarray
            Volumetric heat capacity of rock [J m^-3 K^-1] (dimension nx).
        por : np.ndarray
            Porosity of cells (dimension nx).
        firstwellcell : bool, optional
            Whether the first cell is a well cell with modified properties (default: True).
        kwf : float, optional
            Well fluid thermal conductivity (default: 0.6).
        rcwf : float, optional
            Well fluid volumetric heat capacity [J m^-3 K^-1] (default: 4.2e6).
        drmin : float, optional
            Minimum radial increase for cells (default: 0).
        endcellbound : bool, optional
            Apply end cell boundary condition (default: False).
        """
        self.nx = len(x_array)
        self.ny = nr
        self.nz = 1
        self.x = x_array
        self.initGrid(
            rmin, rmax, k, rcf, rcr, por, firstwellcell, kwf, rcwf, drmin, endcellbound
        )

    def initGrid(
        self,
        rmin: float | np.ndarray,
        rmax: float | np.ndarray,
        k: np.ndarray,
        rcf: np.ndarray,
        rcr: np.ndarray,
        por: np.ndarray,
        firstwellcell: bool,
        kwf: float,
        rcwf: float,
        drmin: float,
        endcellbound: bool,
    ) -> None:
        """
        Initialize the grid with radial and axial properties.

        Parameters
        ----------
        rmin : float or np.ndarray
            Radius of first cell face closest to radial axis (>0). Can be array of size nx.
        rmax : float or np.ndarray
            Radius of midpoint of last cell. Used to calculate cell sizes along axis.
        k : np.ndarray
            Bulk conductivity in radial direction (dimension nx).
        rcf : np.ndarray
            Volumetric heat capacity of fluid [J m^-3 K^-1] (dimension nx).
        rcr : np.ndarray
            Volumetric heat capacity of rock [J m^-3 K^-1] (dimension nx).
        por : np.ndarray
            Porosity of cells (dimension nx).
        firstwellcell : bool
            Whether the first cell is a well cell with modified properties.
        kwf : float
            Well fluid thermal conductivity (used if firstwellcell is True).
        rcwf : float
            Well fluid volumetric heat capacity [J m^-3 K^-1] (used if firstwellcell is True).
        drmin : float
            Minimum radius increase for cells (optional).
        endcellbound : bool
            Apply end cell boundary condition (optional) in radial direction as Dirichlet.
        """
        self.dx = np.zeros_like(self.x)
        dxgrid = np.diff(self.x)
        for i in range(self.nx):
            if i > 0:
                self.dx[i] += 0.5 * dxgrid[i - 1]
            if i < self.nx - 1:
                self.dx[i] += 0.5 * dxgrid[i]

        self.rmin = check_asarray(rmin, self.nx)
        self.rmax = check_asarray(rmax, self.nx)
        k = check_asarray(k, self.nx)
        rcf = check_asarray(rcf, self.nx)
        rcr = check_asarray(rcr, self.nx)
        por = check_asarray(por, self.nx)

        gmesh = np.arange(self.nx * self.ny, dtype=float).reshape(self.nx, self.ny, 1)
        gtrans = np.arange(3 * self.nx * self.ny, dtype=float).reshape(
            3, self.nx, self.ny, 1
        )
        # cell sizes in r
        self.axidr = gmesh * 0
        self.axisumdr = gmesh * 0
        # cell midpoints in r
        self.axicellrmid = gmesh * 0
        # transmission values
        self.txyz = gtrans * 0
        # flux values
        self.fxyz = gtrans * 0
        #  heat production values
        self.axyz = gmesh * 0

        # properties
        self.k = gmesh * 0
        self.vol = gmesh * 0
        self.overcp = gmesh * 0
        self.rcf = gmesh * 0
        self.rcbulk = gmesh * 0

        for i in range(self.nx):
            dmin = self.rmin[i]
            logdmin = np.log10(dmin)
            logdmax = np.log10(self.rmax[i])
            # estimate last cell size
            dlog = (logdmax - logdmin) / (self.ny)

            # axisumdx are cell interfaces starting at first to last cell
            axisumdr = np.logspace(logdmin, logdmax + dlog / 2, self.ny, base=10)
            for ir in range(1, self.ny):
                drscale = 1.2
                if (axisumdr[ir] - axisumdr[ir - 1]) < drmin:
                    if ir == 1:
                        dr = axisumdr[0] * drscale
                    else:
                        dr = (axisumdr[ir - 1] - axisumdr[ir - 2]) * drscale
                    dr = drmin
                    axisumdr[ir] = axisumdr[ir - 1] + dr
            # axidr  are cell sizes
            if endcellbound:
                axisumdr = np.logspace(logdmin, logdmax, self.ny, base=10)
            axidr = np.zeros_like(axisumdr)
            axidr[0] = dmin
            axidr[1:] = np.diff(axisumdr)
            axicellrmid = axisumdr - 0.5 * axidr

            axitoparea = axisumdr**2 * np.pi
            axitoparea[1:] = np.diff(axitoparea)

            self.axicellrmid[i] = np.reshape(axicellrmid * 1.0, (self.ny, 1))
            self.axidr[i] = np.reshape(axidr, (self.ny, 1))
            self.axisumdr[i] = np.reshape(axisumdr, (self.ny, 1))
            for j in range(self.ny):
                self.k[i][j][0] = k[i]
                self.rcf[i][j][0] = rcf[i]
                if (firstwellcell) and (j == 0):
                    self.k[i][j][0] = 30  # 30
                    self.rcbulk[i][j][0] = rcwf
                else:
                    self.rcbulk[i][j][0] = rcf[i] * por[i] + rcr[i] * (1 - por[i])
                self.vol[i][j][0] = axitoparea[j] * self.dx[i]
                self.overcp[i][j][0] = 1.0 / (self.vol[i][j][0] * self.rcbulk[i][j][0])

        # setup connection factors, assume only in radial direction (ia=1) for now
        ia = 1
        for i in range(self.nx):
            for j in range(self.ny - 1):
                self.txyz[ia][i][j][0] = (
                    2
                    * np.pi
                    * self.k[i][j][0]
                    * self.dx[i]
                    / np.log(self.axicellrmid[i][j + 1][0] / self.axicellrmid[i][j][0])
                )
                ln1 = np.log(self.axicellrmid[i][j + 1][0] / self.axisumdr[i][j][0])
                ln2 = np.log(self.axisumdr[i][j][0] / self.axicellrmid[i][j][0])
                self.txyz[ia][i][j][0] = (
                    2
                    * np.pi
                    * self.dx[i]
                    / (ln1 / self.k[i][j + 1][0] + ln2 / self.k[i][j][0])
                )
        ia = 0
        for i in range(self.nx - 1):
            for j in range(self.ny):
                self.txyz[ia][i][j][0] = 1 / (
                    0.5 * self.dx[i] ** 2 / (self.k[i][j][0] * self.vol[i][j][0])
                    + 0.5
                    * self.dx[i + 1] ** 2
                    / (self.k[i + 1][j][0] * self.vol[i + 1][j][0])
                )

    def initTempX(self, tempx: np.ndarray) -> None:
        """
        Set the initial temperature values along the x-axis.

        Parameters
        ----------
        tempx : np.ndarray
            Initial temperatures along the x-axis.
        """
        init_val = self.vol * 0.0
        for i in range(self.nx):
            for j in range(self.ny):
                init_val[i][j][0] = tempx[i]
        self.set_initvalues(init_val)

    def setWellFlow(self, q: np.ndarray) -> None:
        """
        Set the flow along the well cells in x-direction (`fxyz[0][i][:]` to `q[i]`) defined along the well path (nx).

        If there are laterals along the well path these can be incorporated by reducing the flow to q=q/nlateral
        at the along hole position of the laterals.

        Parameters
        ----------
        q : np.ndarray
            Flow along the well bore [m³/s] for each cell along the well path (dimension nx).
        """
        for i in range(self.nx):
            self.fxyz[0, i, 0, :] = q[i]

    def setWellA(self, a: np.ndarray) -> None:
        """
        Set the heat production along the well cells (a[i,0,:] to a[i]) defined along the well path (nx).

        Parameters
        ----------
        a : np.ndarray
            Heat production [W] for each cell along the well path (dimension nx).
        """
        for i in range(self.nx):
            self.axyz[i, 0, :] = a[i]

    def plot_result(
        self,
        result: np.ndarray,
        itime: int,
        rmax: float | None = None,
        fname: str | None = None,
        dif: bool = False,
    ) -> None:
        """
        Plot the simulation result at a specific time step.

        Parameters
        ----------
        result : np.ndarray
            Result array from ODE integration.
        itime : int
            Time index to plot.
        rmax : float, optional
            Maximum radius to plot (default is None).
        fname : str, optional
            File name to save the figure (default is None, shows plot).
        dif : bool, optional
            Plot the difference with the first timestep if True (default: False).
        """
        c = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        fig, ax = plt.subplots(1, 1, figsize=(18, 9))
        temp = result[itime].reshape(self.nx, self.ny)
        if dif:
            temp0 = result[0].reshape(self.nx, self.ny)
            temp = temp - temp0
        temptrans = np.transpose(temp)
        xg = self.x
        yg = self.axicellrmid[0].reshape(self.ny)
        cp = ax.contourf(xg, yg, temptrans)
        fig.colorbar(cp)  # Add a colorbar to a plot

        # contour
        if dif:
            ax.set_title("Temperature Difference")
            levels = np.arange(-50, 30, 20)
        else:
            ax.set_title("Temperature")
            levels = np.arange(0, 100, 10)
        decimals = 0
        # cs = plt.contour(xg, yg, temptrans, levels, colors=c[0])
        cs = plt.contour(xg, yg, temptrans, colors=c[0])
        fmt = "%1." + str(decimals) + "f"
        plt.clabel(cs, fmt=fmt)

        ax.set_ylabel("radius (m)")
        ax.set_xlabel("ahd (m)")
        if rmax != None:
            plt.ylim(0, rmax)
        if fname == None:
            plt.show()
        else:
            plt.savefig(fname)


IFLUXF = [1, 0, 0]
JFLUXF = [0, 1, 0]
KFLUXF = [0, 0, 1]


def thomas_heatloop(
    time: np.ndarray,
    dt: float,
    nt: int,
    qscale: np.ndarray,
    t_inlet: float | np.ndarray,
    grid: SimGridRegular,
    ahddif: bool = True,
    fixsurfaceTemp: bool = True,
) -> np.ndarray:
    """
    Solve transient heat transport using a mixed explicit/implicit scheme:
    - Explicit in the along-hole direction (except boundary treatment)
    - Implicit in the radial direction using the Thomas tridiagonal algorithm

    Integrates over the timeseries time, the heat loop specified in grid. This used a mixture of explicit finite difference
    and the implicit thomas algorithm (which is tridiagonal guassian elimination) for the radial diffusion and advective flow.

    The components of the tridiagonal system (a,b,c,d) are in the range of grid.nx

    - b[i] = diagonal (referring to node)
    - a[i] = same row, column to the left (referring to node i-1)
    - c[i] = same row column to the right (referring to node i+1)
    - d[i] = RHS for node i (RHS = right hand side)

    Mathematical documentation available in report Wees et al. (2023), TKI reference: 1921406
    Equation nr. annotations in code  refer to equation nr. in Appendix A of the report.

    Parameters
    ----------
    time : np.ndarray
        1D array of time steps (arbitrary units). Each entry corresponds to a
        point where the solution is stored.
    dt : float
        Scaling factor that converts the time unit in `time` to seconds.
    nt : int
        Number of intermediate timesteps for each main timestep in `time`.
        The solver uses fixed sub-stepping, not adaptive stepping.
        (It does not use the automated timestepping as in odeint)
    qscale : np.ndarray
        1D array scaling the reference mass flow rate over time.
        Must be the same length as `time`.
    t_inlet : float or np.ndarray
        Fixed inlet temperature at the top of the well.
        If array: must have same length as `time`.
    grid : SimGridRegular
        Grid specifying geometry, transmissivities, flow field, and
        thermophysical properties (rock and fluid).
    ahddif : bool, optional
        If True, include along-hole diffusion outside the borehole.
    fixsurfaceTemp : bool, optional
        If True, impose Dirichlet (fixed-temperature) conditions at the
        surface nodes in the along-hole direction.

    Returns
    -------
    np.ndarray
        Temperature field with dimensions
        `(ntimes, nx, ny, nz)`
        where:
        - `time` dimension corresponds to the sampling times in `time`
        - `nx` is the along-hole direction
        - `ny` is the radial direction
        - `nz` is typically 1 (semi-3D axisymmetric model)
    """
    # set up array to be filled with temperature results
    # dimensions: time, nx, ny, nz, dimensions: time, along hole direction, radial direction, z-direction
    # nz = 1, semi-3D grid
    result = np.arange(len(time) * grid.nx * grid.ny * grid.nz, dtype=float).reshape(
        len(time), grid.nx, grid.ny, grid.nz
    )
    nr = grid.ny
    a = np.arange(nr, dtype=float)
    b = a * 0
    c = a * 0
    d = a * 0
    x = a * 0
    tstart = 0
    temp = grid.init_vals * 1.0

    t_inlet = check_asarray(t_inlet, len(time))

    result[0] = temp * 1.0
    for itime in range(1, len(time)):
        # dtime = (time[itime] - time[itime-1])/nt, tstart is update at the end of every timstep
        dtime = (time[itime] - tstart) / nt
        dtimedt = dtime * dt
        # time = time[itime]

        for istep in range(nt):
            scale = np.interp(
                tstart + istep * dtime, time, qscale
            )  # scaling factors for the reference flow interpolated over time
            ia = 1  # flux calculation in radial (dim j) direction
            k = 0  # nz = 1, so no flux to be calculated in z-dimension

            sign_flux = np.sign(grid.fxyz[0][0][0] * scale)

            if sign_flux >= 0:
                range_i = np.arange(grid.nx)
            else:
                range_i = np.arange(grid.nx - 1, -1, -1)

            # i is Along hole index
            # j is radius index
            for i_index, i in enumerate(range_i):
                for j in range(nr):
                    a[j] = 0.0
                    c[j] = 0.0
                    flux = (
                        grid.fxyz[0][i][j][k] * scale
                    )  # scale fluid flux inside borehole in along hole (ia=0) direction

                    try:
                        d[j] = temp[i][j][k] / (
                            grid.overcp[i][j][k] * dtimedt
                        )  # (overcp = 1/cp) eq nr. (9) - RHS
                    except:
                        print("this goes wrong in thomas heat loop")
                        exit()

                    # add along hole diffusion outside borehole
                    adddif = ahddif
                    if adddif:
                        if (i > 0) and (j > 0):
                            d[j] += (temp[i - 1][j][k] - temp[i][j][k]) * grid.txyz[0][
                                i - 1
                            ][j][k]  # RHS in Appendix A.4 - along axis heat conduction
                        if (i < grid.nx - 1) and (j > 0):
                            d[j] += (temp[i + 1][j][k] - temp[i][j][k]) * grid.txyz[0][
                                i
                            ][j][k]  # RHS in Appendix A.4 - along axis heat conduction

                    b[j] = 1 / (grid.overcp[i][j][k] * dtimedt)  # eq nr. (9) left term

                    if j == 0:
                        # well bore include the mass rate
                        if i_index == 0:
                            t_i = t_inlet[
                                itime
                            ]  # for injection set temperature of first cell in along hole direction ('top of well') to inlet temperature, used in eq nr. (14)
                        else:
                            t_i = temp[range_i[i_index - 1]][j][
                                k
                            ]  # temperature used in factor on RHS in eq nr. (13)

                        d[j] += (
                            abs(flux) * t_i * grid.rcbulk[i][j][k]
                        )  # factor on RHS in eq nr. (13)
                        b[j] += (
                            abs(flux) * grid.rcbulk[i][j][k]
                        )  # factor on LHS in eq nr.(13)
                        a[j] = 0
                    else:
                        # add Tj-1/2
                        a[j] = -grid.txyz[ia][i][j - 1][
                            k
                        ]  # middle term in LHS in eq nr. (9)

                    if j < nr - 1:
                        # add Tj+1/2
                        c[j] = -grid.txyz[ia][i][j][
                            k
                        ]  # right term in LHS in eq nr. (9)
                    b[j] = b[j] - a[j] - c[j]  # eq nr. (9)

                    # if boundary condition is set to a fixed surface temperature, temperature in first and last cells in along hole direction is fixed
                    if fixsurfaceTemp:
                        if (i == 0) or (i == grid.nx - 1):
                            if j > 0:
                                # force the temperature in the next time step to remain the same
                                # for the row of equations set only the diagonal (b), rhs (d) and the off diagonal (a,c) to 0
                                b[j] = 1.0 / (grid.overcp[i][j][k] * dtimedt)
                                d[j] = temp[i][j][k] / (grid.overcp[i][j][k] * dtimedt)
                                c[j] = 0.0
                                a[j] = 0.0
                    # fix temperature in first cell in along hole direction ('top of well') to inlet temperature, as defined by input
                    if (i_index == 0) and (j == 0):
                        b[j] = 1.0 / (grid.overcp[i][j][k] * dtimedt)
                        d[j] = t_inlet[itime] / (grid.overcp[i][j][k] * dtimedt)
                        c[j] = 0.0
                        a[j] = 0.0

                # implement algorithm and solve for temperature
                for j in range(1, nr):
                    # forward substitution to create an upper triangular matrix, w is conversion factor to set elements a to 0
                    w = a[j] / b[j - 1]  # matrix decomposition
                    b[j] = b[j] - w * c[j - 1]  # matrix decomposition
                    d[j] = d[j] - w * d[j - 1]  # forward substitution
                # back substitution, start with last element of x
                x[nr - 1] = d[nr - 1] / b[nr - 1]
                for j in range(nr - 1):
                    it2 = (
                        nr - 2 - j
                    )  # iterate backwards over j for remaining elements of x
                    x[it2] = (d[it2] - c[it2] * x[it2 + 1]) / b[it2]

                for j in range(nr):
                    temp[i][j][k] = x[j]

        # end of timestep, append the temp in the result
        result[itime] = temp * 1.0
        # update start of timestep
        tstart = time[itime]

    res2 = result.reshape(len(time), grid.nx, grid.ny, grid.nz)
    return res2
