"""
Data loading utilities for common neural data formats.

This module provides thin wrappers around common data formats to convert
them to simple numpy arrays and dictionaries that the rest of the package
can work with.

Supported formats:
- NWB (Neurodata Without Borders) - requires pynwb (optional)
- MAT (MATLAB .mat files) - uses h5py or scipy.io
- SpikeInterface sorting objects - requires spikeinterface (optional)
- MNE Raw/Epochs objects - requires mne (optional)

Functions:
    load_nwb_spikes: Load spike times from NWB file
    load_nwb_ecog: Load ECoG signals from NWB file
    load_mat: Load data from MATLAB .mat file
    from_spikeinterface: Convert SpikeInterface sorting to dict
    from_mne: Convert MNE Raw/Epochs to numpy
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

# Type alias for spike trains
SpikeTrains = Dict[Union[int, str], NDArray]


def load_nwb_spikes(
    nwb_path: Union[str, Path],
    unit_ids: Optional[List] = None,
) -> Tuple[SpikeTrains, Dict[str, Any]]:
    """
    Load spike times from an NWB file.

    Parameters
    ----------
    nwb_path : str or Path
        Path to the NWB file.
    unit_ids : list, optional
        Specific unit IDs to load. If None, loads all units.

    Returns
    -------
    spike_trains : dict
        Dictionary mapping unit IDs to spike time arrays (in seconds).
    metadata : dict
        Metadata about the units (electrode info, quality, etc.).

    Raises
    ------
    ImportError
        If pynwb is not installed.

    Examples
    --------
    >>> from river.bridge.io import load_nwb_spikes
    >>> spike_trains, meta = load_nwb_spikes("data.nwb")
    >>> len(spike_trains)
    128
    """
    try:
        from pynwb import NWBHDF5IO
    except ImportError:
        raise ImportError(
            "pynwb is required for NWB support. "
            "Install with: pip install pynwb"
        )

    nwb_path = Path(nwb_path)
    spike_trains: SpikeTrains = {}
    metadata: Dict[str, Any] = {}

    with NWBHDF5IO(str(nwb_path), "r") as io:
        nwbfile = io.read()

        # Check for units table
        if nwbfile.units is None:
            raise ValueError("NWB file does not contain units table")

        units_table = nwbfile.units

        # Get unit IDs
        if unit_ids is None:
            unit_ids = list(range(len(units_table)))

        # Extract spike times for each unit
        for uid in unit_ids:
            spike_times = units_table["spike_times"][uid]
            spike_trains[uid] = np.array(spike_times, dtype=np.float64)

        # Extract metadata
        metadata["n_units"] = len(unit_ids)
        if "quality" in units_table.colnames:
            metadata["quality"] = {
                uid: units_table["quality"][uid] for uid in unit_ids
            }

    return spike_trains, metadata


def load_nwb_ecog(
    nwb_path: Union[str, Path],
    electrode_ids: Optional[List[int]] = None,
    start_time: Optional[float] = None,
    stop_time: Optional[float] = None,
) -> Tuple[NDArray[np.floating], float, Dict[str, Any]]:
    """
    Load ECoG/LFP signals from an NWB file.

    Parameters
    ----------
    nwb_path : str or Path
        Path to the NWB file.
    electrode_ids : list, optional
        Specific electrode indices to load. If None, loads all.
    start_time : float, optional
        Start time in seconds. If None, starts from beginning.
    stop_time : float, optional
        Stop time in seconds. If None, loads until end.

    Returns
    -------
    signal : ndarray
        ECoG signal. Shape (n_samples, n_channels).
    fs : float
        Sampling frequency in Hz.
    metadata : dict
        Metadata about the electrodes.

    Raises
    ------
    ImportError
        If pynwb is not installed.

    Examples
    --------
    >>> from river.bridge.io import load_nwb_ecog
    >>> signal, fs, meta = load_nwb_ecog("data.nwb")
    >>> signal.shape
    (100000, 64)
    """
    try:
        from pynwb import NWBHDF5IO
    except ImportError:
        raise ImportError(
            "pynwb is required for NWB support. "
            "Install with: pip install pynwb"
        )

    nwb_path = Path(nwb_path)
    metadata: Dict[str, Any] = {}

    with NWBHDF5IO(str(nwb_path), "r") as io:
        nwbfile = io.read()

        # Find ECoG/LFP data in acquisition or processing
        ecog_data = None
        for name, ts in nwbfile.acquisition.items():
            if hasattr(ts, "data") and hasattr(ts, "rate"):
                ecog_data = ts
                break

        if ecog_data is None:
            raise ValueError("No suitable time series found in NWB file")

        fs = ecog_data.rate
        data = ecog_data.data[:]

        # Handle time slicing
        if start_time is not None or stop_time is not None:
            start_idx = int(start_time * fs) if start_time else 0
            stop_idx = int(stop_time * fs) if stop_time else len(data)
            data = data[start_idx:stop_idx]

        # Handle electrode selection
        if electrode_ids is not None:
            data = data[:, electrode_ids]

        signal = np.array(data, dtype=np.float64)

        # Extract metadata
        metadata["n_channels"] = signal.shape[1] if signal.ndim > 1 else 1
        metadata["duration_s"] = len(signal) / fs
        if hasattr(ecog_data, "electrodes"):
            metadata["electrode_info"] = "available"

    return signal, float(fs), metadata


def load_mat(
    mat_path: Union[str, Path],
    variables: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Load data from a MATLAB .mat file.

    Handles both v7.3 (HDF5-based) and older .mat formats.

    Parameters
    ----------
    mat_path : str or Path
        Path to the .mat file.
    variables : list, optional
        Specific variable names to load. If None, loads all.

    Returns
    -------
    data : dict
        Dictionary of loaded variables.

    Examples
    --------
    >>> from river.bridge.io import load_mat
    >>> data = load_mat("willett_data.mat")
    >>> data["spikePow"].shape
    (10000, 256)
    """
    mat_path = Path(mat_path)

    # Try h5py first (for v7.3 .mat files)
    try:
        import h5py

        with h5py.File(str(mat_path), "r") as f:
            if variables is None:
                variables = list(f.keys())

            data = {}
            for var in variables:
                if var in f:
                    item = f[var][:]
                    # Handle MATLAB column-major order
                    if item.ndim == 2:
                        item = item.T
                    data[var] = np.array(item)

            return data
    except (OSError, Exception):
        pass

    # Fall back to scipy.io for older .mat files
    try:
        from scipy.io import loadmat

        mat_data = loadmat(str(mat_path), squeeze_me=True, struct_as_record=False)

        # Filter out MATLAB metadata
        data = {
            k: v
            for k, v in mat_data.items()
            if not k.startswith("__")
        }

        if variables is not None:
            data = {k: v for k, v in data.items() if k in variables}

        return data
    except Exception as e:
        raise IOError(f"Failed to load {mat_path}: {e}")


