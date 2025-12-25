import numpy as np
import pygfunction as gt
from scipy.constants import pi

from geoloop.geoloopcore.CoaxialPipe import CoaxialPipe
from geoloop.geoloopcore.CustomPipe import CustomPipe
from geoloop.geoloopcore.simulationparameters import SimulationParameters
from geoloop.geoloopcore.soilproperties import SoilProperties


class PYG_ana:
    """
    Class to simulate a borehole heat exchanger using pygfunction for the determination of the thermal resistivity
    network of the borehole and analytical  g-function.

    Attributes
    ----------
    custom_pipe : CustomPipe
        Depth-dependent borehole configuration and pipe properties.
    soil_props : SoilProperties
        Depth-dependent soil properties (thermal conductivity, temperature profile).
    sim_params : SimulationParameters
        Simulation parameters including time, flow, and input power or temperature.

    Notes
    -----
    The simulation can be run for power  and calls the appropriate function.
    `runsimulation_power` is called for power simulations.

    References
    ----------
    .. [#Cimmino2022]  Cimmino, M., & Cook, J.C. (2022). pygfunction 2.2: New features and improvements in accuracy and computational efficiency.
        In Research Conference Proceedings, IGSHPA Annual Conference 2022 (pp. 45-52).
        International Ground Source Heat Pump Association. DOI: https://doi.org/10.22488/okstate.22.00001
    """

    def __init__(
        self,
        custom_pipe: CustomPipe,
        soil_props: SoilProperties,
        sim_params: SimulationParameters,
    ):
        """
        Constructor for the PYG_ana class.

        Parameters
        ----------
        custom_pipe : CustomPipe
            CustomPipe object defining borehole and pipe properties.
        soil_props : SoilProperties
            SoilProperties object defining soil thermal properties.
        sim_params : SimulationParameters
            SimulationParameters object defining time step, flow rate, and load.
        """
        self.custom_pipe = custom_pipe
        self.soil_props = soil_props
        self.sim_params = sim_params

    def runsimulation(self):
        """
        Main entry point to run the simulation.
        """
        if self.sim_params.run_type == SimulationParameters.POWER:
            return self.runsimulation_power()
        else:
            print("run_type 'TIN' not supported for pyg_ana model type")

    def runsimulation_power(self):
        """
        Run the simulation of the borehole to ground heat exchanger for an input heat demand.

        Returns
        -------
        tuple
            hours, Q_b, flowrate, qsign, T_fi, T_fo, T_bave, z, zseg, T_b, T_ftimes, -qbzseg, h_fpipes
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

        # only one segment simulated because no depth-variation in pyg
        sim_params.nsegments = 1
        nsegments = sim_params.nsegments

        # Load aggregation scheme
        LoadAgg = gt.load_aggregation.ClaessonJaved(sim_params.dt, sim_params.tmax)

        # g-function set-up
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

        # The field contains only one borehole, but needs one extra at very large distance to be correct, ie. gfunc plateaus at 6.7)
        boreField = [
            gt.boreholes.Borehole(
                custom_pipe.b.H,
                custom_pipe.b.D,
                custom_pipe.b.r_b,
                x=0.0,
                y=0.0,
                tilt=np.radians(0.1),
            ),
            gt.boreholes.Borehole(
                custom_pipe.b.H,
                custom_pipe.b.D,
                custom_pipe.b.r_b,
                x=1000.0,
                y=0.0,
                tilt=np.radians(0.1),
            ),
        ]

        # Get time values needed for g-function evaluation
        time_req = LoadAgg.get_times_for_simulation()

        # Calculate g-function
        # g-Function calculation options
        options = {"nSegments": 8, "disp": False}
        np.seterr(under="ignore")

        alpha = soil_props.alfa
        gFunc = gt.gfunction.gFunction(
            boreField, alpha, time=time_req, options=options, method="similarities"
        )

        # Initialize load aggregation scheme
        LoadAgg.initialize(gFunc.gFunc / (2 * pi * k_s))

        Qabsmin = H * 0.1  # assume at least 0.1 W /m to avoid division by zero

        # Delta temperatures are calculated at the segments
        deltaT_b = np.zeros(Nt)
        deltaT_bk = np.zeros((Nt, nsegments))
        power = np.zeros(Nt)
        Q_b = sim_params.Q

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

        ntlow = Nt
        T_b_top = np.zeros(ntlow)
        T_bave = np.zeros(ntlow)
        T_fi = np.zeros(ntlow)
        T_fo = np.zeros(ntlow)

        Q_b = np.zeros(ntlow)
        deltaT_b_ref = np.zeros(ntlow)
        flowrate = np.zeros(ntlow)
        Rs = np.zeros(ntlow)
        qsign = np.zeros(ntlow)

        imax = -1
        for i, t in enumerate(time):
            if (i > imax) and (i < ntlow):
                p = power[i]
                Rs[i] = deltaT_b[i] / (p / H)

        minR = 0.01
        Rs = np.where(np.logical_and(Rs < minR, Rs > -0.5), minR, Rs)

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
        T_g = soil_props.getTg(zseg)

        while iter < niter:
            iter += 1
            imax = -1

            for i, t in enumerate(time):
                if (i > imax) and (i < ntlow):
                    # print(il)
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
