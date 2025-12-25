import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg") # Non-GUI backend
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from geoloop.configuration import PlotInputConfig, load_single_config
from geoloop.bin.Plotmain import DataSelection, DataTotal, PlotInput
from geoloop.constants import test_dir, tests_input_path
from geoloop.plotting.create_plots import PlotResults


class TestPlotInput(unittest.TestCase):
    def test_loading_results_from_sim(self):
        """Test for loading of object for simulation results."""

        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "test_plot_results.json"
        )  # Directory containing this test script

        # Load the configuration
        config_dict = load_single_config(configfile_path)
        config = PlotInputConfig(**config_dict)

        plotinput = PlotInput.from_config(config)

        plotinput.list_filenames()
        param_ds, results_ds = plotinput.load_params_result_data()

        self.assertEqual(
            len(param_ds[0].keys()) + len(results_ds[0].keys()),
            50,
            "The combined keys of parameters and results should total 50.",
        )

    def test_loading_Tfield_from_numerical_sim(self):
        """Test for loading temperature field from numerical simulation results."""

        # Construct the relative path for the config file
        configfile_path = (
            tests_input_path / "test_plot_temperature_field.json"
        )  # Directory containing this test script

        config_dict = load_single_config(configfile_path)
        config = PlotInputConfig(**config_dict)
        plotinput = PlotInput.from_config(config)
        temperature_field_da = plotinput.load_temperature_field_data()

        self.assertIsInstance(
            temperature_field_da[0],
            xr.DataArray,
            "Expected an xarray DataArray object.",
        )
        self.assertEqual(
            temperature_field_da[0].shape,
            (88, 21, 8, 1),
            "Unexpected shape for temperature field data.",
        )
        self.assertFalse(
            np.isnan(temperature_field_da[0].values).all(),
            "Temperature field should not be completely NaN.",
        )


class TestDataSelection(unittest.TestCase):
    def setUp(self):
        """Set up with real data for test of data selection process for plotting, or skip if unavailable."""

        # Construct the path for the config file
        configfile_path = (
            tests_input_path / "test_plot_results.json"
        )  # Directory containing this test script

        # Construct path for output of figures
        self.out_path = test_dir / "output"

        if configfile_path.exists():
            config_dict = load_single_config(configfile_path)
            config = PlotInputConfig(**config_dict)
            self.plotinput = PlotInput.from_config(config)
            self.plotinput.list_filenames()
            param_ds, results_ds = self.plotinput.load_params_result_data()

            temperature_field_da = None

            self.datatotal = DataTotal(results_ds, param_ds, temperature_field_da)

            dataselection = DataSelection.select_sub_datasets(
                self.plotinput, self.datatotal
            )
            self.dataselection = dataselection

        else:
            self.skipTest("Configuration file not found. Skipping real data test.")

    def test_select_sub_datasets(self):
        """Test selecting and aggregating subsets of datasets."""

        # Verify list structures
        self.assertIsInstance(self.dataselection.crossplot_params_df, list)
        self.assertIsInstance(self.dataselection.crossplot_results_df, list)
        self.assertIsInstance(self.dataselection.depthplot_params_ds, list)

        # Verify the DataFrame content for cross-plot parameters
        self.assertGreater(
            len(self.dataselection.crossplot_params_df),
            0,
            "crossplot_params_df should contain data.",
        )
        self.assertEqual(
            self.dataselection.crossplot_params_df[0].iloc[0]["H"],
            "300",
            "Expected specific parameter value.",
        )

        # Verify sample dimension integrity
        self.assertIn(
            "samples",
            self.dataselection.crossplot_results_df[0].columns,
            "Expected 'samples' in crossplot_results_df DataFrame columns.",
        )

        # Verify time plot DataFrame contains the expected time dimension and content
        self.assertGreater(
            len(self.dataselection.timeplot_results_df),
            0,
            "timeplot_results_df should contain data.",
        )
        self.assertIn(
            "time",
            self.dataselection.timeplot_results_df[0].columns,
            "Expected 'time' in timeplot_results_df columns.",
        )

    @patch("matplotlib.pyplot.savefig")
    def test_create_scatterplots(self, mock_savefig):
        """Test cross-plot creation without saving files."""

        PlotResults.create_scatterplots(
            self.dataselection.crossplot_results_df[0],
            self.dataselection.crossplot_params_df[0],
            y_variable="Q_b",
            out_path=self.out_path,
        )
        self.assertTrue(mock_savefig.called)

        plt.close("all")

    def test_create_scatterplots_value_error(self):
        """Test scatter plot raises ValueError for missing y_variable."""

        with self.assertRaises(ValueError):
            PlotResults.create_scatterplots(
                self.dataselection.crossplot_results_df[0],
                self.dataselection.crossplot_params_df[0],
                y_variable="nonexistent",
                out_path=self.out_path,
            )
        plt.close("all")

    @patch("matplotlib.pyplot.savefig")
    def test_create_timeseriesplot(self, mock_savefig):
        """Test time-series plot creation without saving files."""

        PlotResults.create_timeseriesplot(
            self.dataselection.timeplot_results_df[0],
            self.out_path,
            self.plotinput.plot_time_parameters,
        )
        # Ensure savefig was called
        mock_savefig.assert_called()
        plt.close("all")

    @patch("matplotlib.pyplot.savefig")
    def test_create_depthplot(self, mock_savefig):
        """Test depth-plot creation without saving files."""

        out_path = (
            self.plotinput.base_dir
            / self.plotinput.run_names[0]
            / self.plotinput.file_names[0]
        )

        PlotResults.create_depthplot(
            self.plotinput.plot_depth_parameters,
            self.plotinput.plot_times,
            self.dataselection.depthplot_params_ds[0],
            self.dataselection.depthplot_results_ds[0],
            out_path,
        )
        # Ensure savefig was called
        mock_savefig.assert_called()
        plt.close("all")


if __name__ == "__main__":
    unittest.main()
