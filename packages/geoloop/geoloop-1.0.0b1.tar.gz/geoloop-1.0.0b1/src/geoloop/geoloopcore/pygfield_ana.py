import numpy as np
import pygfunction as gt
from matplotlib import pyplot as plt
from scipy.constants import pi

from geoloop.geoloopcore.boreholedesign import BoreholeDesign
from geoloop.geoloopcore.CoaxialPipe import CoaxialPipe
from geoloop.geoloopcore.CustomPipe import CustomPipe
from geoloop.geoloopcore.simulationparameters import SimulationParameters
from geoloop.geoloopcore.soilproperties import SoilProperties


def inclination_with_depth(
    depth: float, max_depth: float, initial_inclination: float, final_inclination: float
) -> float:
    """
    Calculate inclination angle with depth.

    Parameters
    ----------
    depth : float
        Depth at which to calculate the inclination (m).
    max_depth : float
        Maximum depth of the borehole (m).
    initial_inclination : float
        Inclination angle at the surface (radians).
    final_inclination : float
        Inclination angle at maximum depth (radians).

    Returns
    -------
    inclination : float
        Inclination angle at the given depth (radians).
    """
    inclination = initial_inclination + (final_inclination - initial_inclination) * (
        depth / max_depth
    )
    return inclination


def create_curved_borehole(
    H: float,
    D: float,
    x: float,
    y: float,
    initial_tilt: float,
    final_tilt: float,
    orientation: float,
    num_segments: int = 10,
):
    """
    Create a borehole with varying inclination by approximating it with straight segments.

    Parameters
    ----------
    H : float
        Borehole length (m).
    D : float
        Borehole burial depth (m)
    x : float
        x-coordinate of the borehole.
    y : float
        y-coordinate of the borehole.
    initial_tilt : float
        Initial borehole inclination (radians).
    final_tilt : float
        Final borehole inclination (radians).
    orientation : float
        Borehole orientation angle (radians).
    num_segments : int, optional
        Number of segments to approximate the varying inclination. The default is 10.

    Returns
    -------
    segments : list
        List of segment coordinates representing the borehole.
        (x_start, y_start, z_start, x_end, y_end, z_end, tilt, orientation)
    """
    segment_length = H / num_segments
    segments = []

    # starting point
    x_current, y_current = x, y
    z_current = D

    for i in range(num_segments):
        # Depth at midpoint of the segment
        depth = (i + 0.5) * segment_length

        # local tilt at this depth
        tilt = inclination_with_depth(depth, H, initial_tilt, final_tilt)

        # compute offsets in 3D
        x_offset = segment_length * np.sin(tilt) * np.cos(orientation)
        y_offset = segment_length * np.sin(tilt) * np.sin(orientation)
        z_offset = segment_length * np.cos(tilt)

        # avoid degeneracy for perfectly vertical segments
        if (x_offset == 0) and (y_offset == 0):
            x_offset = max(1, x_offset)

        x_end = x_current + x_offset
        y_end = y_current + y_offset
        z_end = z_current + z_offset

        segments.append(
            (x_current, y_current, z_current, x_end, y_end, z_end, tilt, orientation)
        )

        # Move to next segment start
        x_current, y_current, z_current = x_end, y_end, z_end

    return segments


