import unittest

import numpy as np

from geoloop.configuration import load_nested_config, SingleRunConfig, LithologyConfig
from geoloop.bin.SingleRunSim import SingleRun
from geoloop.constants import tests_input_path
from geoloop.geoloopcore.pygfield_ana import (
    PYGFIELD_ana,
    create_curved_borehole,
    inclination_with_depth,
)
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


class TestInclinationAndGeometry(unittest.TestCase):
    def test_inclination_with_depth_linear(self):
        """Inclination must interpolate linearly from initial to final."""
        inc0 = 0.0
        inc1 = np.pi / 4
        H = 100

        self.assertAlmostEqual(inclination_with_depth(0, H, inc0, inc1), inc0)

        self.assertAlmostEqual(inclination_with_depth(H, H, inc0, inc1), inc1)

        self.assertAlmostEqual(
            inclination_with_depth(H / 2, H, inc0, inc1), (inc0 + inc1) / 2
        )

    def test_create_curved_borehole_segment_count(self):
        """The function must return num_segments entries."""
        H = 100
        D = 2
        num_segments = 8

        segs = create_curved_borehole(
            H=H,
            D=D,
            x=0,
            y=0,
            initial_tilt=0.0,
            final_tilt=np.deg2rad(10),
            orientation=0.0,
            num_segments=num_segments,
        )

        self.assertEqual(len(segs), num_segments)

    def test_create_curved_borehole_progresses_downwards(self):
        """Z must increase monotonically (borehole gets deeper)."""
        segs = create_curved_borehole(
            H=50,
            D=1,
            x=0,
            y=0,
            initial_tilt=0,
            final_tilt=np.deg2rad(5),
            orientation=0,
            num_segments=5,
        )

        z_starts = [s[2] for s in segs]
        z_ends = [s[5] for s in segs]

        # all z_end > z_start
        for zs, ze in zip(z_starts, z_ends):
            self.assertGreater(ze, zs)


class TestPYGFIELD_ana(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "pygfield_ana_test.json"
        )  # Directory containing this test script

        # Load configuration
        keysneeded = []
        keysoptional = ["litho_k_param", "loadprofile", "borefield", "flow_data", "variables_config"]
        config_dict = load_nested_config(configfile_path, keysneeded, keysoptional)

        self.config = SingleRunConfig(**config_dict)  # validated Pydantic object

        self.config.lithology_to_k = None
        # lithology to conductivity (optional)
        if self.config.litho_k_param:
            # in a single run always set the base case to True
            self.config.litho_k_param["basecase"] = True
            lithology_to_k = ProcessLithologyToThermalConductivity.from_config(LithologyConfig(**self.config.litho_k_param))
            lithology_to_k.create_multi_thermcon_profiles()
            self.config.lithology_to_k = lithology_to_k

        self.singlerun = SingleRun.from_config(self.config)

        # Extract needed attributes for tests
        self.bh_design = self.singlerun.bh_design
        self.soil_props = self.singlerun.soil_props
        self.sim_params = self.singlerun.sim_params

        self.sim_params.isample = -1

    def test_runsimulation_produces_output(self):
        """Ensure simulation executes and returns expected tuple structure."""
        pygfield = PYGFIELD_ana(
            self.bh_design,
            self.singlerun.bh_design.customPipe,
            self.soil_props,
            self.sim_params,
        )

        out = pygfield.runsimulation()

        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 13)

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
            T_ftimes,
            qbzseg,
            h_fp,
        ) = out

        # validate some shapes
        Nt = len(self.sim_params.time)
        self.assertEqual(len(Q_b), Nt)
        self.assertEqual(len(T_fi), Nt)
        self.assertEqual(len(T_fo), Nt)
        self.assertEqual(T_b.shape[0], Nt)

        borefield = pygfield.borefield

        # Test how nr. fluid temperatures corresponds to nr boreholes
        self.assertTrue(T_ftimes.shape[1] == borefield.nBoreholes / 2)

        # test how nr. of inclination values corresponds to nr. of boreholes
        self.assertTrue(len(borefield.tilt) == borefield.nBoreholes)


if __name__ == "__main__":
    unittest.main()
