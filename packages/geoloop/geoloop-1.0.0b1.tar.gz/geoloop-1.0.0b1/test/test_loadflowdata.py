import unittest

import numpy as np

from geoloop.configuration import LoadProfileConfig, FlowDataConfig, load_single_config
from geoloop.utils.helpers import apply_smoothing
from geoloop.constants import tests_input_path, test_output_path
from geoloop.loadflowdata.flow_data import FlowData
from geoloop.loadflowdata.loadprofile import LoadProfile


class TestLoadprofile(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "test_loadprofile.json"
        )  # Directory containing this test script

        # Load the configuration
        self.config_dict = load_single_config(configfile_path)

        self.config_dict["lp_outdir"] = test_output_path

        self.config = LoadProfileConfig(**self.config_dict)

        # initiate object for lithology_to_k simulation
        self.loadprofile = LoadProfile.from_config(self.config)

    def test_flowdata(self):
        """Ensure object initializes and data call works."""
        self.loadprofile.type = "FROMFILE"

        times = np.array([0, 1, 2])
        load, flow = self.loadprofile.getloadflow(times, m_flow=10)

        self.assertEqual(len(load), 3)
        self.assertEqual(len(flow), 3)

    def test_constant_load(self):
        # Convert the lp_type parameter to CONTANT to test this functionality
        self.loadprofile.type = "CONSTANT"

        times = np.array([0, 4, 10])
        load = self.loadprofile.getload(times)

        # Constant load profile returns peak everywhere
        self.assertTrue(np.all(load == self.loadprofile.peak))

    def test_variable_load(self):
        self.loadprofile.type = "VARIABLE"

        times = np.linspace(0, 8760, 10)
        load = self.loadprofile.getload(times)

        self.assertEqual(len(load), len(times))
        # Should oscillate between base and peak
        self.assertLessEqual(load.max(), self.loadprofile.peak + 1e-6)
        self.assertGreaterEqual(load.min(), self.loadprofile.base - 1e-6)

    def test_fromfile_load(self):
        self.loadprofile.type = "FROMFILE"

        times = np.array([0, 1, 2])
        load = self.loadprofile.getload(times)

        self.assertEqual(len(load), len(times))
        # Basic sanity
        self.assertTrue(np.all(np.isfinite(load)))

    def test_periodic_interpolation(self):
        self.loadprofile.type = "FROMFILE"

        times = np.array([0, len(self.loadprofile.load_data) - 1])
        load = self.loadprofile.getload(times)
        self.assertEqual(len(load), 2)
        # Should interpolate valid values
        self.assertTrue(np.all(np.isfinite(load)))

    def test_flow_scaling(self):
        times = np.array([0, 1, 2, 3])
        m_flow = 5

        load, flow = self.loadprofile.getloadflow(times, m_flow)

        self.assertEqual(len(load), len(flow))
        # Flow must be ≥ minscaleflow * m_flow
        self.assertTrue(np.all(flow >= self.loadprofile.minscaleflow * m_flow))

    def test_minQ_clamping(self):
        self.loadprofile.type = "FROMFILE"

        times = np.array([0, 1, 2])
        load = self.loadprofile.getload(times)

        # If minQ > 0, all positive values must satisfy >= minQ
        if self.loadprofile.minQ > 0:
            self.assertTrue(np.all(np.abs(load) >= self.loadprofile.minQ))


class TestFlowData(unittest.TestCase):
    def setUp(self):
        configfile_path = tests_input_path / "test_flow_data.json"
        self.config_dict = load_single_config(configfile_path)

        self.config_dict["fp_outdir"] = test_output_path

        self.config = FlowDataConfig(**self.config_dict)

        self.flow = FlowData.from_config(self.config)

    def test_constant_flow(self):
        self.flow.type = "CONSTANT"

        times = np.array([0, 12, 100])
        vals = self.flow.getflow(times)

        self.assertTrue(np.all(vals == self.flow.peak_flow))

    def test_variable_flow(self):
        self.flow.type = "VARIABLE"

        times = np.linspace(0, 8760, 20)
        vals = self.flow.getflow(times)

        self.assertEqual(len(vals), 20)
        self.assertLessEqual(vals.max(), self.flow.peak_flow + 1e-6)
        self.assertGreaterEqual(vals.min(), self.flow.base_flow - 1e-6)

    def test_fromfile_flow(self):
        self.flow.type = "FROMFILE"

        times = np.array([0, 5, 10])
        vals = self.flow.getflow(times)

        self.assertEqual(len(vals), 3)
        self.assertTrue(np.all(np.isfinite(vals)))

    def test_fromfile_periodicity(self):
        self.flow.type = "FROMFILE"

        n = len(self.flow.flow_data)
        times = np.array([0, n, n + 10])
        vals = self.flow.getflow(times)

        self.assertEqual(len(vals), 3)
        self.assertTrue(np.all(np.isfinite(vals)))

    def test_flow_scaling(self):
        self.flow.type = "FROMFILE"

        times = np.array([0, 1, 2])
        raw = np.asarray(self.flow.flow_data[self.flow.inputcolumn])
        scaled_check = self.flow.scale

        vals = self.flow.getflow(times)

        self.assertTrue(np.allclose(vals[:2] / raw[:2], scaled_check))

    def test_flow_smoothing_called(self):
        self.flow.smoothing = "M"

        # test wheter the first and second value of the flow profile with daily data are not equal
        self.assertTrue(
            self.flow.flow_data.values[0, 1] != self.flow.flow_data.values[1, 1]
        )

        smooth_data = apply_smoothing(
            self.flow.flow_data,
            column=self.flow.inputcolumn,
            smoothing=self.flow.smoothing,
            outdir=self.flow.outdir,
            prefix="flow",
        )

        # test whether the first 30 values in the flow profile with daily data are equal
        self.assertTrue(
            (smooth_data.m_flow.values[:30] == smooth_data.m_flow.values[0]).all()
        )


if __name__ == "__main__":
    unittest.main()
