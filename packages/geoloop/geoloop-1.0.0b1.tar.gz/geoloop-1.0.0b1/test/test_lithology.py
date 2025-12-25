import unittest

import xarray as xr

from geoloop.constants import tests_input_path, test_output_path
from geoloop.configuration import LithologyConfig, load_single_config
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


class TestThermalConductivityCalculation(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "test_lithology_k_sand_clay.json"
        )  # Directory containing this test script

        # Load and validate config
        config_dict = load_single_config(configfile_path)
        self.config = LithologyConfig(**config_dict)  # validated Pydantic object

        # set outdir for saving the results correctly
        self.config.out_dir_lithology = test_output_path

        # initiate object for lithology_to_k simulation
        self.lithology_to_k = ProcessLithologyToThermalConductivity.from_config(
            self.config
        )

    def test_single_thermcon_sample_creation(self):
        """Test for calculation of thermal conductivity-depth profile"""

        # Create thermal conductivity-depth profile for the basecase scenario
        k_calc_results = self.lithology_to_k.create_single_thermcon_profile(0)

        self.assertEqual(
            k_calc_results.kh_bulk.min(), 1.7429285646340533
        )  # add assertion here

        # Create thermal conductivity-depth profile for the amount of samples specified in the configuration file
        self.lithology_to_k.create_multi_thermcon_profiles()

        self.assertEqual(
            len(self.lithology_to_k.kh_bulk_results), 500
        )  # add assertion here

        self.lithology_to_k.save_thermcon_sample_profiles()

        out_path = self.lithology_to_k.out_dir / self.lithology_to_k.out_table

        self.assertTrue(out_path.exists())

        Dataset = xr.open_dataset(out_path, group="litho_k", engine="h5netcdf")

        self.assertTrue(
            all(
                var in Dataset
                for var in [
                    "depth",
                    "lithology_a_fraction",
                    "lithology_a",
                    "lithology_b",
                    "n_samples",
                    "kh_bulk",
                    "phi",
                ]
            ),
            "Not all expected variables are present in the dataset",
        )


if __name__ == "__main__":
    unittest.main()
