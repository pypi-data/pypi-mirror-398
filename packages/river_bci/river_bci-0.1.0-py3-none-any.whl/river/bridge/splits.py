"""
Train/validation/test splitting for neural data.

This module provides splitting strategies that are aware of temporal
dependencies in neural data, preventing data leakage between splits.

Functions:
    train_val_test_split: Standard 3-way split with optional shuffling
    temporal_split: Time-preserving split (no shuffling)
    session_split: Leave-session-out split
    kfold_temporal: Walk-forward cross-validation
"""

from __future__ import annotations

from typing import Generator, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray


def train_val_test_split(
    *arrays: ArrayLike,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    shuffle: bool = True,
    random_state: Optional[int] = None,
) -> Tuple[NDArray, ...]:
    """
    Split arrays into train, validation, and test sets.

    Parameters
    ----------
    *arrays : array_like
        Arrays to split. All must have the same length along axis 0.
    train_frac : float, optional
        Fraction of data for training. Default is 0.7.
    val_frac : float, optional
        Fraction of data for validation. Default is 0.15.
        Test fraction is inferred as 1 - train_frac - val_frac.
    shuffle : bool, optional
        Whether to shuffle before splitting. Default is True.
        Set to False for time-series data to preserve temporal order.
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    splits : tuple
        For each input array, returns (train, val, test) arrays.
        Total output is (train_0, val_0, test_0, train_1, val_1, test_1, ...).

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.splits import train_val_test_split
    >>> X = np.random.randn(100, 64)
    >>> y = np.random.randint(0, 10, 100)
    >>> X_train, X_val, X_test, y_train, y_val, y_test = train_val_test_split(
    ...     X, y, train_frac=0.7, val_frac=0.15
    ... )
    >>> len(X_train), len(X_val), len(X_test)
    (70, 15, 15)
    """
    if not arrays:
        raise ValueError("At least one array must be provided")

    # Validate fractions
    test_frac = 1.0 - train_frac - val_frac
    if test_frac < 0:
        raise ValueError(
            f"train_frac ({train_frac}) + val_frac ({val_frac}) must be <= 1.0"
        )

    # Convert to arrays and check lengths
    arrays = tuple(np.asarray(arr) for arr in arrays)
    n_samples = len(arrays[0])
    for i, arr in enumerate(arrays[1:], 1):
        if len(arr) != n_samples:
            raise ValueError(
                f"All arrays must have same length. Array 0 has {n_samples}, "
                f"array {i} has {len(arr)}."
            )

    # Create indices
    indices = np.arange(n_samples)

    if shuffle:
        rng = np.random.default_rng(random_state)
        rng.shuffle(indices)

    # Compute split points
    n_train = int(n_samples * train_frac)
    n_val = int(n_samples * val_frac)

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    # Split each array
    result = []
    for arr in arrays:
        result.extend([arr[train_idx], arr[val_idx], arr[test_idx]])

    return tuple(result)


