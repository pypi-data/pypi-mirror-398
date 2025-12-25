from typing import Union

import numpy as np

ArrayLike = Union[np.ndarray, list, float, int]


class TgInterpolator:
    """
    class to manage interpolation of temperature over depth.
    """

    def __init__(self, z_Tg: ArrayLike | None, Tg: ArrayLike, Tgrad: float) -> None:
        """
        Parameters
        ----------
        z_Tg : array_like or None
            Depth values (m) at which temperature samples in `Tg` are defined.
            If None, `Tg` is treated as a scalar.
        Tg : float or array_like
            Ground temperature value(s).
            - If float: temperature at surface.
            - If array_like: temperature profile at depths `z_Tg`.
        Tgrad : float
            Geothermal gradient (C/m). Used only when `Tg` is scalar.
        """
        self.z_Tg = z_Tg
        self.Tg = Tg
        self.Tgrad = Tgrad

    def interp_Tg(self, z: ArrayLike) -> np.ndarray:
        """
        Interpolate temperature at depth.

        Parameters
        ----------
        z : array_like
            Depth(s) in meters.

        Returns
        -------
        np.ndarray
            Interpolated temperature values.
        """
        return np.interp(z, self.z_Tg, self.Tg)

    def getTg(self, z: ArrayLike) -> ArrayLike:
        """
        Get ground temperature at depth.

        Parameters
        ----------
        z : float or array_like
            Depth(s) in meters.

        Returns
        -------
        float or np.ndarray
            Temperature at depth.

        Notes
        -----
        - If `Tg` is scalar: Tg + Tgrad * 0.01 * z
        - If `Tg` is array: interpolated from depth-temperature profile
        """
        if np.isscalar(self.Tg):
            return self.Tg + self.Tgrad * 0.01 * z
        else:
            return self.interp_Tg(z)


class StratInterpolator:
    """
    class to manage interpolation of soil properties to averaged segment properties.
    """

    def __init__(
        self,
        zcoord: ArrayLike,
        zval: ArrayLike,
        nz: int = 10000,
        stepvalue: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        zcoord : array_like
            Depth coordinates (m) defining the property profile.
        zval : array_like
            Property values corresponding to `zcoord`.
        nz : int, optional
            Number of points for the internal fine-resolution discretization.
        stepvalue : bool, optional
            If True:
                Interpret `zval` as piecewise-constant over intervals
                (stepwise profile).
            If False:
                Use linear interpolation between points.
        """
        self.zcoord = zcoord
        self.zval = zval
        self.nz = nz

        # high-resolution depth array
        self.zp = np.linspace(0, self.zcoord[-1], num=nz)
        self.dz = self.zp[1] - self.zp[0]

        self.stepvalue = stepvalue
        if self.stepvalue:
            self.init_indices()

    @property
    def zval(self) -> np.ndarray:
        return self._zval

    @zval.setter
    def zval(self, value: ArrayLike) -> None:
        self._zval = value

    def init_indices(self) -> None:
        """
        For the high resolution array self.zp get indices on the courser intervalled zcoord array.
        The indices are determined by searchsorted of np, giving the lower index when on interval zlith[0] to zlith[1].
        This is only used if stepvalue=True.
        """
        self.indexl = self.zcoord.searchsorted(self.zp)

    def interp(self, zstart: np.ndarray, zend: np.ndarray) -> np.ndarray:
        """
        Interpolate for zstart, zend arrays of the segments, the average value of zval.
        Compute average property value for each depth segment.

        Parameters
        ----------
        zstart : np.ndarray
            Segment start depths (m).
        zend : np.ndarray
            Segment end depths (m).

        Returns
        -------
        np.ndarray
            Average property value per segment.
        """
        val = zstart * 0.0
        ilstart = max(0, int(zstart[0] / self.dz))
        for i in range(len(zend)):
            valsum = 0
            ilend = min(self.nz, int(round(zend[i] / self.dz)))
            ilrange = max(1, ilend - ilstart)
            if self.stepvalue:
                for il in range(ilrange):
                    valsum += self.zval[self.indexl[il + ilstart]]
                val[i] = valsum / ilrange
            else:
                vals = np.interp(self.zp[ilstart:ilend], self.zcoord, self.zval)
                val[i] = np.sum(vals) / ilrange
            ilstart = min(self.nz - 1, ilend)
        return val

    def interp_plot(self, zstart: np.ndarray, zend: np.ndarray) -> np.ndarray:
        """
        Generate a high-resolution vector of interpolated property values.

        Parameters
        ----------
        zstart : np.ndarray
            Segment start depths (m).
        zend : np.ndarray
            Segment end depths (m).

        Returns
        -------
        np.ndarray
            Interpolated property values along internal grid `zp`.
        """
        val = np.zeros_like(self.zp)
        ilstart = max(0, int(zstart[0] / self.dz))

        for i in range(len(zend)):
            ilend = min(self.nz, int(round(zend[i] / self.dz)))
            if ilend > ilstart:
                if self.stepvalue:
                    val[ilstart:ilend] = self.zval[self.indexl[ilstart]]
                else:
                    vals = np.interp(self.zp[ilstart:ilend], self.zcoord, self.zval)
                    val[ilstart:ilend] = vals
            ilstart = ilend

        # Fill the remaining 0 values with the last used value
        last_nonzero_index = (val != 0).nonzero()[0][-1]
        val[last_nonzero_index + 1 :] = val[last_nonzero_index]

        return val
