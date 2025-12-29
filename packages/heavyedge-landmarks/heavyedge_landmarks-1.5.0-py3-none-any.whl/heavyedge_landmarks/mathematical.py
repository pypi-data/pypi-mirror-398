"""Detect mathematical landmarks."""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, peak_prominences

__all__ = [
    "landmarks_type1",
    "landmarks_type2",
    "landmarks_type3",
]


def landmarks_type1(x, Ys, Ls, sigma):
    """Mathematical landmarks for type 1 heavy edge profiles.

    Type 1 heavy edge profiles is a smooth profile with negligible or absent peak.
    The following landmarks are detected:

    1. Contact point.
    2. Knee point between plateau and contact point.
    3. Maximum point.

    Parameters
    ----------
    x : array of shape (M,)
        X grid of profiles.
    Ys : array of shape (N, M)
        Height data of N profiles.
    Ls : array of shape (N,) and dtype=int
        Length of each profile.
    sigma : scalar
        Standard deviation of Gaussian filter for smoothing.

    Returns
    -------
    array of shape (N, 2, 3)
        X and Y coordinates of landmarks.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import landmarks_type1
    >>> with ProfileData(get_sample_path("Prep-Type1.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> lm = landmarks_type1(x, Ys, Ls, 32)
    >>> lm.shape
    (18, 2, 3)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, Ys.T, color="gray", alpha=0.5)
    ... plt.plot(*lm.transpose(1, 2, 0))
    """
    ret = []
    for Y, L in zip(Ys, Ls):
        idxs = _landmarks_type1(Y[:L], sigma)
        ret.append([x[idxs], Y[idxs]])
    return np.array(ret)


def _landmarks_type1(Y, sigma):
    cp = len(Y) - 1

    Y_smooth = gaussian_filter1d(Y, sigma)

    pts = np.column_stack([np.arange(len(Y_smooth)), Y_smooth])
    x, y = pts - pts[0], pts[-1] - pts[0]
    dists = x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
    slope = np.diff(dists)
    (extrema,) = np.nonzero(np.diff(np.sign(slope)))
    K_neg = extrema[slope[extrema] < 0]
    knee = K_neg[np.argmax(np.abs(dists[K_neg]))]

    maximum = np.argmax(Y_smooth)

    return np.array([cp, knee, maximum])


def landmarks_type2(x, Ys, Ls, sigma):
    """Mathematical landmarks for type 2 heavy edge profiles.

    Type 2 heavy edge profiles have heavy edge peak.
    The following landmarks are detected:

    1. Contact point.
    2. Peak point.
    3. Knee point between plateau and peak.

    Parameters
    ----------
    x : array of shape (M,)
        X grid of profiles.
    Ys : array of shape (N, M)
        Height data of N profiles.
    Ls : array of shape (N,) and dtype=int
        Length of each profile.
    sigma : scalar
        Standard deviation of Gaussian filter for smoothing.

    Returns
    -------
    array of shape (N, 2, 3)
        X and Y coordinates of landmarks.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import landmarks_type2
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> lm = landmarks_type2(x, Ys, Ls, 32)
    >>> lm.shape
    (22, 2, 3)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, Ys.T, color="gray", alpha=0.5)
    ... plt.plot(*lm.transpose(1, 2, 0))
    """
    ret = []
    for Y, L in zip(Ys, Ls):
        idxs = _landmarks_type2(Y[:L], sigma)
        ret.append([x[idxs], Y[idxs]])
    return np.array(ret)


def _landmarks_type2(Y, sigma):
    cp = len(Y) - 1

    Y_smooth = gaussian_filter1d(Y, sigma)
    peaks, _ = find_peaks(Y_smooth)
    peak = peaks[-1]

    Y_ = Y_smooth[:peak]
    pts = np.column_stack([np.arange(len(Y_)), Y_])
    x, y = pts - pts[0], pts[-1] - pts[0]
    dists = x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
    slope = np.diff(dists)
    (extrema,) = np.nonzero(np.diff(np.sign(slope)))
    K_pos = extrema[slope[extrema] > 0]
    knee = K_pos[np.argmax(np.abs(dists[K_pos]))]

    return np.array([cp, peak, knee])


def landmarks_type3(x, Ys, Ls, sigma):
    """Mathematical landmarks for type 3 heavy edge profiles.

    Type 3 heavy edge profiles have both peak and trough.
    The following landmarks are detected:

    1. Contact point.
    2. Peak point.
    3. Trough point.
    4. Knee point between plateau and trough.

    Parameters
    ----------
    x : array of shape (M,)
        X grid of profiles.
    Ys : array of shape (N, M)
        Height data of N profiles.
    Ls : array of shape (N,) and dtype=int
        Length of each profile.
    sigma : scalar
        Standard deviation of Gaussian filter for smoothing.

    Returns
    -------
    array of shape (N, 2, 4)
        X and Y coordinates of landmarks.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import landmarks_type3
    >>> with ProfileData(get_sample_path("Prep-Type3.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> lm = landmarks_type3(x, Ys, Ls, 32)
    >>> lm.shape
    (35, 2, 4)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, Ys.T, color="gray", alpha=0.5)
    ... plt.plot(*lm.transpose(1, 2, 0))
    """
    ret = []
    for Y, L in zip(Ys, Ls):
        idxs = _landmarks_type3(Y[:L], sigma)
        ret.append([x[idxs], Y[idxs]])
    return np.array(ret)


def _landmarks_type3(Y, sigma):
    cp = len(Y) - 1

    Y_smooth = gaussian_filter1d(Y, sigma)
    peaks, _ = find_peaks(Y_smooth)
    peak = peaks[-1]

    troughs, _ = find_peaks(-Y_smooth)
    troughs = troughs[troughs < peak]

    if len(troughs) > 0:
        prominences = peak_prominences(-Y_smooth, troughs)[0]
        most_prominent_idx = np.argmax(prominences)
        trough = troughs[most_prominent_idx]

        Y_ = Y_smooth[: int(trough) + 1]
        pts = np.column_stack([np.arange(len(Y_)), Y_])
        x, y = pts - pts[0], pts[-1] - pts[0]
        dists = x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
        slope = np.diff(dists)
        (extrema,) = np.nonzero(np.diff(np.sign(slope)))
        K_neg = extrema[slope[extrema] < 0]
        knee = K_neg[np.argmax(np.abs(dists[K_neg]))]

    else:
        Y_ = Y_smooth[:peak]
        pts = np.column_stack([np.arange(len(Y_)), Y_])
        x, y = pts - pts[0], pts[-1] - pts[0]
        dists = x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]
        slope = np.diff(dists)
        (extrema,) = np.nonzero(np.diff(np.sign(slope)))
        K_pos = extrema[slope[extrema] > 0]
        knee = trough = K_pos[np.argmax(np.abs(dists[K_pos]))]

    return np.array([cp, peak, trough, knee])
