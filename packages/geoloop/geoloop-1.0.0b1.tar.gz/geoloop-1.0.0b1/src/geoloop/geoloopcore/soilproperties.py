import numpy as np

from geoloop.configuration import SingleRunConfig
from geoloop.geoloopcore.strat_interpolator import StratInterpolator, TgInterpolator
from geoloop.lithology.process_lithology import ProcessLithologyToThermalConductivity


class SoilProperties:
    """
    Store soil thermal properties, including geotherm (temperature vs. depth)
    and thermal conductivity profiles (depth-dependent or lithology-based).

    Supports:
    - Depth-based interpolation of ground temperature Tg(z)
    - Depth-based or lithology-based interpolation of k_s(z)
    - Scaling of conductivity profiles
    """

    def __init__(
        self,
        Tg: list | float,
        k_s: list | float,
        z_Tg: list = None,
        Tgrad: float = 0.0,
        z_k_s: list = None,
        k_s_scale: float = 1.0,
        lithology_to_k: ProcessLithologyToThermalConductivity = None,
        alfa: float = 1e-6,
    ) -> None:
        """
        Initialize SoilProperties, containing ground temperature and thermal
        conductivity as functions of depth.

        Parameters
        ----------
        Tg : float or list
            Ground temperature(s) used for interpolation.
            - If array-list: temperature at depths specified by `z_Tg`.
            - If float: constant surface temperature for linear gradient computation.
        k_s : float or list
            Thermal conductivity values (W/m·K), possibly depth-dependent.
            If list-like, entries correspond to depths in `z_k_s`.
        z_Tg : list or None, optional
            Depth values (m) corresponding to `Tg` samples.
            If None, temperature is assumed constant or determined by `Tgrad`.
        Tgrad : float, optional
            Vertical geothermal gradient (K/m). Default is 0 (no gradient).
        z_k_s : list or None, optional
            Depth values (m) corresponding to `k_s` samples.
            If None, conductivity is assumed constant at all depths.
        k_s_scale : float, optional
            Scaling factor applied to thermal conductivity profiles (default 1.0).
        lithology_to_k : lithology_to_k or None, optional
            If provided, conductivity is derived from lithology-based profiles
            using the lithology_to_k lookup structure instead of `k_s`/`z_k_s`.
        alfa : float, optional
            Thermal diffusivity of the ground (m²/s). Default is 1e-6.

        Notes
        -----
        - If `lithology_to_k` is provided, the lithology-based thermal conductivity
          profile overrides `k_s` and `z_k_s`.
        - This constructor initializes two interpolators:
            * `interpolatorTg` – for temperature vs. depth
            * `interpolatorKs` – for conductivity vs. depth
        """
        # subsurface temperature and/or geothermal gradient
        self.Tg = Tg
        self.z_Tg = z_Tg
        self.Tgrad = Tgrad
        self.interpolatorTg = TgInterpolator(self.z_Tg, self.Tg, self.Tgrad)

        # subsurface bulk thermal conductivity
        self.k_s = np.asarray(k_s)
        if z_k_s == None:
            self.z_k_s = np.ones_like(k_s)
        else:
            self.z_k_s = np.asarray(z_k_s)
        self.k_s_scale = k_s_scale
        self.lithology_to_k = lithology_to_k

        self.alfa = alfa  # thermal diffusivity

        # interpolate thermal conductivity
        if isinstance(self.lithology_to_k, ProcessLithologyToThermalConductivity):
            # lithology-based thermal conductivity profile
            zstart, zend = self.lithology_to_k.get_start_end_depths()
            zval = self.lithology_to_k.get_thermcon_sample_profile(0).kh_bulk
            self.interpolatorKs = StratInterpolator(zend, zval)
        else:
            self.interpolatorKs = StratInterpolator(
                self.z_k_s, self.k_s, stepvalue=False
            )

    def getTg(self, z: float | np.ndarray) -> float | np.ndarray:
        """Return ground temperature at depth `z`."""
        return self.interpolatorTg.getTg(z)

    def get_k_s(
        self, zstart: np.ndarray, zend: np.ndarray, isample: int = 0
    ) -> np.ndarray:
        """
        Retrieves and interpolates thermal conductivity-depth profile for depth-segments in the simulation, for the basecase
        in a single simulation or for the specified sample in a stochastic simulation.

        Parameters
        ----------
        zstart : np.ndarray
            Array of starting depths of each segment.
        zend : np.ndarray
            Array of ending depths of each segment.
        isample : int, optional
            Index selecting conductivity sample from lithology_to_k (default 0).

        Returns
        -------
        np.ndarray
            Thermal conductivity-depth profile with depth-resolution for the depth-segments in the simulation.
        """
        if isinstance(self.lithology_to_k, ProcessLithologyToThermalConductivity):
            zval = self.lithology_to_k.get_thermcon_sample_profile(isample).kh_bulk
            self.interpolatorKs.zval = zval

        ks = self.interpolatorKs.interp(zstart, zend)
        return ks * self.k_s_scale

    @classmethod
    def from_config(cls, config: SingleRunConfig) -> "SoilProperties":
        """
        Build a SoilProperties object from a configuration object.

        Parameters
        ----------
        config : SingleRunConfig
            Object containing entries including Tg, k_s, stratigraphy, scaling,
            lithology parameters, and diffusivity.

        Returns
        -------
        SoilProperties
        """

        return SoilProperties(
            Tg=config.Tg,
            z_Tg=config.z_Tg,
            Tgrad=config.Tgrad,
            k_s=config.k_s,
            z_k_s=config.z_k_s,
            k_s_scale=config.k_s_scale,
            alfa=config.alfa,
            lithology_to_k=config.lithology_to_k,  # <-- already built upstream
        )