def visualize_3d_borehole_field(borefield: list) -> "Figure":
    """
    Produce a simple 3D matplotlib visualization of a borehole field.

    Parameters
    ----------
    borefield : list
        List of boreholes, each itself a list of segments
        defined by (x_start, y_start, z_start, x_end, y_end, z_end, tilt, orientation).

    Returns
    -------
    matplotlib.figure.Figure
        The resulting 3D figure.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    for segments in borefield:
        for (
            x_start,
            y_start,
            z_start,
            x_end,
            y_end,
            z_end,
            tilt,
            orientation,
        ) in segments:
            ax.plot([x_start, x_end], [y_start, y_end], [-z_start, -z_end], "bo-")

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Depth (m)")
    ax.set_title("3D Visualization of Borehole Field")

    return fig


def visualize_gfunc(gfunc: gt.gfunction) -> "Figure":
    """
    Visualize a g-function using the built-in pygfunction plotting utility.

    Parameters
    ----------
    gfunc : gt.gfunction.gFunction
        Computed g-function object.

    Returns
    -------
    matplotlib.figure.Figure
        The plotted g-function.
    """
    fig = gfunc.visualize_g_function()
    fig.suptitle("g-function of borehole field")
    fig.tight_layout()
    return fig


class PYGFIELD_ana:
    """
    Field-level simulation driver using pygfunction and an analytical
    approximation for inclined / curved boreholes.

    This class builds a borehole field from a BoreholeDesign (which may include
    inclined/curved boreholes approximated by segments), computes the g-function,
    runs load aggregation and finally evaluates pipe temperatures using a
    CustomPipe / CoaxialPipe model.
    """

    def __init__(
        self,
        bh_design: BoreholeDesign,
        custom_pipe: CustomPipe,
        soil_props: SoilProperties,
        sim_params: SimulationParameters,
    ):
        """
        Initialize the PYGFIELD_ana model with a given borehole field configuration.

        Parameters
        ----------
        bh_design : BoreholeDesign
            Design describing field layout, inclinations and borehole parameters.
        custom_pipe : CustomPipe or CoaxialPipe
            Pipe/borehole model used for temperature calculations.
        soil_props : SoilProperties
            Soil parameters and temperature profile provider.
        sim_params : SimulationParameters
            Simulation control parameters (time vector, loads, flow, run type).
        """
        self.bh_design = bh_design
        self.custom_pipe = custom_pipe
        self.soil_props = soil_props
        self.sim_params = sim_params

    def runsimulation(self):
        """
        Dispatch to the appropriate simulation routine based on run_type.
        """
        if self.sim_params.run_type == SimulationParameters.POWER:
            return self.runsimulation_power()

        else:
            # TIN mode is not implemented in this bhe field driver
            raise NotImplementedError("run_type 'TIN' is not supported by PYGFIELD_ana")

    def runsimulation_power(self) -> tuple:
        """
        Run a power-driven simulation (POWER) for the borehole field.

        Notes
        ------
        The method:
        - Converts the provided pipe model to a pygfunction-compatible object
          (if necessary),
        - Builds a borehole field according to BoreholeDesign (inclined/curved
          boreholes are approximated by segments),
        - Computes the g-function for the field,
        - Initializes load aggregation (Claesson-Javed) and applies the simulated
          loads, and
        - Calls the pipe model to obtain fluid temperatures and extraction rates.

        Returns
        -------
        tuple
            (hours, Q_b, flowrate, qsign, T_fi, T_fo, T_bave, z, zseg, T_b,
             T_ftimes, -qbzseg, h_fpipes)
        """
        sim_params = self.sim_params
        custom_pipe = self.custom_pipe
        soil_props = self.soil_props

        # Extract fluid properties from custom_pipe object
        cp_f = custom_pipe.cp_f

        # Convert the custompipe to the pyg singleutube design with adopted parameters
        if isinstance(custom_pipe, CoaxialPipe):
            coaxial = custom_pipe.create_coaxial()
            custom_pipe = coaxial
        elif isinstance(custom_pipe, CustomPipe):
            multiUTube = custom_pipe.create_multi_u_tube()
            custom_pipe = multiUTube

        # only one segment simulated because no depthvar in pyg
        sim_params.nsegments = 1

        nsegments = sim_params.nsegments

        # Load aggregation scheme
        LoadAgg = gt.load_aggregation.ClaessonJaved(sim_params.dt, sim_params.tmax)

        # Geometry and time arrays
        H = custom_pipe.b.H
        D = custom_pipe.b.D
        Nt = sim_params.Nt
        time = sim_params.time
        m_flow = sim_params.m_flow[0]
        scaleflow = sim_params.m_flow / m_flow

        dz = H / nsegments
        zmin = D + 0.5 * dz
        zmax = D + H - 0.5 * dz
        zseg = np.linspace(zmin, zmax, nsegments)
        zz = np.linspace(D, D + H, nsegments + 1)
        k_s = soil_props.get_k_s(zz[0:-1], zz[1:], sim_params.isample)

        # Build borefield from BoreholeDesign
        borehole_field = []
        N = self.bh_design.N
        M = self.bh_design.M
        R = self.bh_design.R
        num_segments = self.bh_design.num_tiltedsegments

        print(
            "N = total nr. of boreholes, "
            "M = nr. of boreholes per side of the field, "
            "R = Distance between boreholes",
            N,
            M,
            R,
        )

        # Circular / radial arrangement when M <= 0
        if M <= 0:
            initial_tilt = np.deg2rad(self.bh_design.inclination_start)
            final_tilt = np.deg2rad(self.bh_design.inclination_end)

            # Create curved boreholes and flatten to pyg Borehole objects
            for i in range(N):
                angle = 2 * np.pi * i / N
                x = R * np.cos(angle)
                y = R * np.sin(angle)

                segments = create_curved_borehole(
                    custom_pipe.b.H,
                    custom_pipe.b.D,
                    x,
                    y,
                    initial_tilt,
                    final_tilt,
                    angle,
                    num_segments=num_segments,
                )
                borehole_field.append(segments)

            self.borefield = borehole_field

            borehole_field_flat = [
                gt.boreholes.Borehole(
                    custom_pipe.b.H / num_segments,
                    z,
                    custom_pipe.b.r_b,
                    x,
                    y,
                    tilt=tilt,
                    orientation=orientation,
                )
                for segments in borehole_field
                for (x, y, z, _, _, _, tilt, orientation) in segments
            ]

        else:
            # Rectangular field arrangement (N must be multiple of M)
            Ng = int(N / M)
            if (Ng * M) != N:
                print("N must be a multiple of M for agrid arrangement")
                exit()

            B = R
            tilt = 0.5 * (
                np.deg2rad(self.bh_design.inclination_start)
                + np.deg2rad(self.bh_design.inclination_end)
            )

            borehole_field_flat = gt.borefield.Borefield.rectangle_field(
                Ng,
                M,
                B,
                B,
                custom_pipe.b.H,
                custom_pipe.b.D,
                custom_pipe.b.r_b,
                tilt=tilt,
            )
            gt.borefield.Borefield.visualize_field(borehole_field_flat)

            self.borefield = borehole_field_flat

        # Compute g-function for the built field
        alpha = soil_props.alfa
        method = "similarities"
        options = {"nSegments": 1}

        time_req = LoadAgg.get_times_for_simulation()

        # Compute g-function (newer pygfunction versions accept keyword args alpha=, time=)
        np.seterr(under="ignore")
        stringbc = "UBWT"
        gFunc = gt.gfunction.gFunction(
            borehole_field_flat,
            alpha,
            time=time_req,
            options=options,
            method=method,
            boundary_condition=stringbc,
        )
        np.seterr(under="warn")

        # Store for later inspection / plotting
        self.gfunc = gFunc

        # Initialize load aggregation scheme
        LoadAgg.initialize(gFunc.gFunc / (2 * pi * k_s))

        Qabsmin = H * 0.1  # assume at least 0.1 W /m to avoid division by zero

        # Delta temperatures are calculated at the segments
        deltaT_b = np.zeros(Nt)
        deltaT_bk = np.zeros((Nt, nsegments))
        power = np.zeros(Nt)
        Q_b = sim_params.Q / N  # per-borehole load

        for i, (t, Q_b_i) in enumerate(zip(time, Q_b)):
            # Increment time step by (1)
            LoadAgg.next_time_step(t)

            # avoid the Q_B_i to be zero, it is at least the 10% of H in watts
            if abs(Q_b_i) < Qabsmin:
                Q_b_i = Qabsmin * np.sign(Q_b_i)

            # Apply current load
            LoadAgg.set_current_load(Q_b_i / H)

            deltaT_bk[i] = LoadAgg.temporal_superposition()
            deltaT_b[i] = LoadAgg.temporal_superposition()
            power[i] = Q_b_i

        # Prepare storage arrays
        T_b_top = np.zeros(Nt)
        T_bave = np.zeros(Nt)
        T_fi = np.zeros(Nt)
        T_fo = np.zeros(Nt)

        Q_b = np.zeros(Nt)
        deltaT_b_ref = np.zeros(Nt)
        flowrate = np.zeros(Nt)
        Rs = np.zeros(Nt)
        qsign = np.zeros(Nt)

        imax = -1
        for i, t in enumerate(time):
            if (i > imax) and (i < Nt):
                p = power[i]
                Rs[i] = deltaT_b[i] / (p / H)

        minR = 0.01
        Rs = np.where(np.logical_and(Rs < minR, Rs > -0.5), minR, Rs)

        # Iterative refinement to compute pipe & borehole temperatures
        iter = 0
        niter = 3
        # Rsz not filled because not used in pyg-function
        qbzseg = np.zeros((len(Rs), nsegments))
        T_b = np.zeros((len(Rs), nsegments))
        h_fpipes = np.zeros(
            (len(Rs), (custom_pipe.nInlets + custom_pipe.nOutlets) * custom_pipe.nPipes)
        )

        # nPipes is defined differently for standard pyg and the analytical model; in pyg nPipes defines the number of utubes,
        # in the analytical model nPipes defines the nr of pipes
        nz = 20
        z = np.linspace(0.0, H, num=nz)
        T_ftimes = np.zeros(
            (
                len(Rs),
                nz,
                (custom_pipe.nInlets + custom_pipe.nOutlets) * custom_pipe.nPipes,
            )
        )

        # soil temperature
        T_g = soil_props.getTg(zseg)

        while iter < niter:
            iter += 1
            imax = -1

            for i, t in enumerate(time):
                if (i > imax) and (i < Nt):
                    p = power[i]
                    h_f = custom_pipe.h_f

                    T_b[i] = np.asarray(T_g - deltaT_b[i])

                    T_f_in = custom_pipe.get_inlet_temperature(
                        p, T_b[i], scaleflow[i] * m_flow, cp_f
                    )
                    T_f_out = custom_pipe.get_outlet_temperature(
                        T_f_in, T_b[i], scaleflow[i] * m_flow, cp_f
                    )

                    # To compare between depth variation between pyg and ana; Evaluate temperatures fro pyg at nz evenly spaced depths along the borehole
                    # at the (it+1)-th time step
                    T_f = custom_pipe.get_temperature(
                        z, T_f_in, T_b[i], scaleflow[i] * m_flow, cp_f
                    )

                    qbz = custom_pipe.get_total_heat_extraction_rate(
                        T_f_in, T_b[i], scaleflow[i] * m_flow, cp_f
                    )

                    # Store outputs per time-step
                    Q_b[i] = power[i]
                    T_b_top[i] = T_b[i][0]
                    deltaT_b_ref[i] = deltaT_b[i]
                    T_bave[i] = np.average(T_b[i, :])
                    T_fi[i] = T_f_in
                    T_fo[i] = T_f_out
                    h_fpipes[i] = h_f
                    flowrate[i] = scaleflow[i] * m_flow
                    T_ftimes[i] = T_f  # stored index time, depth, pipe
                    # zseg 1 value less than z
                    qbzseg[i] = qbz / custom_pipe.b.H
                    qsign[i] = np.sign(qbz)
                    imax = i

        hours = time / 3600.0

        return (
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
            T_ftimes,
            -qbzseg,
            h_fpipes,
        )
