"""Locate pseudo-landmarks."""

import numpy as np

__all__ = [
    "pseudo_landmarks",
]


def pseudo_landmarks(x, Ys, Ls, k):
    """Sample pseudo-landmarks from edge profiles.

    Pseudo-landmarks are equidistantly sampled landmarks.

    Parameters
    ----------
    x : array of shape (M,)
        X grid of profiles.
    Ys : array of shape (N, M)
        Height data of N profiles.
    Ls : array of shape (N,) and dtype=int
        Length of each profile.
    k : int
        Number of landmarks to sample.

    Returns
    -------
    array of shape (N, 2, k)
        X and Y coordinates of landmarks.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import pseudo_landmarks
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> lm = pseudo_landmarks(x, Ys, Ls, 10)
    >>> lm.shape
    (22, 2, 10)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, Ys.T, color="gray", alpha=0.5)
    ... plt.plot(*lm.transpose(1, 2, 0))
    """
    ret = []
    for Y, L in zip(Ys, Ls):
        idxs = np.linspace(0, L - 1, k, dtype=int)
        ret.append([x[idxs], Y[idxs]])
    return np.array(ret)
