import unittest
from pathlib import Path

import numpy as np
import xarray as xr

from geoloop.configuration import load_nested_config, SingleRunConfig, LithologyConfig
from geoloop.utils.helpers import save_singlerun_results
from geoloop.bin.SingleRunSim import SingleRun
from geoloop.constants import test_dir, tests_input_path
from geoloop.geoloopcore.pyg_ana import PYG_ana
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


class TestPYG_ana(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "pyg_ana_test.json"
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
        self.cp = self.singlerun.bh_design.customPipe
        self.sp = self.singlerun.soil_props
        self.op = self.singlerun.sim_params

        self.op.isample = -1

    def test_PYG_ana_model_run(self):
        """Test for calculation of thermal conductivity-depth profile"""

        pyg_ana = PYG_ana(self.cp, self.sp, self.op)

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
        ) = pyg_ana.runsimulation()

        # Type checks
        self.assertIsInstance(T_f, np.ndarray)
        self.assertIsInstance(T_fi, np.ndarray)
        self.assertIsInstance(z, np.ndarray)

        # Length checks
        self.assertEqual(len(hours), len(Q_b))
        expected_shape = (len(hours), len(z), self.cp.nPipes)
        self.assertEqual(T_f.shape, expected_shape)

        # No NaNs or Infs
        self.assertFalse(np.isnan(T_f).any())
        self.assertFalse(np.isinf(T_f).any())

        # Expected ranges
        self.assertTrue(np.all(T_f > 4))

        # Monotonicity of depth
        self.assertTrue(np.all(np.diff(z) > 0))

        # Approximate known value (example)
        self.assertAlmostEqual(flowrate[0], 0.24, places=2)

    def test_PYG_ana_save_results(self):
        out_dir = Path(test_dir) / "output" / "pyg_ana_test"
        out_dir.mkdir(parents=True, exist_ok=True)  # creates all missing dirs

        runfolder = out_dir.name
        basename = (
            f"{runfolder}_{self.config.model_type[0]}_{self.config.run_type[0]}"
        )

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

        self.assertEqual(parameters["model_type"], "PYG")

        # Check at least one parameter is stored
        self.assertTrue(len(parameters.data_vars) > 0)

        # Optional: Check shape of a known dataset
        self.assertEqual(results["time"].shape[0], len(self.out.gethours()))

        results.close()
        parameters.close()


if __name__ == "__main__":
    unittest.main()
