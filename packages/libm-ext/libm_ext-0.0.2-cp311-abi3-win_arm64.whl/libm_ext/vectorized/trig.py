"""
Vectorized trigonometric functions for NumPy arrays.

This module provides vectorized (element-wise) implementations of:

- :func:`sinpi` - Compute sin(πx) for each element
- :func:`cospi` - Compute cos(πx) for each element

These functions automatically switch between serial and parallel execution
based on array size for optimal performance.

Performance
-----------

For small arrays, serial execution avoids threading overhead.
For large arrays, parallel execution using Rayon provides significant speedup.

Supported dtypes
----------------

- ``numpy.float64`` (double precision)
- ``numpy.float32`` (single precision)
"""

from libm_ext import _core
import numpy as np
import numpy.typing as npt


def _sinpi_serial(x: npt.NDArray) -> npt.NDArray:
    """
    Vectorized sinpi using serial mode (single-threaded).

    Parameters
    ----------
    x : ndarray
        Input array of float32 or float64.

    Returns
    -------
    ndarray
        Element-wise sin(πx).
    """
    if x.dtype == np.float64:
        return _core.sinpi_vectorized_serial(x)
    elif x.dtype == np.float32:
        return _core.sinpif_vectorized_serial(x)
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")


def _sinpi_parallel(x: npt.NDArray) -> npt.NDArray:
    """
    Vectorized sinpi using parallel mode (multi-threaded via Rayon).

    Parameters
    ----------
    x : ndarray
        Input array of float32 or float64.

    Returns
    -------
    ndarray
        Element-wise sin(πx).
    """
    if x.dtype == np.float64:
        return _core.sinpi_vectorized_parallel(x)
    elif x.dtype == np.float32:
        return _core.sinpif_vectorized_parallel(x)
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")


def sinpi(x: npt.NDArray, threshold: int = 16000) -> npt.NDArray:
    r"""
    Compute sin(πx) element-wise for a NumPy array.

    This function automatically switches between serial and parallel execution
    based on array size for optimal performance.

    Parameters
    ----------
    x : ndarray
        Input array. Must be float32 or float64.
    threshold : int, default=10000
        Array size threshold for switching to parallel execution.
        Arrays smaller than this use serial execution.

    Returns
    -------
    ndarray
        Element-wise sin(πx) with the same shape and dtype as input.

    Raises
    ------
    ValueError
        If dtype of x is not float32 or float64.

    Algorithm
    ---------

    Uses the same high-precision algorithm as :func:`libm_ext.sinpi`:

    1. **Argument reduction**: Reduce x to [-1/4, 1/4] using n = round(2|x|)
    2. **Polynomial evaluation**: Minimax polynomial with double-double arithmetic
    3. **Sign adjustment**: Apply quadrant-based sign correction

    See :func:`libm_ext.sinpi` for detailed algorithm description.

    Examples
    --------
    >>> import numpy as np
    >>> from libm_ext.vectorized import sinpi
    >>> x = np.array([0.0, 0.5, 1.0, 1.5])
    >>> sinpi(x)
    array([ 0.,  1.,  0., -1.])

    >>> # Works with float32 too
    >>> x32 = np.array([0.0, 0.25, 0.5], dtype=np.float32)
    >>> sinpi(x32)  # doctest: +ELLIPSIS
    array([0.   , 0.707..., 1.   ], dtype=float32)

    See Also
    --------
    cospi : Vectorized cos(πx)
    libm_ext.sinpi : Scalar version
    """
    if x.size < threshold:
        return _sinpi_serial(x)
    else:
        return _sinpi_parallel(x)


def _cospi_serial(x: npt.NDArray) -> npt.NDArray:
    """
    Vectorized cospi using serial mode (single-threaded).

    Parameters
    ----------
    x : ndarray
        Input array of float32 or float64.

    Returns
    -------
    ndarray
        Element-wise cos(πx).
    """
    if x.dtype == np.float64:
        return _core.cospi_vectorized_serial(x)
    elif x.dtype == np.float32:
        return _core.cospif_vectorized_serial(x)
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")


def _cospi_parallel(x: npt.NDArray) -> npt.NDArray:
    """
    Vectorized cospi using parallel mode (multi-threaded via Rayon).

    Parameters
    ----------
    x : ndarray
        Input array of float32 or float64.

    Returns
    -------
    ndarray
        Element-wise cos(πx).
    """
    if x.dtype == np.float64:
        return _core.cospi_vectorized_parallel(x)
    elif x.dtype == np.float32:
        return _core.cospif_vectorized_parallel(x)
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")


def cospi(x: npt.NDArray, threshold: int = 16000) -> npt.NDArray:
    r"""
    Compute cos(πx) element-wise for a NumPy array.

    This function automatically switches between serial and parallel execution
    based on array size for optimal performance.

    Parameters
    ----------
    x : ndarray
        Input array. Must be float32 or float64.
    threshold : int, default=16000
        Array size threshold for switching to parallel execution.
        Arrays smaller than this use serial execution.

    Returns
    -------
    ndarray
        Element-wise cos(πx) with the same shape and dtype as input.

    Raises
    ------
    ValueError
        If dtype of x is not float32 or float64.

    Algorithm
    ---------

    Uses the same high-precision algorithm as :func:`libm_ext.cospi`:

    1. **Argument reduction**: Reduce x to [-1/4, 1/4] using n = round(2|x|)
    2. **Polynomial evaluation**: Minimax polynomial with double-double arithmetic
    3. **Sign adjustment**: Apply quadrant-based sign correction

    See :func:`libm_ext.cospi` for detailed algorithm description.

    Examples
    --------
    >>> import numpy as np
    >>> from libm_ext.vectorized import cospi
    >>> x = np.array([0.0, 0.5, 1.0, 2.0])
    >>> cospi(x)
    array([ 1.,  0., -1.,  1.])

    >>> # Works with float32 too
    >>> x32 = np.array([0.0, 0.25, 0.5], dtype=np.float32)
    >>> cospi(x32)  # doctest: +ELLIPSIS
    array([1.   , 0.707..., 0.   ], dtype=float32)

    See Also
    --------
    sinpi : Vectorized sin(πx)
    libm_ext.cospi : Scalar version
    """
    if x.size < threshold:
        return _cospi_serial(x)
    else:
        return _cospi_parallel(x)


if __name__ == "__main__":
    from libm_ext.vectorized.utils import bench

    x = np.random.standard_normal(16000)
    bench("sinpi-serial", lambda: _sinpi_serial(x))
    bench("sinpi-parallel", lambda: _sinpi_parallel(x))
