"""Within-sample scaling of landmarks."""

import numpy as np

__all__ = [
    "minmax",
]


def minmax(Xs):
    """Within-sample min-max scaling of landmarks.

    Parameters
    ----------
    Xs : array, shape (N, m, k)
        `N` configuration matrices of `k` landmarks in dimension `m`.

    Returns
    -------
    Xs_scaled : array, shape (N, m, k)
        Min-max scaled configuration matrices.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import pseudo_landmarks, minmax
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> Xs = pseudo_landmarks(x, Ys, Ls, 10)
    >>> Xs_scaled = minmax(Xs)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... fig = plt.figure()
    ... ax1 = fig.add_subplot(211)
    ... ax1.plot(*Xs.transpose(1, 2, 0))
    ... ax1.set_aspect("equal")
    ... ax1.set_title("Original")
    ... ax2 = fig.add_subplot(212)
    ... ax2.plot(*Xs_scaled.transpose(1, 2, 0))
    ... ax2.set_aspect("equal")
    ... ax2.set_title("Scaled")
    """
    _, m, _ = Xs.shape

    ret = np.empty_like(Xs)
    for i in range(m):
        coords = Xs[:, i, :]
        minval = coords.min(axis=1, keepdims=True)
        maxval = coords.max(axis=1, keepdims=True)

        ret[:, i, :] = (Xs[:, i, :] - minval) / (maxval - minval)
    return ret