def from_spikeinterface(
    sorting: Any,
    start_frame: int = 0,
    end_frame: Optional[int] = None,
) -> Tuple[SpikeTrains, float]:
    """
    Convert a SpikeInterface sorting object to spike trains dict.

    Parameters
    ----------
    sorting : spikeinterface.BaseSorting
        SpikeInterface sorting object.
    start_frame : int, optional
        Start frame. Default is 0.
    end_frame : int, optional
        End frame. If None, uses all frames.

    Returns
    -------
    spike_trains : dict
        Dictionary mapping unit IDs to spike times (in seconds).
    fs : float
        Sampling frequency.

    Raises
    ------
    ImportError
        If spikeinterface is not installed.

    Examples
    --------
    >>> from spikeinterface import load_extractor
    >>> from river.bridge.io import from_spikeinterface
    >>> sorting = load_extractor("sorting_folder")
    >>> spike_trains, fs = from_spikeinterface(sorting)
    """
    try:
        import spikeinterface as si
    except ImportError:
        raise ImportError(
            "spikeinterface is required for this function. "
            "Install with: pip install spikeinterface"
        )

    fs = sorting.get_sampling_frequency()
    unit_ids = sorting.get_unit_ids()

    spike_trains: SpikeTrains = {}
    for unit_id in unit_ids:
        spike_frames = sorting.get_unit_spike_train(
            unit_id, start_frame=start_frame, end_frame=end_frame
        )
        # Convert frames to seconds
        spike_trains[unit_id] = spike_frames / fs

    return spike_trains, float(fs)


