"""Finds plateau region by segmented regression."""

import numpy as np

__all__ = [
    "plateau_type2",
    "plateau_type3",
]


def _ols(Xi, Y):
    XT_X_inv = np.linalg.inv(Xi.T @ Xi)
    params = XT_X_inv @ (Xi.T @ Y)
    return params


def _segreg(x, Y, psi0, tol=1e-5, maxiter=30):
    r"""Segmented regression with one breakpoint.

    Parameters
    ----------
    x, Y : (M,) ndarray
        Data points.
    psi0 : scalar
        Initial guess for breakpoint coordinate.
    tol : float, default=1e-5
        Convergence tolerance.
    maxiter : int, default=30
        Force break after this iterations.

    Returns
    -------
    params : (4,) ndarray
        Estimated parameters: b0, b1, b2, psi.
    reached_max : bool
        Iteration is finished not by convergence but by reaching maximum iteration.
    """
    Xi = np.array(
        [
            np.ones_like(x),
            x,
            (x - psi0) * np.heaviside(x - psi0, 0),
            -np.heaviside(x - psi0, 0),
        ]
    ).T

    b0, b1, b2, gamma = _ols(Xi, Y)
    RSS = np.sum((Y - _segreg_predict(x, b0, b1, b2, psi0)) ** 2)

    psi_converged = False
    for _ in range(maxiter):
        RSS_new = RSS
        lamda = 1
        while True:
            psi0_new = psi0 + lamda * gamma / b2
            RSS_new = np.sum((Y - _segreg_predict(x, b0, b1, b2, psi0_new)) ** 2)
            lamda /= 2

            if (psi0_new <= x[0]) or (psi0_new >= x[-1]):
                # exceeded domain; make step size smaller
                continue
            if RSS_new >= RSS:
                # RSS not decreased; make step size smaller
                continue
            psi_converged = np.abs(psi0 - psi0_new) <= tol
            if psi_converged:
                break

        if not psi_converged:
            psi_converged = np.abs(psi0 - psi0_new) <= tol
        if psi_converged:
            psi0 = psi0_new
            reached_max = False
            break

        psi0 = psi0_new
        RSS = RSS_new
        Xi[:, 2] = (x - psi0) * np.heaviside(x - psi0, 0)
        Xi[:, 3] = -np.heaviside(x - psi0, 0)
        b0, b1, b2, gamma = _ols(Xi, Y)
    else:
        reached_max = True

    params = np.array([b0, b1, b2, psi0_new])
    return params, reached_max


def _segreg_predict(x, b0, b1, b2, psi):
    x = np.asarray(x)
    return b0 + b1 * x + b2 * (x - psi) * np.heaviside(x - psi, 0)


def plateau_type2(x, Ys, peaks, knees):
    """Find plateau for type 2 heavy edge profiles.

    Parameters
    ----------
    x : array of shape (M,)
        X grid of profiles.
    Ys : array of shape (N, M)
        Height data of N profiles.
    peaks, knees : arrays of shape (N,)
        X coordinates of peak point and knee point.

    Returns
    -------
    array of shape (N, 3)
        Plateau intercept, slope and boundary coordinates.

    Notes
    -----
    Plateau boundary is located by segmented regression.

    See Also
    --------
    landmarks_type2 : Detects *peaks* and *knees*.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import landmarks_type2, plateau_type2
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> lm = landmarks_type2(x, Ys, Ls, 32)
    >>> peaks, knees = lm[:, 0, 1:].T
    >>> plateau = plateau_type2(x, Ys, peaks, knees)
    >>> plateau.shape
    (22, 3)
    >>> plateau_x = np.stack([np.zeros(len(plateau)), plateau[:, 2]])
    >>> plateau_y = plateau[:, 0] + plateau_x * plateau[:, 1]
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, Ys.T, color="gray")
    ... plt.plot(plateau_x, plateau_y)
    """
    ret = []
    for Y, peak, knee in zip(Ys, peaks, knees):
        peak, knee = np.searchsorted(x, [peak, knee])
        (b0, b1, _, psi), _ = _segreg(x[:peak], Y[:peak], x[knee])
        ret.append([b0, b1, psi])
    return np.array(ret)


def plateau_type3(x, Ys, troughs, knees):
    """Find plateau for type 3 heavy edge profiles.

    Parameters
    ----------
    x : array of shape (M,)
        X grid of profiles.
    Ys : array of shape (N, M)
        Height data of N profiles.
    troughs, knees : arrays of shape (N,)
        X coordinates of trough point and knee point.

    Returns
    -------
    array of shape (N, 3)
        Plateau intercept, slope and boundary coordinates.

    Notes
    -----
    Plateau boundary is located by segmented regression.

    See Also
    --------
    landmarks_type3 : Detects *troughs* and *knees*.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge_landmarks import landmarks_type3, plateau_type3
    >>> with ProfileData(get_sample_path("Prep-Type3.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> lm = landmarks_type3(x, Ys, Ls, 32)
    >>> troughs, knees = lm[:, 0, 2:].T
    >>> plateau = plateau_type3(x, Ys, troughs, knees)
    >>> plateau.shape
    (35, 3)
    >>> plateau_x = np.stack([np.zeros(len(plateau)), plateau[:, 2]])
    >>> plateau_y = plateau[:, 0] + plateau_x * plateau[:, 1]
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, Ys.T, color="gray")
    ... plt.plot(plateau_x, plateau_y)
    """
    ret = []
    for Y, trough, knee in zip(Ys, troughs, knees):
        trough, knee = np.searchsorted(x, [trough, knee])
        (b0, b1, _, psi), _ = _segreg(x[:trough], Y[:trough], x[knee])
        ret.append([b0, b1, psi])
    return np.array(ret)
