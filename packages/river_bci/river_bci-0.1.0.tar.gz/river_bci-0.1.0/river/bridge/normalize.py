"""
Normalization methods for neural data.

This module provides various normalization techniques commonly used in
BCI research, including standard z-score, sliding window z-score (Willett/Chang
style), robust z-score, soft normalization, and min-max scaling.

Functions:
    zscore: Standard z-score normalization
    sliding_zscore: Sliding window z-score (30s default, matches BCI papers)
    robust_zscore: Median/MAD based normalization (outlier robust)
    soft_normalize: x / (x + c) normalization
    minmax_scale: Scale to specified range
"""

from __future__ import annotations

from typing import Tuple, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.ndimage import uniform_filter1d


def zscore(
    data: ArrayLike,
    axis: int = 0,
    eps: float = 1e-8,
) -> NDArray[np.floating]:
    """
    Standard z-score normalization.

    Computes (x - mean) / std along the specified axis.

    Parameters
    ----------
    data : array_like
        Input data array. Can be 1D (n_samples,) or 2D (n_samples, n_channels).
    axis : int, optional
        Axis along which to compute mean and std. Default is 0 (normalize
        each channel/column independently).
    eps : float, optional
        Small constant added to std to prevent division by zero.
        Default is 1e-8.

    Returns
    -------
    normalized : ndarray
        Z-scored data with zero mean and unit variance along the specified axis.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.normalize import zscore
    >>> data = np.array([[1, 2], [3, 4], [5, 6]])
    >>> normalized = zscore(data, axis=0)
    >>> np.allclose(normalized.mean(axis=0), 0)
    True
    >>> np.allclose(normalized.std(axis=0), 1, atol=0.1)
    True
    """
    data = np.asarray(data, dtype=np.float64)
    mean = np.mean(data, axis=axis, keepdims=True)
    std = np.std(data, axis=axis, keepdims=True)
    return (data - mean) / (std + eps)


def sliding_zscore(
    data: ArrayLike,
    fs: float,
    window_s: float = 30.0,
    eps: float = 1e-8,
) -> NDArray[np.floating]:
    """
    Sliding window z-score normalization.

    Computes z-score using a sliding window for mean and std estimation.
    This is the standard normalization approach used in Willett and Chang lab
    BCI papers, with a default 30-second window.

    Uses scipy.ndimage.uniform_filter1d for efficient computation.

    Parameters
    ----------
    data : array_like
        Input data array. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    window_s : float, optional
        Window size in seconds. Default is 30.0 (matches BCI paper conventions).
    eps : float, optional
        Small constant added to std to prevent division by zero.
        Default is 1e-8.

    Returns
    -------
    normalized : ndarray
        Z-scored data using sliding window statistics.

    Notes
    -----
    The window is centered at each sample. Edge effects are handled using
    'reflect' mode, which mirrors the data at the boundaries.

    For real-time applications, use streaming.StreamingZScore instead,
    which uses exponential moving average (causal).

    References
    ----------
    Willett, F. R., et al. (2023). A high-performance speech neuroprosthesis.
        Nature, 620(7976), 1031-1036.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.normalize import sliding_zscore
    >>> # Simulate 10 seconds of data at 1000 Hz
    >>> data = np.random.randn(10000, 64) * 10 + 5
    >>> normalized = sliding_zscore(data, fs=1000, window_s=2.0)
    >>> normalized.shape
    (10000, 64)
    """
    data = np.asarray(data, dtype=np.float64)
    window_samples = int(window_s * fs)

    # Ensure odd window size for symmetric filtering
    if window_samples % 2 == 0:
        window_samples += 1

    if data.ndim == 1:
        # 1D case
        mean = uniform_filter1d(data, size=window_samples, mode="reflect")
        # Compute variance using E[X^2] - E[X]^2
        mean_sq = uniform_filter1d(data**2, size=window_samples, mode="reflect")
        var = mean_sq - mean**2
        std = np.sqrt(np.maximum(var, 0))  # Ensure non-negative
        return (data - mean) / (std + eps)
    else:
        # 2D case: apply along axis 0 (time)
        mean = uniform_filter1d(data, size=window_samples, axis=0, mode="reflect")
        mean_sq = uniform_filter1d(data**2, size=window_samples, axis=0, mode="reflect")
        var = mean_sq - mean**2
        std = np.sqrt(np.maximum(var, 0))
        return (data - mean) / (std + eps)