def from_mne(
    mne_obj: Any,
    picks: Optional[Union[str, List]] = None,
) -> Tuple[NDArray[np.floating], float, List[str]]:
    """
    Convert MNE Raw or Epochs object to numpy array.

    Parameters
    ----------
    mne_obj : mne.io.Raw or mne.Epochs
        MNE data object.
    picks : str or list, optional
        Channel selection. Can be channel names, types ('eeg', 'ecog'),
        or indices. If None, uses all channels.

    Returns
    -------
    data : ndarray
        Data array. Shape (n_samples, n_channels) for Raw,
        or (n_epochs, n_samples, n_channels) for Epochs.
    fs : float
        Sampling frequency.
    ch_names : list
        Channel names.

    Raises
    ------
    ImportError
        If mne is not installed.

    Examples
    --------
    >>> import mne
    >>> from river.bridge.io import from_mne
    >>> raw = mne.io.read_raw_edf("data.edf")
    >>> data, fs, ch_names = from_mne(raw, picks='ecog')
    """
    try:
        import mne
    except ImportError:
        raise ImportError(
            "mne is required for this function. "
            "Install with: pip install mne"
        )

    # Get sampling frequency
    fs = mne_obj.info["sfreq"]

    # Handle picks
    if picks is not None:
        if isinstance(picks, str):
            picks = mne.pick_types(mne_obj.info, **{picks: True})
        mne_obj = mne_obj.copy().pick(picks)

    ch_names = mne_obj.ch_names

    # Extract data based on object type
    if isinstance(mne_obj, mne.io.BaseRaw):
        data = mne_obj.get_data().T  # Transpose to (n_samples, n_channels)
    elif isinstance(mne_obj, mne.Epochs):
        data = mne_obj.get_data()  # Shape: (n_epochs, n_channels, n_times)
        data = np.transpose(data, (0, 2, 1))  # Shape: (n_epochs, n_times, n_channels)
    else:
        raise TypeError(f"Unsupported MNE object type: {type(mne_obj)}")

    return data.astype(np.float64), float(fs), list(ch_names)


def to_nwb(
    nwb_path: Union[str, Path],
    signal: Optional[NDArray] = None,
    spike_trains: Optional[SpikeTrains] = None,
    fs: Optional[float] = None,
    session_description: str = "Neural data",
    identifier: Optional[str] = None,
) -> None:
    """
    Save data to NWB format.

    Parameters
    ----------
    nwb_path : str or Path
        Output path for NWB file.
    signal : ndarray, optional
        Continuous signal data. Shape (n_samples, n_channels).
    spike_trains : dict, optional
        Spike trains dict mapping unit IDs to spike times.
    fs : float, optional
        Sampling frequency (required if signal is provided).
    session_description : str, optional
        Description of the session.
    identifier : str, optional
        Unique identifier. If None, generates a UUID.

    Raises
    ------
    ImportError
        If pynwb is not installed.

    Examples
    --------
    >>> from river.bridge.io import to_nwb
    >>> to_nwb("output.nwb", signal=data, fs=1000)
    """
    try:
        from datetime import datetime

        from pynwb import NWBHDF5IO, NWBFile
        from pynwb.ecephys import ElectricalSeries
    except ImportError:
        raise ImportError(
            "pynwb is required for NWB export. "
            "Install with: pip install pynwb"
        )

    import uuid

    if identifier is None:
        identifier = str(uuid.uuid4())

    nwbfile = NWBFile(
        session_description=session_description,
        identifier=identifier,
        session_start_time=datetime.now(),
    )

    # Add signal data
    if signal is not None:
        if fs is None:
            raise ValueError("fs is required when saving signal data")

        # Create device and electrodes
        device = nwbfile.create_device(name="Neural Recording Device")

        nwbfile.add_electrode_column(name="label", description="electrode label")

        n_channels = signal.shape[1] if signal.ndim > 1 else 1
        for i in range(n_channels):
            nwbfile.add_electrode(
                x=0.0,
                y=0.0,
                z=0.0,
                imp=np.nan,
                location="unknown",
                filtering="none",
                group=nwbfile.create_electrode_group(
                    name=f"electrode_group_{i}",
                    description="electrode group",
                    device=device,
                    location="unknown",
                ),
                label=f"ch{i}",
            )

        electrodes = nwbfile.create_electrode_table_region(
            region=list(range(n_channels)),
            description="all electrodes",
        )

        ecog_series = ElectricalSeries(
            name="ECoG",
            data=signal,
            electrodes=electrodes,
            rate=fs,
            description="ECoG recording",
        )

        nwbfile.add_acquisition(ecog_series)

    # Add spike trains
    if spike_trains is not None:
        for unit_id, times in spike_trains.items():
            nwbfile.add_unit(spike_times=times)

    # Write file
    nwb_path = Path(nwb_path)
    with NWBHDF5IO(str(nwb_path), "w") as io:
        io.write(nwbfile)
