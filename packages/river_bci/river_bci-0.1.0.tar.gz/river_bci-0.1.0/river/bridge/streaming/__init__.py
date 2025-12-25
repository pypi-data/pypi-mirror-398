"""
Streaming: Real-time neural data processing.

This module provides stateful processors for real-time BCI applications.
Each processor maintains internal state and processes data chunk-by-chunk.

Classes:
    - RingBuffer: Circular buffer for maintaining sample history
    - StreamingFilter: Causal IIR filtering with state preservation
    - StreamingHighGamma: Real-time high-gamma envelope extraction
    - StreamingZScore: Online z-score with exponential moving average
    - StreamingBinner: Accumulate samples and emit binned counts/rates
    - StreamingSmooth: Causal Gaussian smoothing
    - StreamingPipeline: Chain multiple streaming processors
"""

from river.bridge.streaming.buffers import RingBuffer
from river.bridge.streaming.features import StreamingBinner, StreamingHighGamma
from river.bridge.streaming.filters import StreamingFilter
from river.bridge.streaming.normalize import StreamingZScore
from river.bridge.streaming.pipeline import StreamingPipeline
from river.bridge.streaming.smooth import StreamingSmooth

__all__ = [
    "RingBuffer",
    "StreamingFilter",
    "StreamingHighGamma",
    "StreamingZScore",
    "StreamingBinner",
    "StreamingSmooth",
    "StreamingPipeline",
]
