import unittest
from pathlib import Path

import numpy as np
import xarray as xr

from geoloop.configuration import SingleRunConfig, load_nested_config, LithologyConfig, StochasticRunConfig
from geoloop.utils.helpers import (
    save_MCrun_results,
    save_singlerun_results,
)
from geoloop.utils.RunManager import run_models
from geoloop.bin.SingleRunSim import SingleRun
from geoloop.constants import test_dir, tests_input_path
from geoloop.geoloopcore.b2g_ana import B2G_ana
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


class TestB2G_ana(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "b2g_ana_test.json"
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
        self.custom_pipe = self.singlerun.bh_design.customPipe
        self.soil_props = self.singlerun.soil_props
        self.sim_params = self.singlerun.sim_params

        self.sim_params.isample = -1

    def test_B2G_ana_model_run(self):
        """Test for calculation of thermal conductivity-depth profile"""

        b2g_ana = B2G_ana(self.custom_pipe, self.soil_props, self.sim_params)

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
            T_f,
            qzb,
            h_fpipes,
        ) = b2g_ana.runsimulation()

        # Type checks
        self.assertIsInstance(T_f, np.ndarray)
        self.assertIsInstance(T_fi, np.ndarray)
        self.assertIsInstance(z, np.ndarray)

        # Length checks
        self.assertEqual(len(hours), len(Q_b))
        expected_shape = (len(hours), len(z), self.custom_pipe.nPipes)
        self.assertEqual(T_f.shape, expected_shape)

        # No NaNs or Infs
        self.assertFalse(np.isnan(T_f).any())
        self.assertFalse(np.isinf(T_f).any())

        # Expected ranges
        self.assertTrue(np.all(T_f > 9))

        # Monotonicity of depth
        self.assertTrue(np.all(np.diff(z) > 0))

        # Approximate known value (example)
        self.assertAlmostEqual(flowrate[0], 0.24, places=2)

    def test_B2G_ana_save_results(self):
        out_dir = Path(test_dir) / "output" / "b2g_ana_test"
        out_dir.mkdir(parents=True, exist_ok=True)  # creates all missing dirs

        self.runfolder = out_dir.name
        basename = f"{self.runfolder}_{self.config.model_type[0]}_{self.config.run_type[0]}"

        outpath = out_dir / basename  # this will be the file path (without extension)

        self.out = self.singlerun.run(-1)

        save_singlerun_results(self.config, self.out, outpath)

        # Check if output file is created
        output_file = outpath.with_name(outpath.stem + "_SR.h5")
        self.assertTrue(output_file.exists())

        # Load HDF5 using xarray to check groups and variables
        results = xr.open_dataset(output_file, group="results", engine="h5netcdf")
        parameters = xr.open_dataset(output_file, group="parameters", engine="h5netcdf")

        # Check expected variables exist in results group
        self.assertIn("T_b", results)
        self.assertIn("zseg", results)
        self.assertIn("nPipes", results)
        self.assertIn("k_g", results)

        self.assertEqual(parameters["model_type"], "ANALYTICAL")

        # Check at least one parameter is stored
        self.assertTrue(len(parameters.data_vars) > 0)

        # Optional: Check shape of a known dataset
        self.assertEqual(results["time"].shape[0], len(self.out.gethours()))

        results.close()
        parameters.close()


class TestB2G_ana_stochastic(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "b2g_ana_test.json"
        )  # Directory containing this test script

        # Load configuration
        keysneeded = ["variables_config"]
        keysoptional = ["litho_k_param", "loadprofile", "borefield", "flow_data"]
        config_dict = load_nested_config(configfile_path, keysneeded, keysoptional)

        self.config = SingleRunConfig(**config_dict)
        # load configuration for variable parameters
        self.config.variables_config = StochasticRunConfig(**self.config.variables_config)

        # Optional lithology-based thermal conductivity sample generation
        self.config.lithology_to_k = None
        if self.config.litho_k_param:
            lithology_to_k = ProcessLithologyToThermalConductivity.from_config(LithologyConfig(**self.config.litho_k_param))
            lithology_to_k.create_multi_thermcon_profiles()
            self.config.lithology_to_k = lithology_to_k

    def test_B2G_ana_stochastic_model_run_and_saving(self):
        out_dir = Path(test_dir) / "output" / "b2g_ana_test"
        out_dir.mkdir(parents=True, exist_ok=True)  # creates all missing dirs

        self.runfolder = out_dir.name
        basename = (
            self.runfolder
            + "_"
            + self.config.model_type[0]
            + "_"
            + self.config.run_type[0]
        )

        outpath = out_dir / basename  # this will be the file path (without extension)

        parameters, results = run_models(self.config)

        save_MCrun_results(self.config, parameters, results, outpath)

        # Check if output file is created
        output_file = outpath.with_name(outpath.stem + "_MC.h5")
        self.assertTrue(output_file.exists())

        # Load HDF5 using xarray to check groups and variables
        results = xr.open_dataset(output_file, group="results", engine="h5netcdf")
        parameters = xr.open_dataset(output_file, group="parameters", engine="h5netcdf")

        # Check expected variables exist in results group
        self.assertIn("T_b", results)
        self.assertEqual(
            len(parameters["samples"]), len(results["flowrate"].isel(time=0))
        )


if __name__ == "__main__":
    unittest.main()