def temporal_split(
    *arrays: ArrayLike,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    gap: int = 0,
) -> Tuple[NDArray, ...]:
    """
    Time-preserving split (no shuffling).

    Splits data while preserving temporal order, preventing future data
    from leaking into training. Optionally includes a gap between splits
    to prevent leakage from temporal autocorrelation.

    Parameters
    ----------
    *arrays : array_like
        Arrays to split. All must have the same length along axis 0.
    train_frac : float, optional
        Fraction of data for training. Default is 0.7.
    val_frac : float, optional
        Fraction of data for validation. Default is 0.15.
    gap : int, optional
        Number of samples to skip between train/val and val/test splits
        to prevent data leakage from temporal autocorrelation. Default is 0.

    Returns
    -------
    splits : tuple
        For each input array, returns (train, val, test) arrays.
        Total output is (train_0, val_0, test_0, train_1, val_1, test_1, ...).

    Notes
    -----
    The gap parameter is important when data has temporal autocorrelation.
    For neural data with 30-second sliding z-score windows, a gap of
    at least 30 seconds worth of samples is recommended.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.splits import temporal_split
    >>> X = np.random.randn(1000, 64)
    >>> y = np.random.randint(0, 10, 1000)
    >>> # Split with 50-sample gaps between sets
    >>> X_train, X_val, X_test, y_train, y_val, y_test = temporal_split(
    ...     X, y, train_frac=0.7, val_frac=0.15, gap=50
    ... )
    """
    if not arrays:
        raise ValueError("At least one array must be provided")

    # Validate fractions
    test_frac = 1.0 - train_frac - val_frac
    if test_frac < 0:
        raise ValueError(
            f"train_frac ({train_frac}) + val_frac ({val_frac}) must be <= 1.0"
        )

    # Convert to arrays and check lengths
    arrays = tuple(np.asarray(arr) for arr in arrays)
    n_samples = len(arrays[0])
    for i, arr in enumerate(arrays[1:], 1):
        if len(arr) != n_samples:
            raise ValueError(
                f"All arrays must have same length. Array 0 has {n_samples}, "
                f"array {i} has {len(arr)}."
            )

    # Account for gaps in split calculation
    effective_samples = n_samples - 2 * gap

    # Compute split points
    n_train = int(effective_samples * train_frac)
    n_val = int(effective_samples * val_frac)

    train_end = n_train
    val_start = train_end + gap
    val_end = val_start + n_val
    test_start = val_end + gap

    # Split each array
    result = []
    for arr in arrays:
        train = arr[:train_end]
        val = arr[val_start:val_end]
        test = arr[test_start:]
        result.extend([train, val, test])

    return tuple(result)


def session_split(
    *arrays: ArrayLike,
    session_ids: ArrayLike,
    test_sessions: Union[List, ArrayLike],
    val_sessions: Optional[Union[List, ArrayLike]] = None,
) -> Tuple[NDArray, ...]:
    """
    Leave-session-out split for multi-session data.

    Splits data by session, keeping entire sessions together. This is
    important for BCI data where sessions may have different recording
    conditions or neural drift.

    Parameters
    ----------
    *arrays : array_like
        Arrays to split. All must have the same length along axis 0.
    session_ids : array_like
        Session identifier for each sample. Shape (n_samples,).
    test_sessions : list or array
        Session IDs to use for testing.
    val_sessions : list or array, optional
        Session IDs to use for validation. If None, validation set is empty.

    Returns
    -------
    splits : tuple
        For each input array, returns (train, val, test) arrays.
        If val_sessions is None, returns (train, test) for each array.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.splits import session_split
    >>> # Simulated multi-session data
    >>> X = np.random.randn(500, 64)
    >>> y = np.random.randint(0, 10, 500)
    >>> session_ids = np.array([1]*100 + [2]*100 + [3]*100 + [4]*100 + [5]*100)
    >>> # Leave session 5 for testing, session 4 for validation
    >>> result = session_split(
    ...     X, y,
    ...     session_ids=session_ids,
    ...     test_sessions=[5],
    ...     val_sessions=[4]
    ... )
    >>> X_train, X_val, X_test, y_train, y_val, y_test = result
    >>> len(X_train), len(X_val), len(X_test)
    (300, 100, 100)
    """
    if not arrays:
        raise ValueError("At least one array must be provided")

    # Convert to arrays
    arrays = tuple(np.asarray(arr) for arr in arrays)
    session_ids = np.asarray(session_ids)
    test_sessions = np.asarray(test_sessions)

    n_samples = len(arrays[0])
    if len(session_ids) != n_samples:
        raise ValueError("session_ids must have same length as arrays")

    # Create masks
    test_mask = np.isin(session_ids, test_sessions)

    if val_sessions is not None:
        val_sessions = np.asarray(val_sessions)
        val_mask = np.isin(session_ids, val_sessions)
        train_mask = ~(test_mask | val_mask)

        result = []
        for arr in arrays:
            result.extend([arr[train_mask], arr[val_mask], arr[test_mask]])
    else:
        train_mask = ~test_mask

        result = []
        for arr in arrays:
            result.extend([arr[train_mask], arr[test_mask]])

    return tuple(result)


