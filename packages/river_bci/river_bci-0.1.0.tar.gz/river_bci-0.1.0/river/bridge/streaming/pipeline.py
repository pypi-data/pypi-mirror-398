"""
Streaming pipeline for chaining real-time processors.

Provides a simple container for chaining multiple streaming processors.
"""

from __future__ import annotations

from typing import Any, List, Optional, Protocol

import numpy as np
from numpy.typing import NDArray


class StreamingProcessor(Protocol):
    """Protocol for streaming processors."""

    def process(self, chunk: NDArray) -> Optional[NDArray]:
        """Process a chunk of data."""
        ...

    def reset(self) -> None:
        """Reset processor state."""
        ...

    @property
    def latency_ms(self) -> float:
        """Processing latency in milliseconds."""
        ...


class StreamingPipeline:
    """
    Chain multiple streaming processors.

    Passes data through each processor in sequence, maintaining
    the streaming nature of the data.

    Examples
    --------
    >>> from river.bridge.streaming import (
    ...     StreamingPipeline, StreamingFilter, StreamingHighGamma, StreamingZScore
    ... )
    >>> pipeline = StreamingPipeline()
    >>> pipeline.add(StreamingFilter(low=0.5, high=None, fs=1000, notch=60))
    >>> pipeline.add(StreamingHighGamma(fs=1000))
    >>> pipeline.add(StreamingZScore(tau_s=30, fs=200))
    >>>
    >>> while True:
    ...     chunk = get_new_data()
    ...     features = pipeline.process(chunk)
    """

    def __init__(self):
        self._processors: List[Any] = []

    def add(self, processor: Any) -> "StreamingPipeline":
        """
        Add a processor to the pipeline.

        Parameters
        ----------
        processor : StreamingProcessor
            Processor to add. Must have process() and reset() methods.

        Returns
        -------
        self : StreamingPipeline
            Returns self for method chaining.
        """
        self._processors.append(processor)
        return self

    def process(self, chunk: NDArray) -> Optional[NDArray[np.floating]]:
        """
        Process a chunk through all processors.

        Parameters
        ----------
        chunk : ndarray
            Input data.

        Returns
        -------
        output : ndarray or None
            Processed data. May be None if a processor (like binner)
            hasn't accumulated enough data to produce output.
        """
        output = chunk

        for processor in self._processors:
            if output is None:
                return None

            result = processor.process(output)

            if result is None:
                return None

            output = result

        return output

    def reset(self) -> None:
        """Reset all processors in the pipeline."""
        for processor in self._processors:
            processor.reset()

    @property
    def latency_ms(self) -> float:
        """Total processing latency in milliseconds."""
        total = 0.0
        for processor in self._processors:
            if hasattr(processor, "latency_ms"):
                total += processor.latency_ms
        return total

    @property
    def processors(self) -> List[Any]:
        """List of processors in the pipeline."""
        return self._processors.copy()

    def __len__(self) -> int:
        return len(self._processors)

    def __repr__(self) -> str:
        names = [type(p).__name__ for p in self._processors]
        return f"StreamingPipeline({' -> '.join(names)})"
