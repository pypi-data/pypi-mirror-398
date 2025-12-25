"""
Trial epoching and windowing for neural data.

This module provides functions for extracting epochs around events,
creating sliding windows, and preparing sequences for RNN/Transformer models.

Functions:
    epoch_data: Extract epochs around event times
    sliding_window: Create overlapping windows using stride tricks
    create_sequences: Prepare sequences for RNN/Transformer
    align_to_events: Align continuous data to discrete labels
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray


def epoch_data(
    data: ArrayLike,
    events: ArrayLike,
    fs: float,
    window: Tuple[float, float] = (-0.5, 2.0),
    baseline: Optional[Tuple[float, float]] = None,
) -> NDArray[np.floating]:
    """
    Extract epochs around event times.

    Parameters
    ----------
    data : array_like
        Continuous data. Shape (n_samples,) or (n_samples, n_channels).
    events : array_like
        Event times in seconds.
    fs : float
        Sampling frequency in Hz.
    window : tuple, optional
        Time window around each event in seconds as (start, stop).
        Negative start means before the event. Default is (-0.5, 2.0).
    baseline : tuple, optional
        Baseline period for correction in seconds as (start, stop).
        If provided, the mean of this period is subtracted from each epoch.
        Times are relative to event. Default is None (no baseline correction).

    Returns
    -------
    epochs : ndarray
        Epoched data. Shape (n_events, n_samples_per_epoch) for 1D input,
        or (n_events, n_samples_per_epoch, n_channels) for 2D input.

    Notes
    -----
    Events that would result in epochs extending beyond the data boundaries
    are excluded with a warning.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.epoch import epoch_data
    >>> # 10 seconds of data at 100 Hz
    >>> data = np.random.randn(1000, 64)
    >>> events = np.array([1.0, 3.0, 5.0, 7.0])
    >>> epochs = epoch_data(data, events, fs=100, window=(-0.2, 0.5))
    >>> epochs.shape
    (4, 70, 64)
    """
    data = np.asarray(data, dtype=np.float64)
    events = np.asarray(events, dtype=np.float64)

    if data.ndim == 1:
        data = data[:, np.newaxis]
        squeeze_output = True
    else:
        squeeze_output = False

    n_samples, n_channels = data.shape
    t_start, t_stop = window

    # Convert window to samples
    start_offset = int(round(t_start * fs))
    stop_offset = int(round(t_stop * fs))
    epoch_length = stop_offset - start_offset

    # Convert events to sample indices
    event_samples = np.round(events * fs).astype(int)

    # Filter out events that would go out of bounds
    valid_mask = (
        (event_samples + start_offset >= 0) & (event_samples + stop_offset <= n_samples)
    )
    n_excluded = np.sum(~valid_mask)
    if n_excluded > 0:
        import warnings

        warnings.warn(
            f"Excluded {n_excluded} events that extend beyond data boundaries."
        )
    event_samples = event_samples[valid_mask]
    n_events = len(event_samples)

    if n_events == 0:
        shape = (0, epoch_length) if squeeze_output else (0, epoch_length, n_channels)
        return np.zeros(shape, dtype=np.float64)

    # Extract epochs
    epochs = np.zeros((n_events, epoch_length, n_channels), dtype=np.float64)
    for i, ev in enumerate(event_samples):
        epochs[i] = data[ev + start_offset : ev + stop_offset]

    # Baseline correction
    if baseline is not None:
        bl_start, bl_stop = baseline
        bl_start_sample = int(round((bl_start - t_start) * fs))
        bl_stop_sample = int(round((bl_stop - t_start) * fs))
        bl_mean = epochs[:, bl_start_sample:bl_stop_sample, :].mean(
            axis=1, keepdims=True
        )
        epochs = epochs - bl_mean

    if squeeze_output:
        return epochs[:, :, 0]
    return epochs


def sliding_window(
    data: ArrayLike,
    window_size: int,
    step_size: int = 1,
) -> NDArray[np.floating]:
    """
    Create overlapping windows using stride tricks for memory efficiency.

    Parameters
    ----------
    data : array_like
        Input data. Shape (n_samples,) or (n_samples, n_channels).
    window_size : int
        Size of each window in samples.
    step_size : int, optional
        Step between windows in samples. Default is 1.

    Returns
    -------
    windows : ndarray
        Windowed data. Shape (n_windows, window_size) for 1D input,
        or (n_windows, window_size, n_channels) for 2D input.

    Notes
    -----
    This function uses numpy stride tricks to create a view into the data
    without copying, making it memory efficient for large datasets.
    However, the returned array should not be modified in place.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.epoch import sliding_window
    >>> data = np.arange(10)
    >>> windows = sliding_window(data, window_size=3, step_size=2)
    >>> windows
    array([[0, 1, 2],
           [2, 3, 4],
           [4, 5, 6],
           [6, 7, 8]])
    """
    data = np.asarray(data, dtype=np.float64)

    if data.ndim == 1:
        n_samples = len(data)
        n_windows = (n_samples - window_size) // step_size + 1

        if n_windows <= 0:
            return np.zeros((0, window_size), dtype=np.float64)

        # Use stride tricks for memory efficiency
        shape = (n_windows, window_size)
        strides = (data.strides[0] * step_size, data.strides[0])
        windows = np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)

        # Return a copy to avoid issues with views
        return windows.copy()

    else:
        n_samples, n_channels = data.shape
        n_windows = (n_samples - window_size) // step_size + 1

        if n_windows <= 0:
            return np.zeros((0, window_size, n_channels), dtype=np.float64)

        # Use stride tricks for memory efficiency
        shape = (n_windows, window_size, n_channels)
        strides = (
            data.strides[0] * step_size,
            data.strides[0],
            data.strides[1],
        )
        windows = np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)

        return windows.copy()


def create_sequences(
    data: ArrayLike,
    seq_len: int,
    step: int = 1,
    labels: Optional[ArrayLike] = None,
) -> Union[NDArray[np.floating], Tuple[NDArray[np.floating], NDArray]]:
    """
    Prepare sequences for RNN/Transformer models.

    Creates overlapping sequences from continuous data, suitable for
    sequence-to-sequence or sequence-to-one prediction tasks.

    Parameters
    ----------
    data : array_like
        Input data. Shape (n_samples, n_features).
    seq_len : int
        Length of each sequence in samples.
    step : int, optional
        Step between sequence starts. Default is 1.
    labels : array_like, optional
        Labels corresponding to each sample. Shape (n_samples,) or
        (n_samples, n_classes). If provided, returns labels aligned
        to the last sample of each sequence (for seq-to-one prediction).

    Returns
    -------
    sequences : ndarray
        Sequences. Shape (n_sequences, seq_len, n_features).
    sequence_labels : ndarray, optional
        Labels for each sequence (last sample's label). Only returned
        if labels is provided.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.epoch import create_sequences
    >>> data = np.random.randn(100, 64)
    >>> labels = np.random.randint(0, 10, 100)
    >>> X, y = create_sequences(data, seq_len=10, step=5, labels=labels)
    >>> X.shape
    (19, 10, 64)
    >>> y.shape
    (19,)
    """
    data = np.asarray(data, dtype=np.float64)

    if data.ndim == 1:
        data = data[:, np.newaxis]

    n_samples, n_features = data.shape
    n_sequences = (n_samples - seq_len) // step + 1

    if n_sequences <= 0:
        if labels is not None:
            labels = np.asarray(labels)
            label_shape = (0,) if labels.ndim == 1 else (0, labels.shape[1])
            return (
                np.zeros((0, seq_len, n_features), dtype=np.float64),
                np.zeros(label_shape, dtype=labels.dtype),
            )
        return np.zeros((0, seq_len, n_features), dtype=np.float64)

    # Create sequences using stride tricks
    shape = (n_sequences, seq_len, n_features)
    strides = (data.strides[0] * step, data.strides[0], data.strides[1])
    sequences = np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)
    sequences = sequences.copy()

    if labels is not None:
        labels = np.asarray(labels)
        # Get label at the end of each sequence
        end_indices = np.arange(seq_len - 1, seq_len - 1 + n_sequences * step, step)
        sequence_labels = labels[end_indices]
        return sequences, sequence_labels

    return sequences


def align_to_events(
    data: ArrayLike,
    fs: float,
    event_times: ArrayLike,
    event_labels: ArrayLike,
    fill_value: Union[int, float, str] = -1,
) -> NDArray:
    """
    Align continuous data to discrete event labels.

    Creates a label array matching the data length where each sample is
    assigned the label of the most recent event.

    Parameters
    ----------
    data : array_like
        Continuous data. Shape (n_samples,) or (n_samples, n_channels).
        Only used to determine the number of samples.
    fs : float
        Sampling frequency in Hz.
    event_times : array_like
        Times of events in seconds.
    event_labels : array_like
        Labels for each event. Must have same length as event_times.
    fill_value : int, float, or str, optional
        Value to use for samples before the first event.
        Default is -1.

    Returns
    -------
    sample_labels : ndarray
        Label for each sample. Shape (n_samples,).

    Notes
    -----
    This is useful for tasks like phoneme or word alignment where
    you have discrete event boundaries and want to label every sample.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.epoch import align_to_events
    >>> data = np.zeros(1000)  # 10 seconds at 100 Hz
    >>> event_times = np.array([2.0, 5.0, 8.0])
    >>> event_labels = np.array(['a', 'b', 'c'])
    >>> labels = align_to_events(data, fs=100, event_times=event_times,
    ...                          event_labels=event_labels, fill_value='_')
    >>> labels[150]  # Before first event
    '_'
    >>> labels[250]  # After 'a' at 2.0s
    'a'
    """
    data = np.asarray(data)
    event_times = np.asarray(event_times, dtype=np.float64)
    event_labels = np.asarray(event_labels)

    if len(event_times) != len(event_labels):
        raise ValueError("event_times and event_labels must have same length")

    n_samples = data.shape[0]

    # Initialize with fill_value
    if isinstance(fill_value, str) or isinstance(event_labels[0], str):
        sample_labels = np.full(n_samples, fill_value, dtype=event_labels.dtype)
    else:
        sample_labels = np.full(n_samples, fill_value, dtype=event_labels.dtype)

    # Sort events by time
    sort_idx = np.argsort(event_times)
    event_times = event_times[sort_idx]
    event_labels = event_labels[sort_idx]

    # Convert event times to sample indices
    event_samples = np.round(event_times * fs).astype(int)

    # Assign labels
    for i in range(len(event_samples)):
        start_sample = max(0, event_samples[i])
        if i < len(event_samples) - 1:
            end_sample = min(n_samples, event_samples[i + 1])
        else:
            end_sample = n_samples
        sample_labels[start_sample:end_sample] = event_labels[i]

    return sample_labels
