"""
ECoG/LFP signal processing for BCI research.

This module provides functions for processing electrocorticography (ECoG) and
local field potential (LFP) signals, including filtering, high-gamma extraction,
and common average referencing.

Default parameters match Chang lab conventions:
- 200 Hz target sample rate
- 70-150 Hz high-gamma band
- 30s sliding z-score normalization

Functions:
    notch_filter: Remove line noise and harmonics
    bandpass: Butterworth bandpass filtering
    hilbert_envelope: Analytic amplitude extraction
    high_gamma: Extract high-gamma features (hilbert or multiband method)
    extract_bands: Multi-band power extraction
    common_average_reference: CAR re-referencing
    downsample: Downsample signal to target rate
    ecog_pipeline: Full preprocessing pipeline
"""

from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.signal import butter, decimate, hilbert, iirnotch, sosfilt, sosfiltfilt


# Standard frequency bands for neural signals
STANDARD_BANDS: Dict[str, Tuple[float, float]] = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 70),
    "high_gamma": (70, 150),
}


def notch_filter(
    signal: ArrayLike,
    fs: float,
    freqs: Union[float, list] = 60.0,
    harmonics: int = 3,
    q: float = 30.0,
    realtime: bool = False,
) -> NDArray[np.floating]:
    """
    Remove line noise and harmonics using notch filtering.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    freqs : float or list, optional
        Base frequency (or list of frequencies) to remove. Default is 60.0 Hz.
    harmonics : int, optional
        Number of harmonics to remove (including fundamental).
        Default is 3 (removes 60, 120, 180 Hz for US line noise).
    q : float, optional
        Quality factor of the notch filter. Higher values create narrower
        notches. Default is 30.0.
    realtime : bool, optional
        If True, use causal filtering (lfilter). If False, use zero-phase
        filtering (filtfilt). Default is False.

    Returns
    -------
    filtered : ndarray
        Signal with line noise removed.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import notch_filter
    >>> # Create signal with 60 Hz noise
    >>> t = np.linspace(0, 1, 1000)
    >>> signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 60 * t)
    >>> filtered = notch_filter(signal, fs=1000, freqs=60)
    """
    signal = np.asarray(signal, dtype=np.float64)

    # Handle single frequency or list
    if isinstance(freqs, (int, float)):
        base_freqs = [freqs]
    else:
        base_freqs = list(freqs)

    # Generate all frequencies to notch (fundamentals + harmonics)
    notch_freqs = []
    for base in base_freqs:
        for h in range(1, harmonics + 1):
            freq = base * h
            if freq < fs / 2:  # Must be below Nyquist
                notch_freqs.append(freq)

    # Apply notch filters sequentially
    filtered = signal.copy()
    for freq in notch_freqs:
        b, a = iirnotch(freq, q, fs)
        if realtime:
            from scipy.signal import lfilter

            if signal.ndim == 1:
                filtered = lfilter(b, a, filtered)
            else:
                filtered = lfilter(b, a, filtered, axis=0)
        else:
            from scipy.signal import filtfilt

            if signal.ndim == 1:
                filtered = filtfilt(b, a, filtered)
            else:
                filtered = filtfilt(b, a, filtered, axis=0)

    return filtered


def bandpass(
    signal: ArrayLike,
    fs: float,
    low: float,
    high: float,
    order: int = 4,
    realtime: bool = False,
) -> NDArray[np.floating]:
    """
    Butterworth bandpass filter.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    low : float
        Low cutoff frequency in Hz.
    high : float
        High cutoff frequency in Hz.
    order : int, optional
        Filter order. Default is 4.
    realtime : bool, optional
        If True, use causal filtering (sosfilt). If False, use zero-phase
        filtering (sosfiltfilt). Default is False.

    Returns
    -------
    filtered : ndarray
        Bandpass filtered signal.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import bandpass
    >>> signal = np.random.randn(10000, 64)
    >>> filtered = bandpass(signal, fs=1000, low=70, high=150)
    """
    signal = np.asarray(signal, dtype=np.float64)
    nyq = fs / 2.0

    # Ensure frequencies are below Nyquist
    high = min(high, nyq * 0.99)
    low = max(low, 0.1)  # Avoid DC

    sos = butter(order, [low / nyq, high / nyq], btype="band", output="sos")

    if realtime:
        if signal.ndim == 1:
            return sosfilt(sos, signal)
        else:
            return sosfilt(sos, signal, axis=0)
    else:
        if signal.ndim == 1:
            return sosfiltfilt(sos, signal)
        else:
            return sosfiltfilt(sos, signal, axis=0)


