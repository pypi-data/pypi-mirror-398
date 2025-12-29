"""Converts configuration matrices to pre-shapes.

.. note::

    Helmert sub-matrices are LRU-cached.
    The number of most recent calls can be set by the environment variable
    `HEAVYEDGE_LANDMARKS_CACHE_SIZE`, which defaults to 4.
"""

import os
import warnings
from functools import lru_cache

import numpy as np
from scipy.linalg import cho_factor, cho_solve, helmert

__all__ = [
    "preshape",
    "dual_preshape",
    "preshape_dual",
]


def preshape(Xs):
    """Convert configuration matrices to pre-shapes.

    Conversion is done using the Helmert sub-matrix.

    Parameters
    ----------
    Xs : array, shape (N, m, k)
        `N` configuration matrices of `k` landmarks in dimension `m`.

    Returns
    -------
    Zs : array, shape (N, m, k-1)
        `N` pre-shape matrices.

    See Also
    --------
    dual_preshape
        Pre-shape in configuration matrix space.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import pseudo_landmarks, preshape
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> Zs = preshape(pseudo_landmarks(x, Ys, Ls, 10))
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(*Zs.transpose(1, 2, 0))
    """
    _, _, k = Xs.shape
    H = _helmert(k)
    HX = np.inner(Xs, H)
    scale = np.linalg.norm(HX, axis=(1, 2), keepdims=True)
    Zs = HX / scale
    return Zs


def dual_preshape(Xs):
    """Pre-shape in configuration matrix space.

    Conversion is done using the Helmert sub-matrix and its hat matrix.

    .. deprecated:: 1.2
        This function will be removed in HeavyEdge-Landmarks 2.0,
        Use :func:`preshape_dual` instead.

    Parameters
    ----------
    Xs : array, shape (N, m, k)
        `N` configuration matrices of `k` landmarks in dimension `m`.

    Returns
    -------
    Zs : array, shape (N, m, k)
        `N` pre-shape matrices.

    See Also
    --------
    preshape
        Pre-shape in its original space.

    Notes
    -----
    Because location and scale information is lost during the pre-shaping process,
    *Zs* is rank-deficient and has unit norm.
    """
    warnings.warn(
        "dual_preshape() is deprecated since HeavyEdge-Landmarks 1.2 "
        "and will be removed in 2.0. "
        "Use preshape_dual() instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    _, _, k = Xs.shape
    H = _helmert(k)
    HX = np.inner(Xs, H)
    scale = np.linalg.norm(HX, axis=(1, 2), keepdims=True)
    Zs = HX / scale
    hat = _helmert_hat(k)
    return np.inner(Zs, hat)


def preshape_dual(Zs):
    """Map pre-shape into configuration matrix space.

    Conversion is done using the Helmert sub-matrix and its hat matrix.

    Parameters
    ----------
    Zs : array, shape (N, m, k-1)
        `N` pre-shape matrices.

    Returns
    -------
    Zs_dual : array, shape (N, m, k)
        *Zs* in configuration matrix space.

    See Also
    --------
    preshape
        Pre-shape in its original space.

    Notes
    -----
    Because location and scale information is lost during the pre-shaping process,
    *Zs_dual* is rank-deficient and has unit norm.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import pseudo_landmarks, preshape, preshape_dual
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> Zs = preshape(pseudo_landmarks(x, Ys, Ls, 10))
    >>> Zs_dual = preshape_dual(Zs)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(*Zs_dual.transpose(1, 2, 0))
    """
    _, _, k_minus_one = Zs.shape
    k = k_minus_one + 1
    hat = _helmert_hat(k)
    return np.inner(Zs, hat)


CACHE_SIZE = os.environ.get("HEAVYEDGE_LANDMARKS_CACHE_SIZE")
if CACHE_SIZE is not None:
    CACHE_SIZE = int(CACHE_SIZE)
else:
    CACHE_SIZE = 4


@lru_cache(maxsize=CACHE_SIZE)
def _helmert(k):
    return helmert(k)


@lru_cache(maxsize=CACHE_SIZE)
def _helmert_hat(k):
    H = helmert(k)
    # Efficient inversion (H.T @ inv(H @ H.T))
    return H.T @ cho_solve(cho_factor(H @ H.T), np.eye(H.shape[0]))