def robust_zscore(
    data: ArrayLike,
    axis: int = 0,
    eps: float = 1e-8,
) -> NDArray[np.floating]:
    """
    Robust z-score using median and median absolute deviation (MAD).

    Computes (x - median) / MAD, which is more robust to outliers than
    standard z-score. The MAD is scaled by 1.4826 to be consistent with
    standard deviation for normal distributions.

    Parameters
    ----------
    data : array_like
        Input data array.
    axis : int, optional
        Axis along which to compute statistics. Default is 0.
    eps : float, optional
        Small constant added to MAD to prevent division by zero.
        Default is 1e-8.

    Returns
    -------
    normalized : ndarray
        Robustly normalized data.

    Notes
    -----
    The scaling factor 1.4826 makes MAD a consistent estimator of standard
    deviation for normally distributed data: MAD * 1.4826 ≈ std.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.normalize import robust_zscore
    >>> # Data with outliers
    >>> data = np.array([1, 2, 3, 100, 4, 5])
    >>> normalized = robust_zscore(data)
    >>> # Outlier (100) will have extreme z-score, but won't affect others much
    """
    data = np.asarray(data, dtype=np.float64)
    median = np.median(data, axis=axis, keepdims=True)
    mad = np.median(np.abs(data - median), axis=axis, keepdims=True)
    # Scale factor for consistency with standard deviation
    mad_scaled = mad * 1.4826
    return (data - median) / (mad_scaled + eps)


def soft_normalize(
    data: ArrayLike,
    norm_constant: float,
) -> NDArray[np.floating]:
    """
    Soft normalization: x / (|x| + c).

    This normalization compresses large values while preserving the sign
    and relative ordering of the data. Output is bounded to (-1, 1).

    Parameters
    ----------
    data : array_like
        Input data array.
    norm_constant : float
        Normalization constant c. Larger values result in less compression.
        Typically set based on the expected magnitude of the data.

    Returns
    -------
    normalized : ndarray
        Soft-normalized data with values in (-1, 1).

    Notes
    -----
    This normalization is useful when you want to preserve the sign of the
    data while bounding the output range. It's less sensitive to outliers
    than z-score normalization.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.normalize import soft_normalize
    >>> data = np.array([-10, -1, 0, 1, 10])
    >>> soft_normalize(data, norm_constant=5)
    array([-0.66666667, -0.16666667,  0.        ,  0.16666667,  0.66666667])
    """
    data = np.asarray(data, dtype=np.float64)
    return data / (np.abs(data) + norm_constant)


def minmax_scale(
    data: ArrayLike,
    feature_range: Tuple[float, float] = (0.0, 1.0),
    axis: int = 0,
) -> NDArray[np.floating]:
    """
    Scale data to a specified range using min-max normalization.

    Transforms data to lie within [min, max] of the feature_range.

    Parameters
    ----------
    data : array_like
        Input data array.
    feature_range : tuple of float, optional
        Desired range of transformed data. Default is (0, 1).
    axis : int, optional
        Axis along which to compute min and max. Default is 0.

    Returns
    -------
    scaled : ndarray
        Scaled data within the specified feature range.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.normalize import minmax_scale
    >>> data = np.array([[1, 2], [3, 4], [5, 6]])
    >>> scaled = minmax_scale(data, feature_range=(0, 1))
    >>> scaled.min(axis=0)
    array([0., 0.])
    >>> scaled.max(axis=0)
    array([1., 1.])
    """
    data = np.asarray(data, dtype=np.float64)
    data_min = np.min(data, axis=axis, keepdims=True)
    data_max = np.max(data, axis=axis, keepdims=True)
    data_range = data_max - data_min

    # Handle constant features (range = 0)
    data_range = np.where(data_range == 0, 1, data_range)

    # Scale to [0, 1]
    scaled = (data - data_min) / data_range

    # Scale to feature_range
    min_val, max_val = feature_range
    return scaled * (max_val - min_val) + min_val