def hilbert_envelope(
    signal: ArrayLike,
    axis: int = 0,
) -> NDArray[np.floating]:
    """
    Extract analytic amplitude (envelope) using Hilbert transform.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples,) or (n_samples, n_channels).
    axis : int, optional
        Axis along which to compute the Hilbert transform. Default is 0.

    Returns
    -------
    envelope : ndarray
        Amplitude envelope of the analytic signal.

    Notes
    -----
    The Hilbert transform is computed using FFT and is therefore non-causal.
    For real-time applications, use streaming.StreamingHighGamma which uses
    a causal approximation.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import hilbert_envelope
    >>> # Create amplitude-modulated signal
    >>> t = np.linspace(0, 1, 1000)
    >>> carrier = np.sin(2 * np.pi * 100 * t)
    >>> envelope_true = 1 + 0.5 * np.sin(2 * np.pi * 5 * t)
    >>> signal = carrier * envelope_true
    >>> envelope_est = hilbert_envelope(signal)
    """
    signal = np.asarray(signal, dtype=np.float64)
    analytic = hilbert(signal, axis=axis)
    return np.abs(analytic)


def high_gamma(
    signal: ArrayLike,
    fs: float,
    freq_range: Tuple[float, float] = (70, 150),
    method: Literal["hilbert", "multiband"] = "hilbert",
    n_bands: int = 8,
    realtime: bool = False,
) -> NDArray[np.floating]:
    """
    Extract high-gamma band features.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    freq_range : tuple, optional
        Frequency range for high-gamma in Hz. Default is (70, 150).
    method : {'hilbert', 'multiband'}, optional
        Extraction method:
        - 'hilbert': Single bandpass + Hilbert transform (fast, default)
        - 'multiband': Average across log-spaced sub-bands (Chang lab style)
        Default is 'hilbert'.
    n_bands : int, optional
        Number of sub-bands for multiband method. Default is 8.
    realtime : bool, optional
        If True, use causal filtering. If False, use zero-phase filtering.
        Default is False.

    Returns
    -------
    hg : ndarray
        High-gamma envelope with same shape as input.

    Notes
    -----
    The multiband method computes the analytic amplitude in multiple
    log-spaced sub-bands and averages them. This is more robust to
    narrow-band noise but slower than single-band Hilbert.

    For real-time applications with causal processing, consider using
    streaming.StreamingHighGamma.

    References
    ----------
    Crone, N. E., et al. (2001). Induced electrocorticographic gamma activity
        during auditory perception. Clinical Neurophysiology, 112(4), 565-582.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import high_gamma
    >>> signal = np.random.randn(10000, 64)
    >>> hg = high_gamma(signal, fs=1000, method='hilbert')
    >>> hg.shape
    (10000, 64)
    """
    signal = np.asarray(signal, dtype=np.float64)
    low, high = freq_range

    if method == "hilbert":
        # Single bandpass + Hilbert
        filtered = bandpass(signal, fs, low, high, realtime=realtime)
        if realtime:
            # Causal envelope approximation: squared + lowpass
            envelope = filtered**2
            # Lowpass to smooth the squared signal
            nyq = fs / 2.0
            sos = butter(2, 20 / nyq, btype="low", output="sos")
            envelope = sosfilt(sos, envelope, axis=0)
            return np.sqrt(np.maximum(envelope, 0))
        else:
            return hilbert_envelope(filtered)

    elif method == "multiband":
        # Multi-band averaging (Chang lab style)
        # Create log-spaced center frequencies
        center_freqs = np.geomspace(low, high, n_bands)

        # Compute bandwidth based on neighboring frequencies
        envelopes = []
        for i, cf in enumerate(center_freqs):
            # Bandwidth proportional to center frequency (constant-Q)
            if i == 0:
                bw_low = cf - low
            else:
                bw_low = (cf - center_freqs[i - 1]) / 2

            if i == len(center_freqs) - 1:
                bw_high = high - cf
            else:
                bw_high = (center_freqs[i + 1] - cf) / 2

            f_low = cf - bw_low
            f_high = cf + bw_high

            filtered = bandpass(signal, fs, f_low, f_high, realtime=realtime)
            if realtime:
                envelope = filtered**2
                nyq = fs / 2.0
                sos = butter(2, 20 / nyq, btype="low", output="sos")
                envelope = sosfilt(sos, envelope, axis=0)
                envelope = np.sqrt(np.maximum(envelope, 0))
            else:
                envelope = hilbert_envelope(filtered)
            envelopes.append(envelope)

        return np.mean(envelopes, axis=0)

    else:
        raise ValueError(f"method must be 'hilbert' or 'multiband', got {method!r}")


