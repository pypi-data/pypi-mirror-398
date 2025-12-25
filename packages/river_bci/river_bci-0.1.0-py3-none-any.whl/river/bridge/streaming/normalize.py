"""
Streaming normalization for real-time neural data processing.

Provides online z-score normalization using exponential moving statistics.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from numpy.typing import NDArray


class StreamingZScore:
    """
    Online z-score with exponential moving average.

    Uses Welford's online algorithm adapted for exponential weighting
    to compute running mean and variance.

    Parameters
    ----------
    tau_s : float, optional
        Time constant in seconds. Default is 30.0 (matches offline
        sliding z-score window).
    fs : float
        Sampling frequency in Hz.
    eps : float, optional
        Small constant for numerical stability. Default is 1e-8.

    Notes
    -----
    The exponential weighting uses:
        alpha = 1 - exp(-dt / tau)

    where dt = 1/fs is the sample period. This gives approximately
    equivalent smoothing to a sliding window of width tau_s.

    Examples
    --------
    >>> from river.bridge.streaming import StreamingZScore
    >>> zscore = StreamingZScore(tau_s=30.0, fs=200)
    >>> while True:
    ...     chunk = get_features()
    ...     normalized = zscore.process(chunk)
    """

    def __init__(
        self,
        tau_s: float = 30.0,
        fs: float = 200.0,
        eps: float = 1e-8,
    ):
        self.tau_s = tau_s
        self.fs = fs
        self.eps = eps

        # Compute decay factor
        dt = 1.0 / fs
        self._alpha = 1.0 - np.exp(-dt / tau_s)

        # Running statistics
        self._mean: Optional[NDArray] = None
        self._var: Optional[NDArray] = None
        self._n_channels: Optional[int] = None
        self._initialized = False

    def process(self, chunk: NDArray) -> NDArray[np.floating]:
        """
        Process a chunk and return z-scored output.

        Parameters
        ----------
        chunk : ndarray
            Input data. Shape (n_samples,) or (n_samples, n_channels).

        Returns
        -------
        normalized : ndarray
            Z-scored data with same shape as input.
        """
        chunk = np.atleast_2d(chunk)
        if chunk.ndim == 1:
            chunk = chunk[:, np.newaxis]
            squeeze = True
        else:
            squeeze = False

        chunk = chunk.astype(np.float64)
        n_samples, n_channels = chunk.shape

        # Initialize on first call
        if not self._initialized or self._n_channels != n_channels:
            self._n_channels = n_channels
            self._mean = np.zeros(n_channels, dtype=np.float64)
            self._var = np.ones(n_channels, dtype=np.float64)
            self._initialized = True

        # Process each sample
        output = np.zeros_like(chunk)
        alpha = self._alpha

        for i in range(n_samples):
            x = chunk[i]

            # Update running mean
            delta = x - self._mean
            self._mean = self._mean + alpha * delta

            # Update running variance using Welford's method
            delta2 = x - self._mean
            self._var = (1 - alpha) * self._var + alpha * delta * delta2

            # Normalize
            std = np.sqrt(self._var)
            output[i] = (x - self._mean) / (std + self.eps)

        if squeeze:
            return output[:, 0]
        return output

    def reset(self) -> None:
        """Reset running statistics."""
        self._mean = None
        self._var = None
        self._n_channels = None
        self._initialized = False

    @property
    def mean(self) -> Optional[NDArray]:
        """Current running mean."""
        return self._mean

    @property
    def std(self) -> Optional[NDArray]:
        """Current running standard deviation."""
        if self._var is None:
            return None
        return np.sqrt(self._var)

    @property
    def latency_ms(self) -> float:
        """Processing latency (essentially zero for z-score)."""
        return 0.0

    def __repr__(self) -> str:
        return f"StreamingZScore(tau_s={self.tau_s}, fs={self.fs})"
