"""
Ring buffer for streaming neural data processing.

Provides efficient circular buffer implementation for maintaining
sample history in real-time processing.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from numpy.typing import NDArray


class RingBuffer:
    """
    Circular buffer for maintaining sample history.

    Efficiently stores a fixed-size history of samples, automatically
    overwriting oldest samples when the buffer is full.

    Parameters
    ----------
    max_samples : int
        Maximum number of samples to store.
    n_channels : int
        Number of channels in the data.

    Examples
    --------
    >>> from river.bridge.streaming import RingBuffer
    >>> buffer = RingBuffer(max_samples=100, n_channels=64)
    >>> buffer.append(np.random.randn(10, 64))
    >>> buffer.get(50).shape
    (50, 64)
    """

    def __init__(self, max_samples: int, n_channels: int):
        self.max_samples = max_samples
        self.n_channels = n_channels
        self._buffer = np.zeros((max_samples, n_channels), dtype=np.float64)
        self._write_idx = 0
        self._n_samples = 0

    def append(self, data: NDArray) -> None:
        """
        Append new data to the buffer.

        Parameters
        ----------
        data : ndarray
            New data to append. Shape (n_samples,) or (n_samples, n_channels).
        """
        data = np.atleast_2d(data)
        if data.ndim == 1:
            data = data[:, np.newaxis]

        n_new = len(data)

        if n_new >= self.max_samples:
            # New data is larger than buffer - just keep last max_samples
            self._buffer[:] = data[-self.max_samples :]
            self._write_idx = 0
            self._n_samples = self.max_samples
        else:
            # Calculate how much wraps around
            end_idx = self._write_idx + n_new

            if end_idx <= self.max_samples:
                # No wrap
                self._buffer[self._write_idx : end_idx] = data
            else:
                # Wraps around
                first_part = self.max_samples - self._write_idx
                self._buffer[self._write_idx :] = data[:first_part]
                self._buffer[: n_new - first_part] = data[first_part:]

            self._write_idx = end_idx % self.max_samples
            self._n_samples = min(self._n_samples + n_new, self.max_samples)

    def get(self, n_samples: Optional[int] = None) -> NDArray[np.floating]:
        """
        Get the last n samples from the buffer.

        Parameters
        ----------
        n_samples : int, optional
            Number of samples to retrieve. If None, returns all available.

        Returns
        -------
        data : ndarray
            Retrieved samples in chronological order.
            Shape (n_samples, n_channels).
        """
        if n_samples is None:
            n_samples = self._n_samples

        n_samples = min(n_samples, self._n_samples)

        if n_samples == 0:
            return np.zeros((0, self.n_channels), dtype=np.float64)

        # Calculate start position
        start_idx = (self._write_idx - n_samples) % self.max_samples

        if start_idx + n_samples <= self.max_samples:
            # No wrap
            return self._buffer[start_idx : start_idx + n_samples].copy()
        else:
            # Wraps around
            first_part = self.max_samples - start_idx
            result = np.zeros((n_samples, self.n_channels), dtype=np.float64)
            result[:first_part] = self._buffer[start_idx:]
            result[first_part:] = self._buffer[: n_samples - first_part]
            return result

    def get_all(self) -> NDArray[np.floating]:
        """
        Get all samples currently in the buffer.

        Returns
        -------
        data : ndarray
            All samples in chronological order.
        """
        return self.get(self._n_samples)

    def clear(self) -> None:
        """Clear the buffer, removing all samples."""
        self._buffer.fill(0)
        self._write_idx = 0
        self._n_samples = 0

    @property
    def n_samples(self) -> int:
        """Number of samples currently in the buffer."""
        return self._n_samples

    @property
    def is_full(self) -> bool:
        """Whether the buffer is full."""
        return self._n_samples >= self.max_samples

    def __len__(self) -> int:
        return self._n_samples

    def __repr__(self) -> str:
        return (
            f"RingBuffer(max_samples={self.max_samples}, "
            f"n_channels={self.n_channels}, "
            f"n_samples={self._n_samples})"
        )
