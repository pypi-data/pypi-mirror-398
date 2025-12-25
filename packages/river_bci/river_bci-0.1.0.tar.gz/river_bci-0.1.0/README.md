# river_bci

Last-mile preprocessing for neural data to ML-ready tensors.

```python
from river import bridge

# One-liner spike preprocessing (Willett 2023 style)
X = bridge.presets.willett_speech(raw_signal, fs=30000)

# ECoG high-gamma extraction
hg = bridge.ecog.high_gamma(ecog_data, fs=1000)

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
```

## Installation

```bash
pip install river_bci
```

## Modules

- **spikes**: Spike train processing (binning, smoothing, threshold crossings)
- **ecog**: ECoG/LFP processing (filtering, high-gamma extraction)
- **normalize**: Normalization methods (z-score, sliding z-score, robust)
- **epoch**: Trial epoching and windowing
- **splits**: Train/val/test splitting with temporal awareness
- **pipeline**: Composable preprocessing pipelines
- **presets**: Published paper preprocessing presets (Willett, Chang lab, NLB)
- **streaming**: Real-time streaming processors
- **io**: Data loading for NWB, MAT, SpikeInterface, MNE
