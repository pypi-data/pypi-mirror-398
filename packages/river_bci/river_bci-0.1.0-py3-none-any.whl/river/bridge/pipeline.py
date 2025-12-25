"""
Composable preprocessing pipelines for neural data.

This module provides a Pipeline class that allows chaining multiple
preprocessing steps with a fluent API. Pipelines track sampling rate
changes through downsampling steps.

Classes:
    Pipeline: Composable preprocessing pipeline with fluent API
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray


class Pipeline:
    """
    Composable preprocessing pipeline for neural data.

    Supports both explicit step addition and fluent API shortcuts.
    Tracks sampling rate through downsampling operations.

    Parameters
    ----------
    realtime : bool, optional
        If True, uses causal processing where applicable.
        Default is False.

    Examples
    --------
    Method 1: Explicit step addition

    >>> from river.bridge import Pipeline
    >>> from river.bridge.ecog import notch_filter, high_gamma
    >>> from river.bridge.normalize import sliding_zscore
    >>> pipe = Pipeline()
    >>> pipe.add("notch", notch_filter, freqs=60)
    >>> pipe.add("hg", high_gamma)
    >>> pipe.add("norm", sliding_zscore, window_s=30)
    >>> features = pipe.fit_transform(raw_data, fs=1000)

    Method 2: Fluent API

    >>> features = (
    ...     Pipeline()
    ...     .car()
    ...     .notch(60)
    ...     .high_gamma()
    ...     .downsample(200)
    ...     .sliding_zscore(30)
    ...     .fit_transform(raw_data, fs=1000)
    ... )
    """

    def __init__(self, realtime: bool = False):
        self._steps: List[Dict[str, Any]] = []
        self._realtime = realtime
        self._current_fs: Optional[float] = None

    def add(
        self,
        name: str,
        func: Callable,
        **params: Any,
    ) -> "Pipeline":
        """
        Add a processing step to the pipeline.

        Parameters
        ----------
        name : str
            Name of the step (for debugging/inspection).
        func : callable
            Processing function. Must accept data as first argument.
        **params
            Additional parameters to pass to the function.

        Returns
        -------
        self : Pipeline
            Returns self for method chaining.
        """
        self._steps.append(
            {
                "name": name,
                "func": func,
                "params": params,
            }
        )
        return self

    def fit_transform(
        self,
        data: ArrayLike,
        fs: float,
    ) -> NDArray[np.floating]:
        """
        Apply all pipeline steps to the data.

        Parameters
        ----------
        data : array_like
            Input data. Shape (n_samples,) or (n_samples, n_channels).
        fs : float
            Sampling frequency in Hz.

        Returns
        -------
        transformed : ndarray
            Transformed data.
        """
        data = np.asarray(data, dtype=np.float64)
        self._current_fs = fs

        for step in self._steps:
            func = step["func"]
            params = step["params"].copy()

            # Inject fs if the function expects it
            if "fs" not in params:
                # Check if function signature includes fs
                import inspect

                sig = inspect.signature(func)
                if "fs" in sig.parameters:
                    params["fs"] = self._current_fs

            # Inject realtime if applicable
            if "realtime" not in params:
                import inspect

                sig = inspect.signature(func)
                if "realtime" in sig.parameters:
                    params["realtime"] = self._realtime

            # Call the function
            result = func(data, **params)

            # Handle functions that return (data, new_fs) tuples
            if isinstance(result, tuple) and len(result) == 2:
                data, self._current_fs = result
            else:
                data = result

        return data

    def transform(self, data: ArrayLike, fs: float) -> NDArray[np.floating]:
        """Alias for fit_transform (no fitting needed for these transforms)."""
        return self.fit_transform(data, fs)

    @property
    def fs(self) -> Optional[float]:
        """Current sampling frequency after all transformations."""
        return self._current_fs

    @property
    def steps(self) -> List[str]:
        """Names of all pipeline steps."""
        return [s["name"] for s in self._steps]

    def __repr__(self) -> str:
        steps_str = " -> ".join(self.steps) if self._steps else "(empty)"
        return f"Pipeline({steps_str})"

    # =========================================================================
    # Fluent API shortcuts
    # =========================================================================

    def car(self, exclude_channels: Optional[list] = None) -> "Pipeline":
        """
        Add common average reference step.

        Parameters
        ----------
        exclude_channels : list, optional
            Channel indices to exclude from reference.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.ecog import common_average_reference

        return self.add(
            "car", common_average_reference, exclude_channels=exclude_channels
        )

    def notch(
        self,
        freqs: Union[float, list] = 60.0,
        harmonics: int = 3,
        q: float = 30.0,
    ) -> "Pipeline":
        """
        Add notch filter step.

        Parameters
        ----------
        freqs : float or list, optional
            Base frequency to remove. Default is 60.0 Hz.
        harmonics : int, optional
            Number of harmonics. Default is 3.
        q : float, optional
            Quality factor. Default is 30.0.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.ecog import notch_filter

        return self.add("notch", notch_filter, freqs=freqs, harmonics=harmonics, q=q)

    def bandpass(
        self,
        low: float,
        high: float,
        order: int = 4,
    ) -> "Pipeline":
        """
        Add bandpass filter step.

        Parameters
        ----------
        low : float
            Low cutoff frequency in Hz.
        high : float
            High cutoff frequency in Hz.
        order : int, optional
            Filter order. Default is 4.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.ecog import bandpass as bp

        return self.add("bandpass", bp, low=low, high=high, order=order)

    def high_gamma(
        self,
        freq_range: Tuple[float, float] = (70, 150),
        method: Literal["hilbert", "multiband"] = "hilbert",
        n_bands: int = 8,
    ) -> "Pipeline":
        """
        Add high-gamma extraction step.

        Parameters
        ----------
        freq_range : tuple, optional
            Frequency range. Default is (70, 150) Hz.
        method : {'hilbert', 'multiband'}, optional
            Extraction method. Default is 'hilbert'.
        n_bands : int, optional
            Number of sub-bands for multiband. Default is 8.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.ecog import high_gamma as hg

        return self.add(
            "high_gamma", hg, freq_range=freq_range, method=method, n_bands=n_bands
        )

    def extract_bands(
        self,
        bands: Optional[Dict[str, Tuple[float, float]]] = None,
        method: Literal["hilbert", "power"] = "hilbert",
    ) -> "Pipeline":
        """
        Add multi-band extraction step.

        Parameters
        ----------
        bands : dict, optional
            Band definitions. If None, uses standard bands.
        method : {'hilbert', 'power'}, optional
            Extraction method. Default is 'hilbert'.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.ecog import extract_bands as eb

        # Wrapper to convert dict output to array
        def extract_bands_array(
            data: ArrayLike,
            fs: float,
            bands: Optional[Dict] = None,
            method: str = "hilbert",
            realtime: bool = False,
        ) -> NDArray:
            result = eb(data, fs, bands=bands, method=method, realtime=realtime)
            # Stack bands along last axis
            return np.stack(list(result.values()), axis=-1)

        return self.add("extract_bands", extract_bands_array, bands=bands, method=method)

    def downsample(self, target_fs: float = 200.0) -> "Pipeline":
        """
        Add downsampling step.

        Parameters
        ----------
        target_fs : float, optional
            Target sampling rate. Default is 200.0 Hz.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.ecog import downsample as ds

        return self.add("downsample", ds, target_fs=target_fs)

    def zscore(self, axis: int = 0, eps: float = 1e-8) -> "Pipeline":
        """
        Add z-score normalization step.

        Parameters
        ----------
        axis : int, optional
            Axis for normalization. Default is 0.
        eps : float, optional
            Small constant for numerical stability. Default is 1e-8.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.normalize import zscore as zs

        return self.add("zscore", zs, axis=axis, eps=eps)

    def sliding_zscore(
        self,
        window_s: float = 30.0,
        eps: float = 1e-8,
    ) -> "Pipeline":
        """
        Add sliding window z-score step.

        Parameters
        ----------
        window_s : float, optional
            Window size in seconds. Default is 30.0.
        eps : float, optional
            Small constant for numerical stability. Default is 1e-8.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.normalize import sliding_zscore as szs

        return self.add("sliding_zscore", szs, window_s=window_s, eps=eps)

    def robust_zscore(self, axis: int = 0, eps: float = 1e-8) -> "Pipeline":
        """
        Add robust z-score (median/MAD) step.

        Parameters
        ----------
        axis : int, optional
            Axis for normalization. Default is 0.
        eps : float, optional
            Small constant for numerical stability. Default is 1e-8.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.normalize import robust_zscore as rzs

        return self.add("robust_zscore", rzs, axis=axis, eps=eps)

    def soft_normalize(self, norm_constant: float) -> "Pipeline":
        """
        Add soft normalization step.

        Parameters
        ----------
        norm_constant : float
            Normalization constant.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.normalize import soft_normalize as sn

        return self.add("soft_normalize", sn, norm_constant=norm_constant)

    def smooth(
        self,
        sigma_ms: float = 50.0,
        bin_size_ms: float = 20.0,
        causal: bool = False,
    ) -> "Pipeline":
        """
        Add Gaussian smoothing step.

        Parameters
        ----------
        sigma_ms : float, optional
            Smoothing sigma in ms. Default is 50.0.
        bin_size_ms : float, optional
            Bin size in ms. Default is 20.0.
        causal : bool, optional
            Use causal smoothing. Default is False.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.spikes import smooth_rates

        if self._realtime:
            causal = True

        return self.add(
            "smooth", smooth_rates, sigma_ms=sigma_ms, bin_size_ms=bin_size_ms, causal=causal
        )

    def bin_spikes(
        self,
        bin_size_ms: float = 20.0,
        output: Literal["count", "rate"] = "rate",
    ) -> "Pipeline":
        """
        Add spike binning step (for spike trains, not continuous data).

        Parameters
        ----------
        bin_size_ms : float, optional
            Bin size in ms. Default is 20.0.
        output : {'count', 'rate'}, optional
            Output type. Default is 'rate'.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.spikes import bin_spike_trains

        return self.add("bin_spikes", bin_spike_trains, bin_size_ms=bin_size_ms, output=output)

    def spike_band_power(
        self,
        bin_size_ms: float = 20.0,
        freq_range: Tuple[float, float] = (300, 3000),
    ) -> "Pipeline":
        """
        Add spike band power extraction step.

        Parameters
        ----------
        bin_size_ms : float, optional
            Bin size in ms. Default is 20.0.
        freq_range : tuple, optional
            Frequency range. Default is (300, 3000) Hz.

        Returns
        -------
        self : Pipeline
        """
        from river.bridge.spikes import spike_band_power as sbp

        return self.add(
            "spike_band_power", sbp, bin_size_ms=bin_size_ms, freq_range=freq_range
        )

    def custom(self, name: str, func: Callable, **params: Any) -> "Pipeline":
        """
        Add a custom processing step.

        Parameters
        ----------
        name : str
            Step name.
        func : callable
            Processing function.
        **params
            Function parameters.

        Returns
        -------
        self : Pipeline
        """
        return self.add(name, func, **params)


def compose(*pipelines: Pipeline, realtime: bool = False) -> Pipeline:
    """
    Compose multiple pipelines into one.

    Parameters
    ----------
    *pipelines : Pipeline
        Pipelines to compose (applied in order).
    realtime : bool, optional
        Override realtime setting for composed pipeline.

    Returns
    -------
    composed : Pipeline
        New pipeline with all steps from input pipelines.

    Examples
    --------
    >>> from river.bridge.pipeline import Pipeline, compose
    >>> filter_pipe = Pipeline().car().notch(60)
    >>> feature_pipe = Pipeline().high_gamma().downsample(200)
    >>> full_pipe = compose(filter_pipe, feature_pipe)
    """
    result = Pipeline(realtime=realtime)
    for pipe in pipelines:
        for step in pipe._steps:
            result._steps.append(step.copy())
    return result
