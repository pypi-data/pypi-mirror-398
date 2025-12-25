"""
Streaming smoothing for real-time neural data processing.

Provides causal Gaussian (half-Gaussian) smoothing using exponential
moving average.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from numpy.typing import NDArray


class StreamingSmooth:
    """
    Causal Gaussian (half-Gaussian) smoothing.

    Approximates half-Gaussian smoothing using an exponential moving
    average, which is suitable for real-time processing.

    Parameters
    ----------
    sigma_ms : float, optional
        Smoothing time constant in milliseconds. Default is 50.0.
    fs : float
        Sampling frequency in Hz.

    Notes
    -----
    The exponential moving average with time constant sigma_ms
    approximates a causal Gaussian (half-Gaussian) kernel.

    For symmetric Gaussian smoothing (non-causal), use the offline
    smooth_rates function instead.

    Examples
    --------
    >>> from river.bridge.streaming import StreamingSmooth
    >>> smoother = StreamingSmooth(sigma_ms=50, fs=1000)
    >>> while True:
    ...     chunk = get_data()
    ...     smoothed = smoother.process(chunk)
    """

    def __init__(
        self,
        sigma_ms: float = 50.0,
        fs: float = 1000.0,
    ):
        self.sigma_ms = sigma_ms
        self.fs = fs

        # Convert sigma to decay factor
        # For exponential smoothing: alpha = 1 - exp(-dt / tau)
        # where tau = sigma_ms / 1000
        dt = 1.0 / fs
        tau = sigma_ms / 1000.0
        self._alpha = 1.0 - np.exp(-dt / tau)

        # State
        self._state: Optional[NDArray] = None
        self._n_channels: Optional[int] = None

    def process(self, chunk: NDArray) -> NDArray[np.floating]:
        """
        Process a chunk with causal smoothing.

        Parameters
        ----------
        chunk : ndarray
            Input data. Shape (n_samples,) or (n_samples, n_channels).

        Returns
        -------
        smoothed : ndarray
            Smoothed data with same shape as input.
        """
        chunk = np.atleast_2d(chunk)
        if chunk.ndim == 1:
            chunk = chunk[:, np.newaxis]
            squeeze = True
        else:
            squeeze = False

        chunk = chunk.astype(np.float64)
        n_samples, n_channels = chunk.shape

        # Initialize state
        if self._state is None or self._n_channels != n_channels:
            self._n_channels = n_channels
            self._state = chunk[0].copy() if n_samples > 0 else np.zeros(n_channels)

        # Apply exponential moving average
        output = np.zeros_like(chunk)
        alpha = self._alpha

        for i in range(n_samples):
            self._state = alpha * chunk[i] + (1 - alpha) * self._state
            output[i] = self._state

        if squeeze:
            return output[:, 0]
        return output

    def reset(self) -> None:
        """Reset smoother state."""
        self._state = None
        self._n_channels = None

    @property
    def latency_ms(self) -> float:
        """Processing latency (approximately sigma_ms / 2 for EMA)."""
        return self.sigma_ms / 2

    def __repr__(self) -> str:
        return f"StreamingSmooth(sigma_ms={self.sigma_ms}, fs={self.fs})"
