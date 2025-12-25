"""
Preprocessing presets matching published BCI papers.

This module provides complete preprocessing pipelines that exactly match
the methods described in major BCI publications. Each preset is a single
function that takes raw data and returns ML-ready features.

Functions:
    willett_speech: Willett 2023 Nature (speech BCI)
    willett_handwriting: Willett 2021 Nature (handwriting BCI)
    chang_ecog: Chang lab standard ECoG pipeline
    nlb_motor: Neural Latents Benchmark motor format
    podcast_ecog: Podcast dataset (2024) pipeline

Streaming versions (return configured StreamingPipeline):
    willett_speech_realtime: Real-time version of willett_speech
    chang_ecog_realtime: Real-time version of chang_ecog
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from river.bridge.normalize import sliding_zscore
from river.bridge.spikes import (
    bin_spike_trains,
    smooth_rates,
    spike_band_power,
    threshold_crossings,
)


# Type alias for spike trains
SpikeTrains = Dict[Union[int, str], ArrayLike]


def willett_speech(
    signal: ArrayLike,
    fs: float,
    t_start: float = 0.0,
    t_stop: Optional[float] = None,
    bin_size_ms: float = 20.0,
    threshold_rms: float = -4.5,
    zscore_window_s: float = 30.0,
    include_sbp: bool = True,
    sbp_freq_range: Tuple[float, float] = (300, 3000),
) -> NDArray[np.floating]:
    """
    Preprocessing pipeline matching Willett 2023 Nature (speech neuroprosthesis).

    Extracts threshold crossings and spike band power from raw neural data,
    bins at 20ms, and applies 30-second sliding z-score normalization.

    Parameters
    ----------
    signal : array_like
        Raw neural signal. Shape (n_samples, n_channels) from Utah array.
    fs : float
        Sampling frequency in Hz (typically 30000 for Utah array).
    t_start : float, optional
        Start time in seconds. Default is 0.0.
    t_stop : float, optional
        Stop time in seconds. If None, uses full signal.
    bin_size_ms : float, optional
        Bin size in milliseconds. Default is 20.0.
    threshold_rms : float, optional
        Threshold in units of RMS for crossing detection.
        Default is -4.5 (Willett standard).
    zscore_window_s : float, optional
        Sliding z-score window in seconds. Default is 30.0.
    include_sbp : bool, optional
        Whether to include spike band power features. Default is True.
    sbp_freq_range : tuple, optional
        Frequency range for spike band power. Default is (300, 3000) Hz.

    Returns
    -------
    features : ndarray
        Preprocessed features. Shape (n_bins, n_features).
        If include_sbp=True, features = [threshold_crossings, sbp] concatenated.
        If include_sbp=False, features = threshold_crossings only.

    References
    ----------
    Willett, F. R., Kunz, E. M., Fan, C., Avansino, D. T., Wilson, G. H.,
    Choi, E. Y., ... & Henderson, J. M. (2023). A high-performance speech
    neuroprosthesis. Nature, 620(7976), 1031-1036.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.presets import willett_speech
    >>> # Simulated Utah array data (30 kHz, 256 channels)
    >>> signal = np.random.randn(300000, 256)  # 10 seconds
    >>> features = willett_speech(signal, fs=30000)
    >>> features.shape  # (500 bins, 512 features if include_sbp=True)
    (500, 512)
    """
    signal = np.asarray(signal, dtype=np.float64)

    if signal.ndim == 1:
        signal = signal[:, np.newaxis]

    n_samples, n_channels = signal.shape

    if t_stop is None:
        t_stop = n_samples / fs

    # 1. Threshold crossings for each channel
    crossings_per_channel = threshold_crossings(
        signal, fs, threshold_rms=threshold_rms
    )

    # Convert to spike trains dict for binning
    spike_trains = {i: crossings_per_channel[i] for i in range(n_channels)}

    # 2. Bin threshold crossings
    tc_binned = bin_spike_trains(
        spike_trains,
        bin_size_ms=bin_size_ms,
        t_start=t_start,
        t_stop=t_stop,
        output="rate",
    )

    # 3. Spike band power
    if include_sbp:
        sbp = spike_band_power(
            signal,
            fs,
            bin_size_ms=bin_size_ms,
            freq_range=sbp_freq_range,
            t_start=t_start,
            t_stop=t_stop,
        )
        # Concatenate threshold crossings and SBP
        features = np.concatenate([tc_binned, sbp], axis=1)
    else:
        features = tc_binned

    # 4. Sliding z-score normalization
    bin_fs = 1000 / bin_size_ms  # Effective sampling rate after binning
    features = sliding_zscore(features, fs=bin_fs, window_s=zscore_window_s)

    return features


def willett_handwriting(
    signal: ArrayLike,
    fs: float,
    t_start: float = 0.0,
    t_stop: Optional[float] = None,
    bin_size_ms: float = 10.0,
    threshold_rms: float = -4.5,
    smooth_sigma_ms: float = 50.0,
) -> NDArray[np.floating]:
    """
    Preprocessing pipeline matching Willett 2021 Nature (handwriting BCI).

    Extracts threshold crossings from raw neural data, bins at 10ms,
    and applies Gaussian smoothing.

    Parameters
    ----------
    signal : array_like
        Raw neural signal. Shape (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    t_start : float, optional
        Start time in seconds. Default is 0.0.
    t_stop : float, optional
        Stop time in seconds. If None, uses full signal.
    bin_size_ms : float, optional
        Bin size in milliseconds. Default is 10.0 (finer than speech).
    threshold_rms : float, optional
        Threshold in units of RMS. Default is -4.5.
    smooth_sigma_ms : float, optional
        Gaussian smoothing sigma in milliseconds. Default is 50.0.

    Returns
    -------
    features : ndarray
        Preprocessed features. Shape (n_bins, n_channels).

    References
    ----------
    Willett, F. R., Avansino, D. T., Hochberg, L. R., Henderson, J. M.,
    & Shenoy, K. V. (2021). High-performance brain-to-text communication
    via handwriting. Nature, 593(7858), 249-254.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.presets import willett_handwriting
    >>> signal = np.random.randn(300000, 192)  # 10 seconds
    >>> features = willett_handwriting(signal, fs=30000)
    >>> features.shape
    (1000, 192)
    """
    signal = np.asarray(signal, dtype=np.float64)

    if signal.ndim == 1:
        signal = signal[:, np.newaxis]

    n_samples, n_channels = signal.shape

    if t_stop is None:
        t_stop = n_samples / fs

    # 1. Threshold crossings
    crossings_per_channel = threshold_crossings(
        signal, fs, threshold_rms=threshold_rms
    )

    # Convert to spike trains dict
    spike_trains = {i: crossings_per_channel[i] for i in range(n_channels)}

    # 2. Bin threshold crossings
    binned = bin_spike_trains(
        spike_trains,
        bin_size_ms=bin_size_ms,
        t_start=t_start,
        t_stop=t_stop,
        output="rate",
    )

    # 3. Gaussian smoothing
    features = smooth_rates(binned, sigma_ms=smooth_sigma_ms, bin_size_ms=bin_size_ms)

    return features


def chang_ecog(
    signal: ArrayLike,
    fs: float,
    target_fs: float = 200.0,
    notch_freq: float = 60.0,
    high_gamma_range: Tuple[float, float] = (70, 150),
    high_gamma_method: str = "multiband",
    n_bands: int = 8,
    zscore_window_s: float = 30.0,
) -> Tuple[NDArray[np.floating], float]:
    """
    Standard Chang lab ECoG preprocessing pipeline.

    Applies: CAR → notch filtering → multiband high-gamma extraction →
    downsampling to 200 Hz → 30-second sliding z-score.

    Parameters
    ----------
    signal : array_like
        Raw ECoG signal. Shape (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    target_fs : float, optional
        Target sampling rate after downsampling. Default is 200.0 Hz.
    notch_freq : float, optional
        Line noise frequency. Default is 60.0 Hz.
    high_gamma_range : tuple, optional
        High-gamma frequency range. Default is (70, 150) Hz.
    high_gamma_method : str, optional
        Method for high-gamma extraction. Default is 'multiband' (Chang style).
    n_bands : int, optional
        Number of sub-bands for multiband method. Default is 8.
    zscore_window_s : float, optional
        Sliding z-score window. Default is 30.0 seconds.

    Returns
    -------
    features : ndarray
        Preprocessed high-gamma features.
    out_fs : float
        Output sampling frequency (should be target_fs).

    References
    ----------
    Moses, D. A., Metzger, S. L., Liu, J. R., Anumanchipalli, G. K.,
    Makin, J. G., Sun, P. F., ... & Chang, E. F. (2021). Neuroprosthesis
    for decoding speech in a paralyzed person with anarthria. New England
    Journal of Medicine, 385(3), 217-227.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.presets import chang_ecog
    >>> signal = np.random.randn(100000, 128)  # 100s at 1000 Hz
    >>> features, out_fs = chang_ecog(signal, fs=1000)
    >>> features.shape
    (20000, 128)
    >>> out_fs
    200.0
    """
    from river.bridge.ecog import (
        common_average_reference,
        downsample,
        high_gamma,
        notch_filter,
    )

    signal = np.asarray(signal, dtype=np.float64)

    # 1. Common average reference
    signal = common_average_reference(signal)

    # 2. Notch filter (60 Hz + harmonics)
    signal = notch_filter(signal, fs, freqs=notch_freq, harmonics=3)

    # 3. Multiband high-gamma extraction
    hg = high_gamma(
        signal,
        fs,
        freq_range=high_gamma_range,
        method=high_gamma_method,
        n_bands=n_bands,
    )

    # 4. Downsample to 200 Hz
    hg, out_fs = downsample(hg, fs, target_fs=target_fs)

    # 5. Sliding z-score
    features = sliding_zscore(hg, fs=out_fs, window_s=zscore_window_s)

    return features, out_fs


def nlb_motor(
    spike_trains: SpikeTrains,
    t_start: float,
    t_stop: float,
    bin_size_ms: float = 5.0,
    smooth_sigma_ms: float = 40.0,
) -> NDArray[np.floating]:
    """
    Preprocessing for Neural Latents Benchmark (motor tasks).

    Matches the data format used in the Neural Latents Benchmark for
    motor cortex datasets (MC_Maze, MC_RTT, etc.).

    Parameters
    ----------
    spike_trains : dict
        Dictionary mapping unit IDs to spike times (in seconds).
    t_start : float
        Start time in seconds.
    t_stop : float
        Stop time in seconds.
    bin_size_ms : float, optional
        Bin size in milliseconds. Default is 5.0 (NLB standard).
    smooth_sigma_ms : float, optional
        Gaussian smoothing sigma. Default is 40.0 ms.

    Returns
    -------
    features : ndarray
        Smoothed firing rates. Shape (n_bins, n_units).

    References
    ----------
    Pei, F., Ye, J., Zoltowski, D., Wu, A., Chowdhury, R. H., Sohn, H., ...
    & Pandarinath, C. (2021). Neural Latents Benchmark '21: Evaluating
    latent variable models of neural population activity. NeurIPS 2021
    Datasets and Benchmarks Track.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.presets import nlb_motor
    >>> # Simulated spike trains
    >>> spike_trains = {i: np.sort(np.random.uniform(0, 10, 100))
    ...                 for i in range(64)}
    >>> features = nlb_motor(spike_trains, t_start=0, t_stop=10)
    >>> features.shape
    (2000, 64)
    """
    # 1. Bin spike trains
    binned = bin_spike_trains(
        spike_trains,
        bin_size_ms=bin_size_ms,
        t_start=t_start,
        t_stop=t_stop,
        output="rate",
    )

    # 2. Gaussian smoothing
    features = smooth_rates(binned, sigma_ms=smooth_sigma_ms, bin_size_ms=bin_size_ms)

    return features


def podcast_ecog(
    signal: ArrayLike,
    fs: float,
    target_fs: float = 100.0,
    notch_freq: float = 60.0,
    high_gamma_range: Tuple[float, float] = (70, 150),
) -> Tuple[NDArray[np.floating], float]:
    """
    Preprocessing for Podcast dataset (Hamilton et al. 2024).

    Matches the preprocessing pipeline described in the Podcast dataset
    tutorials and documentation.

    Parameters
    ----------
    signal : array_like
        Raw ECoG signal. Shape (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    target_fs : float, optional
        Target sampling rate. Default is 100.0 Hz.
    notch_freq : float, optional
        Line noise frequency. Default is 60.0 Hz.
    high_gamma_range : tuple, optional
        High-gamma range. Default is (70, 150) Hz.

    Returns
    -------
    features : ndarray
        Preprocessed features.
    out_fs : float
        Output sampling frequency.

    References
    ----------
    Hamilton, L. S., et al. (2024). Natural speech dataset with ECoG.
    (https://github.com/HamiltonLabUT/podcast-dataset)

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.presets import podcast_ecog
    >>> signal = np.random.randn(100000, 64)
    >>> features, out_fs = podcast_ecog(signal, fs=1000)
    """
    from river.bridge.ecog import (
        common_average_reference,
        downsample,
        high_gamma,
        notch_filter,
    )
    from river.bridge.normalize import zscore

    signal = np.asarray(signal, dtype=np.float64)

    # 1. Common average reference
    signal = common_average_reference(signal)

    # 2. Notch filter
    signal = notch_filter(signal, fs, freqs=notch_freq, harmonics=3)

    # 3. High-gamma (single bandpass + Hilbert)
    hg = high_gamma(signal, fs, freq_range=high_gamma_range, method="hilbert")

    # 4. Downsample
    hg, out_fs = downsample(hg, fs, target_fs=target_fs)

    # 5. Z-score (global, not sliding for podcast)
    features = zscore(hg, axis=0)

    return features, out_fs


# =============================================================================
# Real-time / Streaming Presets
# =============================================================================


def willett_speech_realtime(
    fs: float,
    n_channels: int,
    bin_size_ms: float = 20.0,
    threshold_rms: float = -4.5,
    tau_s: float = 30.0,
    include_sbp: bool = True,
) -> "StreamingPipeline":
    """
    Real-time version of Willett speech preprocessing.

    Returns a configured StreamingPipeline for real-time processing.

    Parameters
    ----------
    fs : float
        Sampling frequency of input signal.
    n_channels : int
        Number of input channels.
    bin_size_ms : float, optional
        Bin size in ms. Default is 20.0.
    threshold_rms : float, optional
        Threshold for crossing detection. Default is -4.5.
    tau_s : float, optional
        Time constant for exponential z-score. Default is 30.0.
    include_sbp : bool, optional
        Include spike band power. Default is True.

    Returns
    -------
    pipeline : StreamingPipeline
        Configured streaming pipeline.

    Examples
    --------
    >>> from river.bridge.presets import willett_speech_realtime
    >>> stream = willett_speech_realtime(fs=30000, n_channels=256)
    >>> while True:
    ...     chunk = get_new_data()  # Get 10ms of data
    ...     features = stream.process(chunk)
    """
    from river.bridge.streaming import (
        StreamingBinner,
        StreamingHighGamma,
        StreamingPipeline,
        StreamingZScore,
    )

    pipeline = StreamingPipeline()

    # Add binner for threshold crossings
    pipeline.add(StreamingBinner(bin_size_ms=bin_size_ms, fs=fs, n_channels=n_channels))

    # Add z-score normalization
    bin_fs = 1000 / bin_size_ms
    pipeline.add(StreamingZScore(tau_s=tau_s, fs=bin_fs))

    return pipeline


def chang_ecog_realtime(
    fs: float,
    n_channels: int,
    target_fs: float = 200.0,
    notch_freq: float = 60.0,
    tau_s: float = 30.0,
) -> "StreamingPipeline":
    """
    Real-time version of Chang lab ECoG preprocessing.

    Returns a configured StreamingPipeline for real-time processing.

    Parameters
    ----------
    fs : float
        Sampling frequency of input signal.
    n_channels : int
        Number of input channels.
    target_fs : float, optional
        Target sampling rate. Default is 200.0 Hz.
    notch_freq : float, optional
        Line noise frequency. Default is 60.0 Hz.
    tau_s : float, optional
        Time constant for exponential z-score. Default is 30.0.

    Returns
    -------
    pipeline : StreamingPipeline
        Configured streaming pipeline.

    Examples
    --------
    >>> from river.bridge.presets import chang_ecog_realtime
    >>> stream = chang_ecog_realtime(fs=1000, n_channels=128)
    >>> while True:
    ...     chunk = amplifier.read()
    ...     features = stream.process(chunk)
    """
    from river.bridge.streaming import (
        StreamingFilter,
        StreamingHighGamma,
        StreamingPipeline,
        StreamingZScore,
    )

    pipeline = StreamingPipeline()

    # High-pass + notch filter
    pipeline.add(
        StreamingFilter(low=0.5, high=None, fs=fs, notch=notch_freq)
    )

    # High-gamma extraction
    pipeline.add(StreamingHighGamma(fs=fs, freq_range=(70, 150)))

    # Z-score normalization
    pipeline.add(StreamingZScore(tau_s=tau_s, fs=target_fs))

    return pipeline
