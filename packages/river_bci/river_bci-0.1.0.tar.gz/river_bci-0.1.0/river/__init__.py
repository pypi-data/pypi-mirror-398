"""
River: Last-mile preprocessing for neural data to ML-ready tensors.

This package provides the `bridge` submodule which handles preprocessing
between raw neural data (from SpikeInterface, MNE, NWB) and ML-ready tensors.

Example usage:
    from river import bridge

    # One-liner spike preprocessing
    X = bridge.presets.willett_speech(spike_times, t_start=0, t_stop=100)

    # ECoG high-gamma extraction
    hg = bridge.ecog.high_gamma(raw_ecog, fs=1000)

    # Composable pipeline
    features = (
        bridge.Pipeline()
        .car()
        .notch(60)
        .high_gamma()
        .downsample(200)
        .sliding_zscore(30)
        .fit_transform(ecog_data, fs=1000)
    )
"""

__version__ = "0.1.0"

from river import bridge

__all__ = ["bridge", "__version__"]
