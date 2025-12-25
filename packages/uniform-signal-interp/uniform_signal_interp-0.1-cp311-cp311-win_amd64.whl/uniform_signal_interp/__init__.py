from .uniform_signal_interp import (
    uniform_signal_linear_interp,
    uniform_signal_linear_vertical_interp_2d,
    uniform_signal_cubic_interp,
)


import numpy as np
from numpy.typing import NDArray
from typing import Optional


def py_uniform_signal_cubic_interp(
    signal: NDArray, x: NDArray, fill_value: Optional[float] = None
) -> NDArray:
    """
    Fast one-dimensional cubic interpolator.

    Parameters
    ----------
    signal : ndarray, real or complex
        The 1-D data that will be interpolated.
        Must be ordered along the interpolation axis
        (i.e. signal[i] is the value at the i-th grid node).

    x : ndarray, real
        Abscissae at which the interpolated values are requested.
        They are expressed in *unit-index* coordinates:
        0.0          → first sample (signal[0])
        1.0          → second sample (signal[1])
        signal_len-1 → last sample (signal[-1])
        Fractional values trigger cubic interpolation; integers simply
        copy the corresponding entry from `signal`.

    fill_value : float or complex, optional
        Value returned for every `x` that falls outside the
        closed interval [0, signal_len-1].
        If `fill_value` is omitted (None) the function *clamps* the
        result to the edge value instead of extrapolating.

    Returns
    -------
    ndarray
        Array with the same shape and dtype as `x` containing the
        interpolated (or clamped/filled) values.

    Notes
    -----
    * Inside the range [1 … signal_len-2] a local cubic polynomial
      fitted to the four neighbouring samples is used.
    * At the two left-most and two right-most samples the function
      falls back to linear interpolation so that no boundary
      information beyond the provided array is required.
    * The implementation is fully vectorised and handles complex
      valued `signal` without extra overhead.

    Examples
    --------
    >>> signal = np.array([1.0, 2.0, 1.5, 3.0, 2.5])
    >>> x_query = np.array([-0.5, 0.5, 1.7, 4.8, 5.2])
    >>> interpol_cubic(signal, x_query, fill_value=np.nan)
    array([ 1.   ,  1.5  ,  1.758,  2.5  ,   nan ])
    """
    signal_x_len = len(signal)

    yout = np.zeros(len(x), dtype=signal.dtype)  # predefine

    # indices outside of the range
    x_idx = x < 0  # maps which index in x it is
    if x_idx.any():
        if fill_value is None:
            yout[x_idx] = signal[0]
        else:
            yout[x_idx] = fill_value
    x_idx = x > (signal_x_len - 1)  # maps which index in x it is
    if x_idx.any():
        if fill_value is None:
            yout[x_idx] = signal[signal_x_len - 1]
        else:
            yout[x_idx] = fill_value

    # indices on the rim: linear interpolation
    x_idx = np.logical_and(x >= 0, x < 1)  # maps which index in x it is
    if x_idx.any():
        _x = x[x_idx]
        yout[x_idx] = (signal[1] - signal[0]) * _x + signal[0]

    x_idx = np.logical_and(
        x >= (signal_x_len - 2), x <= (signal_x_len - 1)
    )  # maps which index in x it is
    if x_idx.any():
        _x = x[x_idx]
        yout[x_idx] = (signal[signal_x_len - 1] - signal[signal_x_len - 2]) * (
            _x - (signal_x_len - 2)
        ) + signal[signal_x_len - 2]

    # indices inside the range: cubic interpolation
    x_idx = np.logical_and(
        x >= 1, x < (signal_x_len - 2)
    )  # maps which index in x it is
    if x_idx.any():
        _x = x[x_idx]  # maps x2 to x index
        _signal_idx = _x.astype(int)  # maps which signal,x to take
        signal_p2 = signal[_signal_idx + 2]
        signal_p1 = signal[_signal_idx + 1]
        signal_p0 = signal[_signal_idx]
        signal_m1 = signal[_signal_idx - 1]
        d = signal_p0
        c = (signal_p1 - signal_m1) / 2.0
        b = (-signal_p2 + 4 * signal_p1 - 5 * signal_p0 + 2 * signal_m1) / 2.0
        a = (signal_p2 - 3 * signal_p1 + 3 * signal_p0 - signal_m1) / 2.0
        xi = _x - _signal_idx
        yout[x_idx] = ((a * xi + b) * xi + c) * xi + d

    return yout


def py_uniform_signal_linear_vertical_interp_2d(
    signal: NDArray, x: float, fill_value=None
):
    """
    Fast linear interpolator.
    Returns the values in in the same way interpol. Can deal with complex input.
    signal shape: [None, None]
    """
    signal_shape = signal.shape
    signal_x_len = signal_shape[0]

    # indices outside of the range
    if x < 0:
        if fill_value is None:
            yout = signal[0]
        else:
            yout = fill_value
    elif x >= (signal_x_len - 1):
        if fill_value is None:
            yout = signal[signal_x_len - 1]
        else:
            yout = fill_value
    else:
        _signal_idx = int(x)  # maps which signal,x to take
        signal_p1 = signal[_signal_idx + 1]
        signal_p0 = signal[_signal_idx]
        yout = (signal_p1 - signal_p0) * (x - _signal_idx) + signal_p0

    return yout


def py_uniform_signal_linear_interp(signal: NDArray, x: NDArray, fill_value=None):
    """
    Fast linear interpolator.
    Returns the values in in the same way interpol. Can deal with complex input.
    ---
    signal shape: [None]
    x shape: [None]
    """
    signal_x_len = len(signal)

    yout = np.zeros(len(x), dtype=signal.dtype)  # predefine

    # indices outside of the range
    x_idx = x < 0  # maps which index in x it is
    if x_idx.any():
        if fill_value is None:
            yout[x_idx] = signal[0]
        else:
            yout[x_idx] = fill_value
    x_idx = x >= (signal_x_len - 1)  # maps which index in x it is
    if x_idx.any():
        if fill_value is None:
            yout[x_idx] = signal[signal_x_len - 1]
        else:
            yout[x_idx] = fill_value

    # linear interpolation
    x_idx = np.logical_and(
        x >= 0, x < (signal_x_len - 1)
    )  # maps which index in x it is
    if x_idx.any():
        _x = x[x_idx]  # maps x2 to x index
        _signal_idx = _x.astype(int)  # maps which signal,x to take
        signal_p1 = signal[_signal_idx + 1]
        signal_p0 = signal[_signal_idx]
        yout[x_idx] = (signal_p1 - signal_p0) * (_x - _signal_idx) + signal_p0

    return yout