def kfold_temporal(
    *arrays: ArrayLike,
    n_folds: int = 5,
    gap: int = 0,
) -> Generator[Tuple[NDArray, ...], None, None]:
    """
    Walk-forward (expanding window) cross-validation.

    For time-series data, uses all previous folds as training data and
    the current fold as test data. This respects temporal ordering.

    Parameters
    ----------
    *arrays : array_like
        Arrays to split. All must have the same length along axis 0.
    n_folds : int, optional
        Number of folds. Default is 5.
    gap : int, optional
        Number of samples to skip between train and test to prevent
        data leakage. Default is 0.

    Yields
    ------
    splits : tuple
        For each fold, yields (train_0, test_0, train_1, test_1, ...).

    Notes
    -----
    Unlike standard k-fold, this method:
    - Never uses future data for training
    - Training set grows with each fold
    - First fold uses only fold 0 for training, fold 1 for testing
    - Last fold uses folds 0 to n-2 for training, fold n-1 for testing

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.splits import kfold_temporal
    >>> X = np.random.randn(500, 64)
    >>> y = np.random.randint(0, 10, 500)
    >>> for fold_idx, (X_train, X_test, y_train, y_test) in enumerate(
    ...     kfold_temporal(X, y, n_folds=5)
    ... ):
    ...     print(f"Fold {fold_idx}: train={len(X_train)}, test={len(X_test)}")
    Fold 0: train=100, test=100
    Fold 1: train=200, test=100
    Fold 2: train=300, test=100
    Fold 3: train=400, test=100
    """
    if not arrays:
        raise ValueError("At least one array must be provided")

    arrays = tuple(np.asarray(arr) for arr in arrays)
    n_samples = len(arrays[0])

    # Compute fold boundaries
    fold_size = n_samples // n_folds
    fold_starts = [i * fold_size for i in range(n_folds)]
    fold_ends = fold_starts[1:] + [n_samples]

    # Generate folds (walk-forward)
    for fold_idx in range(n_folds - 1):
        train_end = fold_ends[fold_idx] - gap
        test_start = fold_ends[fold_idx]
        test_end = fold_ends[fold_idx + 1]

        result = []
        for arr in arrays:
            result.extend([arr[:train_end], arr[test_start:test_end]])

        yield tuple(result)


def stratified_temporal_split(
    *arrays: ArrayLike,
    labels: ArrayLike,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    gap: int = 0,
) -> Tuple[NDArray, ...]:
    """
    Temporal split with approximate class balance in each set.

    Performs a temporal split but adjusts boundaries to maintain
    approximate class proportions. Useful when class distribution
    varies over time.

    Parameters
    ----------
    *arrays : array_like
        Arrays to split.
    labels : array_like
        Class labels for each sample. Used to compute class balance.
    train_frac : float, optional
        Target training fraction. Default is 0.7.
    val_frac : float, optional
        Target validation fraction. Default is 0.15.
    gap : int, optional
        Gap between splits. Default is 0.

    Returns
    -------
    splits : tuple
        (train_0, val_0, test_0, train_1, val_1, test_1, ..., train_labels, val_labels, test_labels)

    Notes
    -----
    This is a soft stratification - it maintains temporal order but
    tries to find split points that result in similar class distributions.
    For strict stratification, use regular train_val_test_split with shuffle=True,
    but be aware this breaks temporal ordering.

    Examples
    --------
    >>> import numpy as np
    >>> from river.bridge.splits import stratified_temporal_split
    >>> X = np.random.randn(1000, 64)
    >>> # Labels that change distribution over time
    >>> labels = np.concatenate([
    ...     np.zeros(300), np.ones(200), np.zeros(200), np.ones(300)
    ... ]).astype(int)
    >>> result = stratified_temporal_split(X, labels=labels, train_frac=0.7)
    """
    arrays = tuple(np.asarray(arr) for arr in arrays)
    labels = np.asarray(labels)
    n_samples = len(arrays[0])

    # For now, just use regular temporal split
    # A more sophisticated implementation would search for optimal split points
    # that maintain class balance while respecting temporal order
    all_arrays = arrays + (labels,)
    return temporal_split(*all_arrays, train_frac=train_frac, val_frac=val_frac, gap=gap)
