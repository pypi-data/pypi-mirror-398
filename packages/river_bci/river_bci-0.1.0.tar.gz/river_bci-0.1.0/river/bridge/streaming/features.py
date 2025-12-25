"""
Streaming feature extraction for real-time neural data processing.

Provides real-time high-gamma extraction and spike binning.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.signal import butter, sosfilt, sosfilt_zi

from river.bridge.streaming.buffers import RingBuffer


class StreamingHighGamma:
    """
    Real-time high-gamma envelope extraction.

    Uses causal bandpass filtering followed by squared magnitude
    and lowpass smoothing (approximates Hilbert envelope).

    Parameters
    ----------
    fs : float
        Sampling frequency in Hz.
    freq_range : tuple, optional
        High-gamma frequency range. Default is (70, 150) Hz.
    order : int, optional
        Filter order. Default is 4.
    smooth_ms : float, optional
        Smoothing time constant in ms. Default is 20.0.

    Attributes
    ----------
    latency_ms : float
        Estimated processing latency in milliseconds.

    Examples
    --------
    >>> from river.bridge.streaming import StreamingHighGamma
    >>> hg = StreamingHighGamma(fs=1000)
    >>> while True:
    ...     chunk = get_new_data()
    ...     envelope = hg.process(chunk)
    """

    def __init__(
        self,
        fs: float,
        freq_range: Tuple[float, float] = (70, 150),
        order: int = 4,
        smooth_ms: float = 20.0,
    ):
        self.fs = fs
        self.freq_range = freq_range
        self.order = order
        self.smooth_ms = smooth_ms

        nyq = fs / 2.0
        low, high = freq_range
        high = min(high, nyq * 0.99)

        # Bandpass filter
        self._bp_sos = butter(order, [low / nyq, high / nyq], btype="band", output="sos")

        # Lowpass filter for envelope smoothing
        smooth_freq = 1000 / (2 * np.pi * smooth_ms)  # Convert time constant to freq
        smooth_freq = min(smooth_freq, nyq * 0.5)
        self._lp_sos = butter(2, smooth_freq / nyq, btype="low", output="sos")

        # State
        self._bp_zi: Optional[NDArray] = None
        self._lp_zi: Optional[NDArray] = None
        self._n_channels: Optional[int] = None

        # Latency estimate
        self._latency_samples = order * 2  # Rough estimate

    def _init_state(self, n_channels: int) -> None:
        """Initialize filter states."""
        self._n_channels = n_channels

        bp_zi_base = sosfilt_zi(self._bp_sos)
        self._bp_zi = np.tile(bp_zi_base[:, :, np.newaxis], (1, 1, n_channels))

        lp_zi_base = sosfilt_zi(self._lp_sos)
        self._lp_zi = np.tile(lp_zi_base[:, :, np.newaxis], (1, 1, n_channels))

    def process(self, chunk: NDArray) -> NDArray[np.floating]:
        """
        Process a chunk and extract high-gamma envelope.

        Parameters
        ----------
        chunk : ndarray
            Input data. Shape (n_samples,) or (n_samples, n_channels).

        Returns
        -------
        envelope : ndarray
            High-gamma envelope with same shape as input.
        """
        chunk = np.atleast_2d(chunk)
        if chunk.ndim == 1:
            chunk = chunk[:, np.newaxis]
            squeeze = True
        else:
            squeeze = False

        n_samples, n_channels = chunk.shape

        if self._n_channels is None or self._n_channels != n_channels:
            self._init_state(n_channels)

        # Bandpass filter
        bp_out = np.zeros_like(chunk, dtype=np.float64)
        for ch in range(n_channels):
            bp_out[:, ch], self._bp_zi[:, :, ch] = sosfilt(
                self._bp_sos, chunk[:, ch], zi=self._bp_zi[:, :, ch]
            )

        # Squared magnitude (instantaneous power)
        power = bp_out**2

        # Lowpass smooth
        envelope = np.zeros_like(power)
        for ch in range(n_channels):
            envelope[:, ch], self._lp_zi[:, :, ch] = sosfilt(
                self._lp_sos, power[:, ch], zi=self._lp_zi[:, :, ch]
            )

        # Square root for amplitude
        envelope = np.sqrt(np.maximum(envelope, 0))

        if squeeze:
            return envelope[:, 0]
        return envelope

    def reset(self) -> None:
        """Reset processor state."""
        self._bp_zi = None
        self._lp_zi = None
        self._n_channels = None

    @property
    def latency_ms(self) -> float:
        """Processing latency in milliseconds."""
        return self._latency_samples / self.fs * 1000

    def __repr__(self) -> str:
        return (
            f"StreamingHighGamma(fs={self.fs}, "
            f"freq_range={self.freq_range}, "
            f"latency_ms={self.latency_ms:.1f})"
        )


class StreamingBinner:
    """
    Accumulate samples and emit binned counts/rates.

    Collects samples in a buffer and emits binned output when
    a full bin's worth of samples has been accumulated.

    Parameters
    ----------
    bin_size_ms : float, optional
        Bin size in milliseconds. Default is 20.0.
    fs : float
        Sampling frequency in Hz.
    n_channels : int
        Number of input channels.
    output : {'count', 'rate'}, optional
        Output type. 'count' for spike counts, 'rate' for firing rate.
        Default is 'rate'.

    Examples
    --------
    >>> from river.bridge.streaming import StreamingBinner
    >>> binner = StreamingBinner(bin_size_ms=20, fs=30000, n_channels=256)
    >>> while True:
    ...     chunk = get_new_data()  # e.g., 1ms of data
    ...     binned = binner.process(chunk)
    ...     if binned is not None:  # Full bin accumulated
    ...         process_bin(binned)
    """

    def __init__(
        self,
        bin_size_ms: float = 20.0,
        fs: float = 30000.0,
        n_channels: int = 1,
        output: str = "rate",
    ):
        self.bin_size_ms = bin_size_ms
        self.fs = fs
        self.n_channels = n_channels
        self.output = output

        self._samples_per_bin = int(bin_size_ms * fs / 1000.0)
        self._buffer = np.zeros((self._samples_per_bin, n_channels), dtype=np.float64)
        self._buffer_idx = 0

    def process(self, chunk: NDArray) -> Optional[NDArray[np.floating]]:
        """
        Process a chunk of data.

        Parameters
        ----------
        chunk : ndarray
            Input data. Shape (n_samples,) or (n_samples, n_channels).

        Returns
        -------
        binned : ndarray or None
            Binned output if a full bin was accumulated, None otherwise.
            Shape (n_complete_bins, n_channels).
        """
        chunk = np.atleast_2d(chunk)
        if chunk.ndim == 1:
            chunk = chunk[:, np.newaxis]

        n_samples = len(chunk)
        results = []

        chunk_idx = 0
        while chunk_idx < n_samples:
            # How many samples until bin is full?
            remaining_in_bin = self._samples_per_bin - self._buffer_idx
            n_to_copy = min(remaining_in_bin, n_samples - chunk_idx)

            # Copy samples to buffer
            self._buffer[self._buffer_idx : self._buffer_idx + n_to_copy] = chunk[
                chunk_idx : chunk_idx + n_to_copy
            ]
            self._buffer_idx += n_to_copy
            chunk_idx += n_to_copy

            # Emit bin if full
            if self._buffer_idx >= self._samples_per_bin:
                if self.output == "count":
                    binned = self._buffer.sum(axis=0)
                else:  # rate
                    binned = self._buffer.sum(axis=0) / (self.bin_size_ms / 1000.0)

                results.append(binned)
                self._buffer_idx = 0

        if results:
            return np.array(results)
        return None

    def reset(self) -> None:
        """Reset binner state."""
        self._buffer.fill(0)
        self._buffer_idx = 0

    @property
    def latency_ms(self) -> float:
        """Processing latency (bin size)."""
        return self.bin_size_ms

    def __repr__(self) -> str:
        return (
            f"StreamingBinner(bin_size_ms={self.bin_size_ms}, "
            f"fs={self.fs}, n_channels={self.n_channels})"
        )