def extract_bands(
    signal: ArrayLike,
    fs: float,
    bands: Optional[Dict[str, Tuple[float, float]]] = None,
    method: Literal["hilbert", "power"] = "hilbert",
    realtime: bool = False,
) -> Dict[str, NDArray[np.floating]]:
    """
    Extract power/amplitude in multiple frequency bands.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    bands : dict, optional
        Dictionary mapping band names to (low, high) frequency tuples.
        If None, uses standard bands (delta, theta, alpha, beta, gamma,
        high_gamma).
    method : {'hilbert', 'power'}, optional
        - 'hilbert': Return analytic amplitude (magnitude of Hilbert transform)
        - 'power': Return squared amplitude
        Default is 'hilbert'.
    realtime : bool, optional
        If True, use causal filtering. Default is False.

    Returns
    -------
    band_features : dict
        Dictionary mapping band names to feature arrays.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import extract_bands
    >>> signal = np.random.randn(10000, 64)
    >>> bands = extract_bands(signal, fs=1000)
    >>> list(bands.keys())
    ['delta', 'theta', 'alpha', 'beta', 'gamma', 'high_gamma']
    """
    if bands is None:
        bands = STANDARD_BANDS

    signal = np.asarray(signal, dtype=np.float64)
    result = {}

    for name, (low, high) in bands.items():
        # Skip bands outside the Nyquist frequency
        if low >= fs / 2:
            continue

        filtered = bandpass(signal, fs, low, min(high, fs / 2 * 0.99), realtime=realtime)

        if realtime:
            envelope = filtered**2
            nyq = fs / 2.0
            smooth_freq = min(low / 2, 5)  # Smooth at frequency below band
            sos = butter(2, smooth_freq / nyq, btype="low", output="sos")
            envelope = sosfilt(sos, envelope, axis=0)
            envelope = np.sqrt(np.maximum(envelope, 0))
        else:
            envelope = hilbert_envelope(filtered)

        if method == "power":
            result[name] = envelope**2
        else:
            result[name] = envelope

    return result


def common_average_reference(
    signal: ArrayLike,
    exclude_channels: Optional[list] = None,
) -> NDArray[np.floating]:
    """
    Apply common average reference (CAR).

    Subtracts the mean across channels from each channel at each time point.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples, n_channels).
    exclude_channels : list, optional
        Indices of channels to exclude from the reference calculation
        (but still re-reference). Useful for noisy channels.

    Returns
    -------
    referenced : ndarray
        CAR-referenced signal.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import common_average_reference
    >>> signal = np.random.randn(10000, 64)
    >>> referenced = common_average_reference(signal)
    >>> np.allclose(referenced.mean(axis=1), 0)
    True
    """
    signal = np.asarray(signal, dtype=np.float64)

    if signal.ndim == 1:
        # Single channel - CAR doesn't make sense
        return signal

    if exclude_channels is not None:
        # Create mask for included channels
        include_mask = np.ones(signal.shape[1], dtype=bool)
        include_mask[exclude_channels] = False
        ref = signal[:, include_mask].mean(axis=1, keepdims=True)
    else:
        ref = signal.mean(axis=1, keepdims=True)

    return signal - ref


