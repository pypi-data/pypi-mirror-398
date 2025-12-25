import sys
from pathlib import Path

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
from matplotlib.colors import to_hex, to_rgb

from geoloop.constants import lithology_colors, lithology_names_english
from geoloop.geoloopcore.strat_interpolator import StratInterpolator


def mix_hex_colors(colors: list[str], fractions: list[float]) -> str:
    """
    Combine multiple hex colors using given fractional weights.

    Parameters
    ----------
    colors : list of str
        Hex color strings (e.g. '#aabbcc').
    fractions : list of float
        Fractions for each color. Typically sums to 1. Values may be 0..1.

    Returns
    -------
    str
        Resulting mixed color as a hex string.
    """
    mixed_color = np.zeros(3)
    for color, fraction in zip(colors, fractions):
        mixed_color += np.array(to_rgb(color)) * fraction
    return to_hex(mixed_color)


def plot_lithology_and_thermcon(
    litho_ds: xr.Dataset,
    kx_plotting_base: np.ndarray,
    interp_obj: StratInterpolator,
    kx_plotting_max: np.ndarray,
    kx_plotting_min: np.ndarray,
    litho_h5path: str | Path,
    out_dir: Path,
) -> None:
    """
    Create and save a combined lithology "layer-cake" plot with thermal
    conductivity profiles plotted alongside.

    The main panel shows lithology as vertically stacked colored bands
    (mixed color when two lithologies are present). A narrow side panel
    shows horizontally stacked bars for lithology fractions. Thermal
    conductivity curves are plotted on a twin x-axis (using the internal
    grid from the StratInterpolator).

    Parameters
    ----------
    litho_ds : xarray.Dataset
        Dataset containing fields `depth`, lithology type a `lithology_a`, lithology type b `lithology_b`,
        and the fraction of type a `lithology_a_fraction`.
    kx_plotting_base : np.ndarray
        Fine-grid, interpolated base-case thermal conductivity values (aligned with interp_obj.zp).
    interp_obj : StratInterpolator
        Interpolator object; used for the internal z-grid (zp) and interpolation.
    kx_plotting_max : np.ndarray
        Fine-grid, interpolated maximum thermal conductivity values.
    kx_plotting_min : np.ndarray
        Fine-grid, interpolated minimum thermal conductivity values.
    litho_h5path : str | Path
        Path to the source lithology .h5 file (used to build output filename).
    out_dir : Path
        Directory where the figure will be written.

    Returns
    -------
    None

    """
    plt.rcParams.update({"font.size": 14})

    # Create main + side axes: wide main column + narrow side bar
    fig, (ax_main, ax_side) = plt.subplots(
        1, 2, figsize=(8, 8), gridspec_kw={"width_ratios": [4, 0.8]}
    )

    # Prepare lists for plotting
    current_depth = 0
    depths = []
    fractions_a = []
    fractions_b = []
    colors_main = []

    # Build mixed colors and fraction lists
    for i in range(len(litho_ds["depth"])):
        # depth value for this layer (end depth)
        depth = litho_ds["depth"].values[i]

        lithology_a = litho_ds["lithology_a"].isel(depth=i).item()
        lithology_b = litho_ds["lithology_b"].isel(depth=i).item()
        fraction_a = litho_ds["lithology_a_fraction"].isel(depth=i).item()
        fraction_b = 1 - fraction_a

        # Prepare data for the side plot
        depths.append((current_depth + depth) / 2)  # Center of the bar
        fractions_a.append(fraction_a)
        fractions_b.append(fraction_b)

        # Prepare data for the main plot
        mixed_color = mix_hex_colors(
            [lithology_colors[lithology_a], lithology_colors[lithology_b]],
            [fraction_a, fraction_b],
        )
        colors_main.append(mixed_color)

        current_depth = depth

    # Plot the main lithology column with mixed colors
    for i in range(len(litho_ds["depth"])):
        depth_start = litho_ds["depth"].values[i - 1] if i > 0 else 0
        depth_end = litho_ds["depth"].values[i]
        ax_main.fill_betweenx(
            [depth_start, depth_end], 0, 1, color=colors_main[i], edgecolor=None
        )

    # Adjust axis limits to cover all the plotted data
    ax_main.set_xlim(0, 1)  # Set x-axis to range from 0 to 1 for consistency
    ax_main.set_ylim(
        min(litho_ds["depth"].values), max(litho_ds["depth"].values)
    )  # Make sure the depth range covers all data

    # Calculate depth ranges
    depth_ranges = [
        (litho_ds["depth"].values[i - 1] if i > 0 else 0, litho_ds["depth"].values[i])
        for i in range(len(litho_ds["depth"]))
    ]

    # Create the side plot (horizontally stacked bars for fractions)
    for i, (depth_start, depth_end) in enumerate(depth_ranges):
        bar_height = depth_end - depth_start
        # Left segment (fraction A)
        ax_side.barh(
            y=depth_start,  # Start of the depth range
            width=fractions_a[i],
            height=bar_height,
            color=lithology_colors[litho_ds["lithology_a"].isel(depth=i).item()],
            align="edge",
        )
        # Right segment (fraction B), stacked by using left=fraction_a
        ax_side.barh(
            y=depth_start,  # Start of the depth range
            width=fractions_b[i],
            height=bar_height,
            left=fractions_a[i],
            color=lithology_colors[litho_ds["lithology_b"].isel(depth=i).item()],
            align="edge",
        )

    # Style the side axis
    ax_side.set_xlabel("Lithology fractions")
    ax_side.set_xlim(0, 1)
    ax_side.set_xticks([0, 0.5, 1])
    ax_side.set_xticklabels(["0", "0.5", "1.0"])
    ax_side.set_ylim(ax_main.get_ylim())  # Align y-axes
    ax_side.invert_yaxis()

    # Remove y-axis ticks and labels
    ax_side.set_yticks([])  # Remove ticks
    ax_side.set_yticklabels([])  # Remove labels

    # Spines visibility
    ax_side.spines["top"].set_visible(True)
    ax_side.spines["right"].set_visible(True)
    ax_side.spines["bottom"].set_visible(True)
    ax_side.spines["left"].set_visible(True)

    # Plot thermal conductivity on a secondary x-axis for the main plot
    ax_main.set_xticks([])
    ax_main.set_ylabel("Depth [m]")
    ax_kx = ax_main.twiny()
    ax_kx.plot(
        kx_plotting_base, interp_obj.zp, color="black", linestyle="-", label="Basecase"
    )
    ax_kx.plot(kx_plotting_max, interp_obj.zp, color="blue", linestyle=":", label="Max")
    ax_kx.plot(kx_plotting_min, interp_obj.zp, color="blue", linestyle=":", label="Min")
    ax_kx.set_xlabel("Thermal Conductivity [W/mk]")
    ax_kx.invert_yaxis()
    ax_kx.legend(bbox_to_anchor=(0.5, -0.01), title="Thermal Conductivity")

    # Create legend for lithologies
    handles = []
    labels = []
    used_lithologies = set(litho_ds["lithology_a"].values) | set(
        litho_ds["lithology_b"].values
    )
    for lithology_type in used_lithologies:
        english_name = lithology_names_english.get(lithology_type, lithology_type)
        handles.append(
            plt.Rectangle((0, 0), 1, 1, color=lithology_colors[lithology_type])
        )
        labels.append(lithology_type)
    ax_main.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.9, -0.01),
        title="Lithology",
    )

    plt.tight_layout()

    # Save the figure
    h5_file_name = Path(litho_h5path).name
    fig_name = Path(h5_file_name).stem
    fig_path = out_dir / fig_name

    plt.savefig(fig_path)


