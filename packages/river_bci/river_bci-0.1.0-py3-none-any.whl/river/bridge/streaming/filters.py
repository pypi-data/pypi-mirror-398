"""
Streaming filters for real-time neural signal processing.

Provides causal IIR filtering with state preservation between chunks.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.signal import butter, group_delay, iirnotch, lfilter, lfilter_zi, sosfilt, sosfilt_zi, tf2sos


class StreamingFilter:
    """
    Causal IIR filter with state preservation.

    Maintains filter state between calls to process(), enabling
    continuous real-time filtering of chunked data.

    Parameters
    ----------
    low : float or None
        Low cutoff frequency in Hz. If None, no high-pass.
    high : float or None
        High cutoff frequency in Hz. If None, no low-pass.
    fs : float
        Sampling frequency in Hz.
    order : int, optional
        Filter order. Default is 4.
    notch : float or None, optional
        Notch filter frequency. If provided, applies notch filter.
    notch_q : float, optional
        Notch filter quality factor. Default is 30.

    Attributes
    ----------
    latency_ms : float
        Estimated filter group delay in milliseconds.

    Examples
    --------
    >>> from river.bridge.streaming import StreamingFilter
    >>> filt = StreamingFilter(low=1.0, high=100.0, fs=1000, notch=60)
    >>> while True:
    ...     chunk = get_new_data()  # e.g., 10ms of data
    ...     filtered = filt.process(chunk)
    """

    def __init__(
        self,
        low: Optional[float],
        high: Optional[float],
        fs: float,
        order: int = 4,
        notch: Optional[float] = None,
        notch_q: float = 30.0,
    ):
        self.fs = fs
        self.order = order
        self.notch = notch
        self.notch_q = notch_q

        nyq = fs / 2.0
        self._sos_list = []
        self._zi_list = []
        self._n_channels: Optional[int] = None

        # Build bandpass/highpass/lowpass filter
        if low is not None and high is not None:
            # Bandpass
            high = min(high, nyq * 0.99)
            sos = butter(order, [low / nyq, high / nyq], btype="band", output="sos")
            self._sos_list.append(sos)
        elif low is not None:
            # Highpass
            sos = butter(order, low / nyq, btype="high", output="sos")
            self._sos_list.append(sos)
        elif high is not None:
            # Lowpass
            high = min(high, nyq * 0.99)
            sos = butter(order, high / nyq, btype="low", output="sos")
            self._sos_list.append(sos)

        # Build notch filter(s)
        if notch is not None:
            # Add harmonics up to Nyquist
            harmonics = 1
            while notch * (harmonics + 1) < nyq:
                harmonics += 1

            for h in range(1, harmonics + 1):
                freq = notch * h
                if freq < nyq:
                    b, a = iirnotch(freq, notch_q, fs)
                    sos = tf2sos(b, a)
                    self._sos_list.append(sos)

        # Compute latency
        self._latency_samples = self._compute_latency()

    def _compute_latency(self) -> float:
        """Compute approximate group delay at center frequency."""
        if not self._sos_list:
            return 0.0

        # Use first filter's group delay as approximation
        sos = self._sos_list[0]
        # Convert SOS to transfer function for group_delay
        from scipy.signal import sos2tf

        b, a = sos2tf(sos)
        try:
            w, gd = group_delay((b, a), fs=self.fs)
            # Return delay at center of passband
            return float(gd[len(gd) // 2])
        except Exception:
            return 0.0

    def _init_state(self, n_channels: int) -> None:
        """Initialize filter states for given number of channels."""
        self._n_channels = n_channels
        self._zi_list = []

        for sos in self._sos_list:
            # sosfilt_zi returns shape (n_sections, 2)
            # We need to tile for each channel
            zi_base = sosfilt_zi(sos)
            # Shape: (n_sections, 2, n_channels)
            zi = np.tile(zi_base[:, :, np.newaxis], (1, 1, n_channels))
            self._zi_list.append(zi)

    def process(self, chunk: NDArray) -> NDArray[np.floating]:
        """
        Process a chunk of data through the filter.

        Parameters
        ----------
        chunk : ndarray
            Input data chunk. Shape (n_samples,) or (n_samples, n_channels).

        Returns
        -------
        filtered : ndarray
            Filtered data with same shape as input.
        """
        chunk = np.atleast_2d(chunk)
        if chunk.ndim == 1:
            chunk = chunk[:, np.newaxis]
            squeeze = True
        else:
            squeeze = False

        n_samples, n_channels = chunk.shape

        # Initialize state on first call or if channels change
        if self._n_channels is None or self._n_channels != n_channels:
            self._init_state(n_channels)

        # Apply each filter in sequence
        output = chunk.astype(np.float64)

        for i, sos in enumerate(self._sos_list):
            # Apply filter to each channel
            filtered = np.zeros_like(output)
            zi = self._zi_list[i]

            for ch in range(n_channels):
                filtered[:, ch], zi[:, :, ch] = sosfilt(
                    sos, output[:, ch], zi=zi[:, :, ch]
                )

            self._zi_list[i] = zi
            output = filtered

        if squeeze:
            return output[:, 0]
        return output

    def reset(self) -> None:
        """Reset filter state."""
        self._n_channels = None
        self._zi_list = []

    @property
    def latency_ms(self) -> float:
        """Processing latency in milliseconds."""
        return self._latency_samples / self.fs * 1000

    def __repr__(self) -> str:
        return (
            f"StreamingFilter(fs={self.fs}, order={self.order}, "
            f"notch={self.notch}, latency_ms={self.latency_ms:.1f})"
        )
