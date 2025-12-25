"""
Bridge: Neural data preprocessing for BCI research.

Submodules:
    - spikes: Spike train processing (binning, smoothing, threshold crossings)
    - ecog: ECoG/LFP processing (filtering, high-gamma extraction)
    - normalize: Normalization methods (z-score, sliding z-score, robust)
    - epoch: Trial epoching and windowing
    - splits: Train/val/test splitting with temporal awareness
    - pipeline: Composable preprocessing pipelines
    - presets: Published paper preprocessing presets
    - io: Data loading utilities for NWB, MAT, SpikeInterface, MNE
    - streaming: Real-time streaming processors
"""

from river.bridge import ecog, epoch, io, normalize, presets, spikes, splits, streaming
from river.bridge.pipeline import Pipeline

__all__ = [
    "spikes",
    "ecog",
    "normalize",
    "epoch",
    "splits",
    "pipeline",
    "presets",
    "io",
    "streaming",
    "Pipeline",
]
