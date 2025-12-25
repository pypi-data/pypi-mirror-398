"""
Spike train processing for BCI research.

This module provides functions for processing spike trains, including binning,
smoothing, threshold crossing detection, and spike band power extraction.

Default parameters match Willett lab conventions:
- 20ms bins
- -4.5 RMS threshold for threshold crossings
- 50ms Gaussian smoothing

Functions:
    bin_spikes: Single spike train to binned counts/rates
    bin_spike_trains: Multiple units to (n_bins, n_units) array
    smooth_rates: Gaussian smoothing of firing rates
    threshold_crossings: Detect threshold crossings (no spike sorting)
    spike_band_power: Extract spike band power feature
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, filtfilt, sosfilt, sosfiltfilt


SpikeTrains = Dict[Union[int, str], ArrayLike]


def bin_spikes(
    spike_times: ArrayLike,
    bin_size_ms: float = 20.0,
    t_start: Optional[float] = None,
    t_stop: Optional[float] = None,
    output: Literal["count", "rate"] = "rate",
) -> NDArray[np.floating]:
    """
    Bin a single spike train into counts or firing rates.

    Parameters
    ----------
    spike_times : array_like
        Array of spike times in seconds.
    bin_size_ms : float, optional
        Bin size in milliseconds. Default is 20.0 (Willett lab standard).
    t_start : float, optional
        Start time in seconds. If None, uses min(spike_times).
    t_stop : float, optional
        Stop time in seconds. If None, uses max(spike_times).
    output : {'count', 'rate'}, optional
        Output type. 'count' returns spike counts per bin,
        'rate' returns firing rate in Hz. Default is 'rate'.

    Returns
    -------
    binned : ndarray
        Binned spike counts or rates. Shape (n_bins,).

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.spikes import bin_spikes
    >>> spike_times = np.array([0.1, 0.15, 0.3, 0.5, 0.8])
    >>> rates = bin_spikes(spike_times, bin_size_ms=100, t_start=0, t_stop=1)
    >>> rates.shape
    (10,)
    """
    spike_times = np.asarray(spike_times, dtype=np.float64)

    if len(spike_times) == 0:
        if t_start is None or t_stop is None:
            return np.array([], dtype=np.float64)
        n_bins = int(np.ceil((t_stop - t_start) / (bin_size_ms / 1000.0)))
        return np.zeros(n_bins, dtype=np.float64)

    if t_start is None:
        t_start = spike_times.min()
    if t_stop is None:
        t_stop = spike_times.max()

    bin_size_s = bin_size_ms / 1000.0
    n_bins = int(np.ceil((t_stop - t_start) / bin_size_s))
    bin_edges = np.linspace(t_start, t_start + n_bins * bin_size_s, n_bins + 1)

    counts, _ = np.histogram(spike_times, bins=bin_edges)
    counts = counts.astype(np.float64)

    if output == "count":
        return counts
    elif output == "rate":
        return counts / bin_size_s
    else:
        raise ValueError(f"output must be 'count' or 'rate', got {output!r}")


def bin_spike_trains(
    spike_trains: SpikeTrains,
    bin_size_ms: float = 20.0,
    t_start: Optional[float] = None,
    t_stop: Optional[float] = None,
    output: Literal["count", "rate"] = "rate",
) -> NDArray[np.floating]:
    """
    Bin multiple spike trains into a (n_bins, n_units) array.

    Parameters
    ----------
    spike_trains : dict
        Dictionary mapping unit IDs to spike time arrays (in seconds).
        Keys can be integers or strings.
    bin_size_ms : float, optional
        Bin size in milliseconds. Default is 20.0 (Willett lab standard).
    t_start : float, optional
        Start time in seconds. If None, uses min of all spike times.
    t_stop : float, optional
        Stop time in seconds. If None, uses max of all spike times.
    output : {'count', 'rate'}, optional
        Output type. Default is 'rate'.

    Returns
    -------
    binned : ndarray
        Binned spike data. Shape (n_bins, n_units).
        Units are ordered by sorted keys.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.spikes import bin_spike_trains
    >>> spike_trains = {
    ...     0: np.array([0.1, 0.2, 0.5]),
    ...     1: np.array([0.15, 0.3, 0.7]),
    ... }
    >>> rates = bin_spike_trains(spike_trains, bin_size_ms=100, t_start=0, t_stop=1)
    >>> rates.shape
    (10, 2)
    """
    if not spike_trains:
        raise ValueError("spike_trains must not be empty")

    # Determine time range
    if t_start is None or t_stop is None:
        all_times = []
        for times in spike_trains.values():
            times = np.asarray(times)
            if len(times) > 0:
                all_times.extend([times.min(), times.max()])
        if not all_times:
            raise ValueError("All spike trains are empty and t_start/t_stop not specified")
        if t_start is None:
            t_start = min(all_times)
        if t_stop is None:
            t_stop = max(all_times)

    # Sort unit IDs for consistent ordering
    sorted_units = sorted(spike_trains.keys())
    n_units = len(sorted_units)

    # Bin each unit
    binned_list = []
    for unit_id in sorted_units:
        binned = bin_spikes(
            spike_trains[unit_id],
            bin_size_ms=bin_size_ms,
            t_start=t_start,
            t_stop=t_stop,
            output=output,
        )
        binned_list.append(binned)

    return np.column_stack(binned_list)


def smooth_rates(
    rates: ArrayLike,
    sigma_ms: float = 50.0,
    bin_size_ms: float = 20.0,
    causal: bool = False,
    axis: int = 0,
) -> NDArray[np.floating]:
    """
    Gaussian smoothing of firing rates.

    Parameters
    ----------
    rates : array_like
        Firing rates array. Shape (n_bins,) or (n_bins, n_units).
    sigma_ms : float, optional
        Standard deviation of Gaussian kernel in milliseconds.
        Default is 50.0 (Willett lab standard).
    bin_size_ms : float, optional
        Bin size in milliseconds (to convert sigma to bins).
        Default is 20.0.
    causal : bool, optional
        If True, use causal (half-Gaussian) smoothing for real-time
        applications. If False, use symmetric Gaussian. Default is False.
    axis : int, optional
        Axis along which to smooth. Default is 0 (time axis).

    Returns
    -------
    smoothed : ndarray
        Smoothed firing rates with same shape as input.

    Notes
    -----
    For causal smoothing, we use an exponential kernel that approximates
    a half-Gaussian. This is suitable for real-time applications.

    For streaming/real-time applications, consider using
    streaming.StreamingSmooth instead.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.spikes import smooth_rates
    >>> rates = np.random.poisson(10, size=(100, 64)).astype(float)
    >>> smoothed = smooth_rates(rates, sigma_ms=50, bin_size_ms=20)
    >>> smoothed.shape
    (100, 64)
    """
    rates = np.asarray(rates, dtype=np.float64)
    sigma_bins = sigma_ms / bin_size_ms

    if causal:
        # Causal smoothing using exponential kernel
        # Exponential decay approximates half-Gaussian
        alpha = 1.0 / sigma_bins
        n_samples = rates.shape[axis]

        # Create output array
        smoothed = np.zeros_like(rates)

        # Apply exponential moving average
        if rates.ndim == 1:
            smoothed[0] = rates[0]
            for i in range(1, n_samples):
                smoothed[i] = alpha * rates[i] + (1 - alpha) * smoothed[i - 1]
        else:
            # Handle multi-dimensional case
            # Move axis to first position for easier iteration
            rates_t = np.moveaxis(rates, axis, 0)
            smoothed_t = np.zeros_like(rates_t)
            smoothed_t[0] = rates_t[0]
            for i in range(1, n_samples):
                smoothed_t[i] = alpha * rates_t[i] + (1 - alpha) * smoothed_t[i - 1]
            smoothed = np.moveaxis(smoothed_t, 0, axis)

        return smoothed
    else:
        # Non-causal (symmetric) Gaussian smoothing
        return gaussian_filter1d(rates, sigma=sigma_bins, axis=axis, mode="reflect")


def threshold_crossings(
    signal: ArrayLike,
    fs: float,
    threshold_rms: float = -4.5,
    refractory_ms: float = 1.0,
) -> NDArray[np.floating]:
    """
    Detect threshold crossings for spike-like events.

    This implements Willett-style threshold crossing detection without
    spike sorting. Useful for intracortical recordings where precise
    spike sorting is not required.

    Parameters
    ----------
    signal : array_like
        Raw neural signal. Shape (n_samples,) for single channel or
        (n_samples, n_channels) for multiple channels.
    fs : float
        Sampling frequency in Hz.
    threshold_rms : float, optional
        Threshold in units of RMS. Negative values detect negative-going
        crossings (typical for extracellular recordings).
        Default is -4.5 (Willett lab standard).
    refractory_ms : float, optional
        Refractory period in milliseconds. Crossings within this period
        after a detected crossing are ignored. Default is 1.0 ms.

    Returns
    -------
    crossings : ndarray
        For single channel: array of crossing times in seconds.
        For multiple channels: list of arrays, one per channel.

    Notes
    -----
    The threshold is computed as threshold_rms * RMS(signal) for each channel.
    The RMS is computed over the entire signal.

    References
    ----------
    Willett, F. R., et al. (2021). High-performance brain-to-text
        communication via handwriting. Nature, 593(7858), 249-254.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.spikes import threshold_crossings
    >>> # Simulate noisy signal with spikes
    >>> np.random.seed(42)
    >>> signal = np.random.randn(10000)
    >>> signal[1000] = -10  # Add a "spike"
    >>> signal[5000] = -12
    >>> crossings = threshold_crossings(signal, fs=30000)
    >>> len(crossings)  # Should detect the two large negative deflections
    2
    """
    signal = np.asarray(signal, dtype=np.float64)
    refractory_samples = int(refractory_ms * fs / 1000.0)

    def detect_single_channel(sig: NDArray) -> NDArray:
        """Detect crossings in a single channel."""
        rms = np.sqrt(np.mean(sig**2))
        threshold = threshold_rms * rms

        # Find all samples below threshold (for negative threshold)
        if threshold_rms < 0:
            below_threshold = sig < threshold
        else:
            below_threshold = sig > threshold

        # Find crossing points (transition from above to below)
        crossings_mask = np.diff(below_threshold.astype(int)) == 1
        crossing_indices = np.where(crossings_mask)[0] + 1

        # Apply refractory period
        if len(crossing_indices) == 0:
            return np.array([], dtype=np.float64)

        valid_crossings = [crossing_indices[0]]
        for idx in crossing_indices[1:]:
            if idx - valid_crossings[-1] >= refractory_samples:
                valid_crossings.append(idx)

        return np.array(valid_crossings, dtype=np.float64) / fs

    if signal.ndim == 1:
        return detect_single_channel(signal)
    else:
        # Multiple channels
        return [detect_single_channel(signal[:, i]) for i in range(signal.shape[1])]


def spike_band_power(
    signal: ArrayLike,
    fs: float,
    bin_size_ms: float = 20.0,
    freq_range: tuple = (300, 3000),
    t_start: Optional[float] = None,
    t_stop: Optional[float] = None,
) -> NDArray[np.floating]:
    """
    Extract spike band power (SBP) feature.

    Spike band power is the power in the spike frequency band (300-3000 Hz),
    commonly used as an alternative to explicit spike detection.

    Parameters
    ----------
    signal : array_like
        Raw neural signal. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    bin_size_ms : float, optional
        Bin size for power averaging in milliseconds. Default is 20.0.
    freq_range : tuple, optional
        Frequency range for spike band in Hz. Default is (300, 3000).
    t_start : float, optional
        Start time in seconds. If None, starts at 0.
    t_stop : float, optional
        Stop time in seconds. If None, uses full signal length.

    Returns
    -------
    sbp : ndarray
        Spike band power. Shape (n_bins,) or (n_bins, n_channels).

    Notes
    -----
    The spike band power is computed by:
    1. Bandpass filtering the signal to the spike band
    2. Computing the squared magnitude (instantaneous power)
    3. Averaging within each time bin

    References
    ----------
    Willett, F. R., et al. (2023). A high-performance speech neuroprosthesis.
        Nature, 620(7976), 1031-1036.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.spikes import spike_band_power
    >>> # Simulate 1 second of data at 30 kHz
    >>> signal = np.random.randn(30000, 64)
    >>> sbp = spike_band_power(signal, fs=30000, bin_size_ms=20)
    >>> sbp.shape
    (50, 64)
    """
    signal = np.asarray(signal, dtype=np.float64)
    was_1d = signal.ndim == 1
    if was_1d:
        signal = signal[:, np.newaxis]

    n_samples, n_channels = signal.shape

    if t_start is None:
        t_start = 0.0
    if t_stop is None:
        t_stop = n_samples / fs

    # Bandpass filter to spike band
    low, high = freq_range
    nyq = fs / 2.0

    # Check if frequency range is valid for the sampling rate
    if high >= nyq:
        high = nyq * 0.99  # Slightly below Nyquist

    # Design Butterworth bandpass filter
    sos = butter(4, [low / nyq, high / nyq], btype="band", output="sos")

    # Filter signal
    filtered = sosfiltfilt(sos, signal, axis=0)

    # Compute instantaneous power (squared magnitude)
    power = filtered**2

    # Bin the power
    bin_size_s = bin_size_ms / 1000.0
    samples_per_bin = int(bin_size_s * fs)

    start_sample = int(t_start * fs)
    stop_sample = int(t_stop * fs)

    # Ensure we have valid sample indices
    start_sample = max(0, start_sample)
    stop_sample = min(n_samples, stop_sample)

    n_bins = (stop_sample - start_sample) // samples_per_bin

    # Reshape and average within bins
    power_subset = power[start_sample : start_sample + n_bins * samples_per_bin]
    power_binned = power_subset.reshape(n_bins, samples_per_bin, n_channels)
    sbp = power_binned.mean(axis=1)

    if was_1d:
        return sbp[:, 0]
    return sbp
