"""Numerical integration utilities for group sequential design.

These routines port the canonical grid generation and update algorithms
from the original C and C++ implementations in gsDesign.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray

SQRT_2PI: float = float(np.sqrt(2.0 * np.pi))
FloatArray = NDArray[np.float64]


def _normal_pdf(x: FloatArray) -> FloatArray:
    """Evaluate the standard normal density at the supplied points."""
    squared = np.square(x, dtype=np.float64)
    return np.exp(-0.5 * squared) / SQRT_2PI


def _as_float64(array: Iterable[float]) -> FloatArray:
    """Convert an iterable of floats to a contiguous float64 NumPy array."""
    return np.asarray(array, dtype=np.float64)


def gridpts(
    r: int = 18,
    mu: float = 0.0,
    a: float = -np.inf,
    b: float = np.inf,
) -> tuple[FloatArray, FloatArray]:
    """
    Construct Simpson's rule grid points for canonical normal integration.

    Args:
        r: Number of odd grid points defining the Simpson stencil (at least 2).
        mu: Mean shift applied to the canonical grid before truncation.
        a: Lower integration limit; use ``-numpy.inf`` for no truncation.
        b: Upper integration limit; use ``numpy.inf`` for no truncation.

    Returns:
        A tuple containing grid locations ``z`` and Simpson weights ``w``.
    """

    if r < 2:
        raise ValueError("r must be at least 2 for Simpson integration.")
    if not a < b:
        raise ValueError("Lower limit 'a' must be strictly less than upper limit 'b'.")

    base_count = 6 * r - 1
    x = np.empty(base_count, dtype=np.float64)
    odd_indices = np.arange(r - 1, dtype=np.int64)
    right_indices = 6 * r - 2 - odd_indices
    tmp = 3.0 + 4.0 * np.log(r / (odd_indices.astype(np.float64) + 1.0))
    x[odd_indices] = mu - tmp
    x[right_indices] = mu + tmp

    mid_indices = np.arange(r - 1, 5 * r, dtype=np.int64)
    x[mid_indices] = mu - 3.0 + 3.0 * (mid_indices - (r - 1)) / (2.0 * r)

    if np.nanmin(x) < a:
        x = x[x > a]
        x = np.insert(x, 0, a)
    if np.nanmax(x) > b:
        x = x[x < b]
        x = np.append(x, b)

    m = x.size
    if m == 1:
        return x.astype(np.float64), np.ones(1, dtype=np.float64)

    z = np.empty(2 * m - 1, dtype=np.float64)
    w = np.empty(2 * m - 1, dtype=np.float64)

    odd_positions = np.arange(0, 2 * m - 1, 2)
    even_positions = np.arange(1, 2 * m - 1, 2)

    z[odd_positions] = x
    z[even_positions] = 0.5 * (x[:-1] + x[1:])

    w[odd_positions[0]] = x[1] - x[0]
    if m > 2:
        w[odd_positions[1:-1]] = x[2:] - x[:-2]
    w[odd_positions[-1]] = x[-1] - x[-2]
    w[even_positions] = 4.0 * (x[1:] - x[:-1])
    w /= 6.0

    return z, w


def h1(
    r: int = 18,
    theta: float = 0.0,
    info: float = 1.0,
    a: float = -np.inf,
    b: float = np.inf,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """
    Initialize the density grid for the first group sequential analysis.

    Args:
        r: Number of odd grid points defining the Simpson stencil (at least 2).
        theta: Canonical drift parameter for the analysis.
        info: Fisher information at the analysis; must be positive.
        a: Lower integration limit; use ``-numpy.inf`` for no truncation.
        b: Upper integration limit; use ``numpy.inf`` for no truncation.

    Returns:
        A tuple of arrays ``(z, w, h)`` ready for recursive integration.
    """

    if info <= 0:
        raise ValueError("Information 'info' must be positive.")

    mu = float(theta) * np.sqrt(info)
    z, w = gridpts(r=r, mu=mu, a=a, b=b)
    deviation = z - mu
    h = w * _normal_pdf(deviation)
    return z, w, h


def hupdate(
    r: int,
    theta: float,
    info: float,
    a: float,
    b: float,
    theta_prev: float,
    info_prev: float,
    gm1: tuple[Iterable[float], Iterable[float], Iterable[float]],
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """
    Update the density grid for a subsequent group sequential analysis.

    Args:
        r: Number of odd grid points defining the Simpson stencil (at least 2).
        theta: Canonical drift parameter for the current analysis.
        info: Fisher information at the current analysis; must exceed ``info_prev``.
        a: Lower integration limit; use ``-numpy.inf`` for no truncation.
        b: Upper integration limit; use ``numpy.inf`` for no truncation.
        theta_prev: Canonical drift parameter at the previous analysis.
        info_prev: Fisher information at the previous analysis; must be positive.
        gm1: tuple ``(z_prev, w_prev, h_prev)`` from ``h1`` or ``hupdate``.

    Returns:
        A tuple of arrays ``(z, w, h)`` updated for the current analysis.
    """

    if info <= info_prev:
        raise ValueError("Current information must exceed previous information.")
    if info_prev <= 0:
        raise ValueError("Previous information must be positive.")

    try:
        z_prev_raw, _, h_prev_raw = gm1
    except (TypeError, ValueError) as exc:
        raise ValueError("gm1 must unpack into (z_prev, w_prev, h_prev).") from exc

    z_prev = _as_float64(z_prev_raw)
    h_prev = _as_float64(h_prev_raw)
    if z_prev.shape != h_prev.shape:
        raise ValueError("Previous grid points and weights must share the same shape.")

    rt_info = np.sqrt(info)
    rt_info_prev = np.sqrt(info_prev)
    delta = info - info_prev
    rt_delta = np.sqrt(delta)

    z, w = gridpts(r=r, mu=float(theta) * rt_info, a=a, b=b)

    mu = theta * info - theta_prev * info_prev
    scale = rt_info / rt_delta
    t = (z_prev * rt_info_prev + mu) / rt_delta

    kernel = _normal_pdf(z[:, np.newaxis] * scale - t[np.newaxis, :])
    h = kernel @ h_prev
    h *= w * scale
    return z, w, h


__all__ = ["gridpts", "h1", "hupdate"]
