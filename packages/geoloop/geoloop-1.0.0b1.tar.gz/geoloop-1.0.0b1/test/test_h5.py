import unittest
from pathlib import Path

import numpy as np
import xarray as xr

from geoloop.configuration import load_nested_config, SingleRunConfig, LithologyConfig
from geoloop.utils.helpers import save_singlerun_results
from geoloop.bin.SingleRunSim import SingleRun
from geoloop.constants import test_dir, tests_input_path
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


class TestH5(unittest.TestCase):
    def setUp(self):
        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "test_h5.json"
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

    def test_from_array(self):
        out_dir = Path(test_dir) / "output" / "h5_test"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Create a simple NumPy array
        data = np.arange(12).reshape(3, 4)

        # Wrap it in an xarray DataArray
        da = xr.DataArray(data, dims=("x", "y"), coords={"x": range(3), "y": range(4)})

        # Convert to Dataset (optional, but recommended for saving)
        ds = da.to_dataset(name="my_data")

        # Save to HDF5 using h5netcdf
        ds.to_netcdf((out_dir / "example_from_numpy.h5"), engine="h5netcdf")

    def test_directly(self):
        out_dir = Path(test_dir) / "output" / "h5_test"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Directly create an xarray DataArray
        da = xr.DataArray(
            [[1, 2, 3], [4, 5, 6]],
            dims=("row", "col"),
            coords={"row": ["r1", "r2"], "col": ["c1", "c2", "c3"]},
        )

        # Convert to Dataset and save
        ds = da.to_dataset(name="my_data")

        ds.to_netcdf((out_dir / "example_direct_xarray.h5"), engine="h5netcdf")

    def test_FINVOL_field(self):
        out_dir = Path(test_dir) / "output" / "h5_test"
        out_dir.mkdir(parents=True, exist_ok=True)

        runfolder = out_dir.name
        basename = (
            f"{runfolder}_{self.config.model_type[0]}_{self.config.run_type[0]}"
        )

        outpath = out_dir / basename  # this will be the file path (without extension)

        self.out = self.singlerun.run(-1)

        save_singlerun_results(self.config, self.out, outpath)
        self.out.save_T_field_FINVOL(outpath)

        output_file = outpath.with_name(outpath.stem + "_FINVOL_T.h5")

        # Check if output file is created
        self.assertTrue(output_file.exists())