def main_Plot_lithology(litho_h5_path: str) -> None:
    """
    Main function to load data, process thermal conductivity profiles, and generate lithology plots.

    Parameters
    ----------
    litho_h5_path : str
        Path to the .h5 file containing the dataset of subsurface properties.

    Returns
    --------
    None

    """
    base_dir = Path(litho_h5_path).parent

    # Open dataset (group 'litho_k' expected)
    litho_k_ds = xr.open_dataset(litho_h5_path, group="litho_k", engine="netcdf4")

    # select only basecase, sample 0
    litho_k_ds_base = litho_k_ds.sel(n_samples=0)

    z = litho_k_ds_base.depth.values
    zval = litho_k_ds_base.kx.values

    zend = z
    zstart = z[:-1] * 1

    # Append 0 at the beginning of zstart (so first segment starts at 0)
    zstart = np.insert(zstart, 0, 0)

    # Build interpolator & compute fine-grid, interpolated conductivity profiles
    interp_obj = StratInterpolator(zend, zval)

    # Interpolate basecase thermal conductivity values
    kx_plotting_base = interp_obj.interp_plot(zstart, zend)

    # Calculate max and min thermal conductivity profiles and interpolate
    kx_max = litho_k_ds.kx.max(dim="n_samples").values
    interp_obj.zval = kx_max
    kx_plotting_max = interp_obj.interp_plot(zstart, zend)

    kx_min = litho_k_ds.kx.min(dim="n_samples").values
    interp_obj.zval = kx_min
    kx_plotting_min = interp_obj.interp_plot(zstart, zend)

    # Create the layer cake plot
    plot_lithology_and_thermcon(
        litho_k_ds_base,
        kx_plotting_base,
        interp_obj,
        kx_plotting_max,
        kx_plotting_min,
        litho_h5_path,
        base_dir,
    )


if __name__ == "__main__":
    litho_h5_path = sys.argv[1]
    main_Plot_lithology(litho_h5_path)