def downsample(
    signal: ArrayLike,
    fs: float,
    target_fs: float = 200.0,
) -> Tuple[NDArray[np.floating], float]:
    """
    Downsample signal to target sampling rate.

    Uses scipy.signal.decimate with anti-aliasing.

    Parameters
    ----------
    signal : array_like
        Input signal. Shape (n_samples,) or (n_samples, n_channels).
    fs : float
        Current sampling frequency in Hz.
    target_fs : float, optional
        Target sampling frequency in Hz. Default is 200.0 (Chang lab standard).

    Returns
    -------
    downsampled : ndarray
        Downsampled signal.
    new_fs : float
        Actual new sampling frequency (may differ slightly from target_fs
        due to integer downsampling factor).

    Notes
    -----
    The downsampling factor must be an integer. If fs/target_fs is not
    an integer, the signal is downsampled by the nearest integer factor,
    resulting in a slightly different actual sampling rate.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import downsample
    >>> signal = np.random.randn(10000, 64)
    >>> downsampled, new_fs = downsample(signal, fs=1000, target_fs=200)
    >>> downsampled.shape
    (2000, 64)
    >>> new_fs
    200.0
    """
    signal = np.asarray(signal, dtype=np.float64)

    if target_fs >= fs:
        return signal, fs

    factor = int(round(fs / target_fs))

    if factor == 1:
        return signal, fs

    if signal.ndim == 1:
        downsampled = decimate(signal, factor, zero_phase=True)
    else:
        downsampled = decimate(signal, factor, axis=0, zero_phase=True)

    new_fs = fs / factor
    return downsampled, new_fs


def ecog_pipeline(
    signal: ArrayLike,
    fs: float,
    target_fs: float = 200.0,
    notch_freq: float = 60.0,
    high_gamma_range: Tuple[float, float] = (70, 150),
    high_gamma_method: Literal["hilbert", "multiband"] = "hilbert",
    zscore_window_s: float = 30.0,
    realtime: bool = False,
) -> Tuple[NDArray[np.floating], float]:
    """
    Complete ECoG preprocessing pipeline.

    Applies: CAR → notch → high-gamma extraction → downsample → sliding z-score

    Parameters
    ----------
    signal : array_like
        Raw ECoG signal. Shape (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    target_fs : float, optional
        Target sampling rate after downsampling. Default is 200.0 Hz.
    notch_freq : float, optional
        Line noise frequency. Default is 60.0 Hz (US).
    high_gamma_range : tuple, optional
        High-gamma frequency range. Default is (70, 150) Hz.
    high_gamma_method : {'hilbert', 'multiband'}, optional
        High-gamma extraction method. Default is 'hilbert'.
    zscore_window_s : float, optional
        Window size for sliding z-score in seconds. Default is 30.0.
    realtime : bool, optional
        If True, use causal processing. Default is False.

    Returns
    -------
    features : ndarray
        Preprocessed high-gamma features.
    out_fs : float
        Output sampling frequency.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.ecog import ecog_pipeline
    >>> signal = np.random.randn(100000, 64)  # 100s at 1000 Hz
    >>> features, out_fs = ecog_pipeline(signal, fs=1000)
    >>> features.shape
    (20000, 64)
    >>> out_fs
    200.0
    """
    from river.bridge.normalize import sliding_zscore

    signal = np.asarray(signal, dtype=np.float64)

    # 1. Common average reference
    signal = common_average_reference(signal)

    # 2. Notch filter
    signal = notch_filter(signal, fs, freqs=notch_freq, realtime=realtime)

    # 3. High-gamma extraction
    hg = high_gamma(
        signal,
        fs,
        freq_range=high_gamma_range,
        method=high_gamma_method,
        realtime=realtime,
    )

    # 4. Downsample
    hg, out_fs = downsample(hg, fs, target_fs)

    # 5. Sliding z-score
    features = sliding_zscore(hg, out_fs, window_s=zscore_window_s)

    return features, out_fs
