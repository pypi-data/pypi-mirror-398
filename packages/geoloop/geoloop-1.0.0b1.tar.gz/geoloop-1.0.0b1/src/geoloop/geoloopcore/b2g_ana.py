import numpy as np
import pygfunction as gt
from scipy.constants import pi

from geoloop.geoloopcore.CustomPipe import CustomPipe
from geoloop.geoloopcore.simulationparameters import SimulationParameters
from geoloop.geoloopcore.soilproperties import SoilProperties


class B2G_ana:
    """
    Class for analytical / semi-analytical borehole-to-ground simulation.

    This class uses pygfunction's g-function and a load aggregation scheme
    (Claesson-Javed) to compute borehole wall temperatures and then obtains
    fluid/pipe temperatures from `CustomPipe` methods.

    Attributes
    ----------
    custom_pipe : CustomPipe
        Depth-dependent borehole configuration and properties.
    soil_props : SoilProperties
        Depth-dependent soil parameters (conductivity and temperature).
    sim_params : SimulationParameters
        Simulation parameters (time, flow, power, temperature).

    Notes
    -----
    The simulation can be run for input power or input temperature and calls the appropriate function.
    `runsimulation_power` is called for power simulations
    `runsimulation_temperature` is called for temperature simulations
    """

    def __init__(
        self,
        custom_pipe: CustomPipe,
        soil_properties: SoilProperties,
        simulation_parameters: SimulationParameters,
    ) -> None:
        """
        Initialize the analytical BHE model wrapper.

        Parameters
        ----------
        custom_pipe : CustomPipe
            Pipe/borehole configuration object.
        soil_properties : SoilProperties
            Soil properties provider.
        simulation_parameters : SimulationParameters
            Operational and simulation parameters.
        """
        self.custom_pipe = custom_pipe
        self.soil_props = soil_properties
        self.sim_params = simulation_parameters

    def runsimulation(self):
        """
        Run the simulation of the borehole to ground heat exchanger.

        Returns
        -------
        tuple
            (hours, Q_b, flowrate, qsign, T_fi, T_fo, T_bave,
            z, zseg, T_b, T_ftimes, qbzseg, h_fpipes)
        """
        if self.sim_params.run_type == SimulationParameters.POWER:
            return self.runsimulation_power()
        else:
            return self.runsimulation_temperature()

    def runsimulation_temperature(self) -> tuple:
        """
        Run the simulation of the borehole to ground heat exchanger for an input inlet temperature.

        The method:
        - computes the segment-wise g-function scaling,
        - uses load-aggregation to obtain borehole wall temperature response,
        - calls CustomPipe methods to compute fluid temperatures for each time step.

        Returns
        -------
        tuple
            (hours, Q_b, flowrate, qsign, T_fi, T_fo, T_bave,
             z, zseg, T_b, T_ftimes, qbzseg, h_fpipes)
        """
        sim_params = self.sim_params
        custom_pipe = self.custom_pipe
        soil_props = self.soil_props
        nsegments = sim_params.nsegments

        # temporal arrays and derived geometry
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
        z = np.linspace(D, D + H, nsegments + 1)

        # Build load aggregation + g-function once
        LoadAgg = []
        for k in range(nsegments):
            la = gt.load_aggregation.ClaessonJaved(sim_params.dt, sim_params.tmax)
            LoadAgg.append(la)
        # TODO: JD: the workaround below was not reuired anymore?
        # The field contains only one borehole
        # boreField = [gt.boreholes.Borehole(custom_pipe.b.H, custom_pipe.b.D, custom_pipe.b.r_b, x=0., y=0.)]
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
        time_req = LoadAgg[0].get_times_for_simulation()

        # Calculate g-function
        # g-Function calculation options
        options = {"nSegments": 8, "disp": False}
        np.seterr(under="ignore")

        alpha = soil_props.alfa
        gFunc = gt.gfunction.gFunction(
            boreField, alpha, time=time_req, options=options, method="similarities"
        )

        # Initialize load aggregation scheme
        for k in range(nsegments):
            LoadAgg[k].initialize(gFunc.gFunc / (2 * pi * k_s[k]))

        # Protect agains zero loads
        Qabsmin = H * 0.1  # assume at least 0.1 W /m to avoid division by zero

        # Compute deltaT_b by temporal superposition for each segment/time
        deltaT_b = np.zeros(Nt)
        deltaT_bk = np.zeros((Nt, nsegments))
        power = np.zeros(Nt)
        Q_b = sim_params.Q

        # First pass: compute deltaT_b using aggregated loads
        for i, (t, Q_b_i) in enumerate(zip(time, Q_b)):
            # avoid the Q_B_i to be zero, it is at least the 10% of H in watts
            if abs(Q_b_i) < Qabsmin:
                Q_b_i = Qabsmin * np.sign(Q_b_i)

            # Increment time step by (1)
            for k in range(nsegments):
                LoadAgg[k].next_time_step(t)
                # Apply current load
                LoadAgg[k].set_current_load(Q_b_i / H)

            # Evaluate the average borehole wall temeprature
            deltaT_b[i] = 0
            for k in range(nsegments):
                deltaT_bk[i, k] = LoadAgg[k].temporal_superposition()

            deltaT_b[i] = np.average(deltaT_bk[i, :])
            power[i] = Q_b_i

        # Initialize output containers
        T_b_top = np.zeros(Nt)
        T_bave = np.zeros(Nt)
        T_fi = np.zeros(Nt)
        T_fo = np.zeros(Nt)

        Q_b = np.zeros(Nt)
        deltaT_b_ref = np.zeros(Nt)
        flowrate = np.zeros(Nt)
        Rs = np.zeros(Nt)
        qsign = np.zeros(Nt)

        # Initial guess for Rs (borehole thermal resistance) per time step
        imax = -1
        for i, t in enumerate(time):
            if (i > imax) and (i < Nt):
                p = power[i]
                Rs[i] = deltaT_b[i] / (p / H)

        minR = 0.01
        Rs = np.where(np.logical_and(Rs < minR, Rs > -0.5), minR, Rs)

        # iterate to refine Rsz using qbzseg from pipe model (few iterations)
        iter = 0
        niter = 3
        Rsz = np.zeros((len(Rs), nsegments))
        qbzseg = np.zeros((len(Rs), nsegments))
        T_b = np.zeros((len(Rs), nsegments))
        h_fpipes = np.zeros((len(Rs), custom_pipe.nPipes))
        T_ftimes = np.zeros((len(Rs), nsegments + 1, custom_pipe.nPipes))

        while iter < niter:
            if iter == 0:
                for i, rsi in enumerate(Rs):
                    Rsz[i] = rsi * np.ones(nsegments)

            else:
                # Recompute g-function/loadaggs (keeps same options)
                alpha = soil_props.alfa
                gFunc = gt.gfunction.gFunction(
                    boreField,
                    alpha,
                    time=time_req,
                    options=options,
                    method="similarities",
                )

                # Reset load aggregation
                for k in range(nsegments):
                    LoadAgg[k] = gt.load_aggregation.ClaessonJaved(
                        sim_params.dt, sim_params.tmax
                    )
                    # Initialize load aggregation scheme
                    LoadAgg[k].initialize(gFunc.gFunc / (2 * pi * k_s[k]))

                Rsz = np.zeros((len(Rs), nsegments))
                for k in range(nsegments):
                    # this only works if time is same as reduced time array
                    for i, (t, Q_b_i) in enumerate(zip(time, qbzseg[:, k])):
                        # Increment time step by (1)
                        LoadAgg[k].next_time_step(t)

                        if abs(Q_b_i * H) < Qabsmin:
                            Q_b_i = Qabsmin * np.sign(Q_b_i) / H

                        # Apply current load
                        LoadAgg[k].set_current_load(Q_b_i)

                        # Evaluate borehole wall temeprature
                        deltaT_bk[i][k] = LoadAgg[k].temporal_superposition()
                        Rsz[i, k] = deltaT_bk[i][k] / qbzseg[i, k]

            # For each time-step compute fluid solution using CustomPipe
            iter += 1
            imax = -1
            for i, t in enumerate(time):
                if (i > imax) and (i < Nt):
                    p = power[i]
                    custom_pipe.update_scaleflow(scaleflow[i])
                    h_f = custom_pipe.h_f
                    signpower = np.sign(p)
                    T_f_in = sim_params.Tin[i]

                    T_f_out, p, Reff, T_f, Tb, qbz = (
                        custom_pipe.get_temperature_depthvar(
                            T_f_in,
                            signpower,
                            Rsz[i],
                            soil_props=soil_props,
                            nsegments=nsegments,
                        )
                    )

                    Q_b[i] = p
                    T_b_top[i] = Tb[0]
                    deltaT_b_ref[i] = deltaT_b[i]
                    T_bave[i] = np.average(Tb)
                    T_fi[i] = T_f_in
                    h_fpipes[i] = h_f
                    T_fo[i] = T_f_out
                    flowrate[i] = scaleflow[i] * m_flow
                    T_ftimes[i] = T_f  # stored index time, depth, pipe
                    T_b[i] = Tb
                    qbzseg[i] = qbz
                    qsign[i] = np.sign(max(qbz) * min(qbz))
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
            qbzseg,
            h_fpipes,
        )

    def runsimulation_power(self) -> tuple:
        """
        Run the simulation of the borehole to ground heat exchanger for an input heat demand.

        Returns
        -------
        tuple
            (hours, Q_b, flowrate, qsign, T_fi, T_fo, T_bave,
             z, zseg, T_b, T_ftimes, qbzseg, h_fpipes)
        """
        sim_params = self.sim_params
        custom_pipe = self.custom_pipe
        soil_props = self.soil_props
        nsegments = sim_params.nsegments

        # geomertry and derived arrays
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
        z = np.linspace(D, D + H, nsegments + 1)

        # prepare load aggregation + gfunc
        # The field contains only one borehole
        old = False
        if old:
            boreField = [
                gt.boreholes.Borehole(
                    custom_pipe.b.H, custom_pipe.b.D, custom_pipe.b.r_b, x=0.0, y=0.0
                )
            ]
        # The field contains only one borehole, but needs one extra at very large distance to be correct, ie. gfunc plateaus at 6.7)
        else:
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

        LoadAgg = []
        for k in range(nsegments):
            la = gt.load_aggregation.ClaessonJaved(sim_params.dt, sim_params.tmax)
            LoadAgg.append(la)

        # Get time values needed for g-function evaluation
        time_req = LoadAgg[0].get_times_for_simulation()

        # Calculate g-function
        # g-Function calculation options
        options = {"nSegments": 8, "disp": False}
        np.seterr(under="ignore")

        alpha = soil_props.alfa
        gFunc = gt.gfunction.gFunction(
            boreField, alpha, time=time_req, options=options, method="similarities"
        )

        # initialize load aggregation scheme
        for k in range(nsegments):
            LoadAgg[k].initialize(gFunc.gFunc / (2 * pi * k_s[k]))

        Qabsmin = H * 0.1  # assume at least 0.1 W /m to avoid division by zero

        deltaT_b = np.zeros(Nt)
        deltaT_bk = np.zeros((Nt, nsegments))
        power = np.zeros(Nt)
        Q_b = sim_params.Q

        for i, (t, Q_b_i) in enumerate(zip(time, Q_b)):
            # avoid the Q_B_i to be zero, it is at least the 10% of H in watts
            if abs(Q_b_i) < Qabsmin:
                Q_b_i = Qabsmin * np.sign(Q_b_i)

            # Increment time step by (1)
            for k in range(nsegments):
                LoadAgg[k].next_time_step(t)
                # Apply current load
                LoadAgg[k].set_current_load(Q_b_i / H)

            # Evaluate the average borehole wall temeprature
            deltaT_b[i] = 0
            for k in range(nsegments):
                deltaT_bk[i, k] = LoadAgg[k].temporal_superposition()

            deltaT_b[i] = np.average(deltaT_bk[i, :])
            power[i] = Q_b_i

        T_b_top = np.zeros(Nt)
        T_bave = np.zeros(Nt)
        T_fi = np.zeros(Nt)
        T_fo = np.zeros(Nt)

        Q_b = np.zeros(Nt)
        deltaT_b_ref = np.zeros(Nt)
        flowrate = np.zeros(Nt)
        Rs = np.zeros(Nt)
        qsign = np.zeros(Nt)

        #  compute initial Rs
        imax = -1
        for i, t in enumerate(time):
            if (i > imax) and (i < Nt):
                power_i = power[i]
                p = np.maximum(power_i, 100)
                Rs[i] = deltaT_b[i] / (p / H)

        minR = 0.01
        Rs = np.where(np.logical_and(Rs < minR, Rs > -0.5), minR, Rs)

        # iterative refinement
        iter = 0
        niter = 3
        Rsz = np.zeros((len(Rs), nsegments))
        qbzseg = np.zeros((len(Rs), nsegments))
        T_b = np.zeros((len(Rs), nsegments))
        h_fpipes = np.zeros((len(Rs), custom_pipe.nPipes))
        T_ftimes = np.zeros((len(Rs), nsegments + 1, custom_pipe.nPipes))

        while iter < niter:
            if iter == 0:
                for i, rsi in enumerate(Rs):
                    Rsz[i] = rsi * np.ones(nsegments)

            else:
                # reinitilize  g-function
                alpha = soil_props.alfa
                gFunc = gt.gfunction.gFunction(
                    boreField,
                    alpha,
                    time=time_req,
                    options=options,
                    method="similarities",
                )

                # Reinitialize load aggregation scheme
                for k in range(nsegments):
                    LoadAgg[k] = gt.load_aggregation.ClaessonJaved(
                        sim_params.dt, sim_params.tmax
                    )
                    LoadAgg[k].initialize(gFunc.gFunc / (2 * pi * k_s[k]))

                Rsz = np.zeros((len(Rs), nsegments))
                for k in range(nsegments):
                    # this only works if time is same as reduced time array
                    for i, (t, Q_b_i) in enumerate(zip(time, qbzseg[:, k])):
                        # Increment time step by (1)
                        LoadAgg[k].next_time_step(t)

                        if abs(Q_b_i * H) < Qabsmin:
                            Q_b_i = Qabsmin * np.sign(Q_b_i) / H

                        # Apply current load
                        LoadAgg[k].set_current_load(Q_b_i)

                        # Evaluate borehole wall temeprature
                        deltaT_bk[i][k] = LoadAgg[k].temporal_superposition()
                        Rsz[i, k] = deltaT_bk[i][k] / qbzseg[i, k]
            iter += 1
            imax = -1

            # compute fluid temperatures for this iteration
            for i, t in enumerate(time):
                if (i > imax) and (i < Nt):
                    # print(il)
                    power_i = power[i]
                    custom_pipe.update_scaleflow(scaleflow[i])
                    h_f = custom_pipe.h_f

                    (T_f_out, T_f_in, Reff, T_f, Tb, qbz) = (
                        custom_pipe.get_temperature_depthvar_power(
                            power_i, Rsz[i], soil_props, nsegments=nsegments
                        )
                    )

                    Q_b[i] = power[i]
                    T_b_top[i] = Tb[0]
                    deltaT_b_ref[i] = deltaT_b[i]
                    T_bave[i] = np.average(Tb)
                    T_fi[i] = T_f_in
                    h_fpipes[i] = h_f
                    T_fo[i] = T_f_out
                    flowrate[i] = scaleflow[i] * m_flow
                    T_ftimes[i] = T_f  # stored index time, depth, pipe
                    T_b[i] = Tb
                    # qbz is calculated at the depth division in segments (zseg)
                    qbzseg[i] = qbz
                    qsign[i] = np.sign(max(qbz) * min(qbz))
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
            qbzseg,
            h_fpipes,
        )
