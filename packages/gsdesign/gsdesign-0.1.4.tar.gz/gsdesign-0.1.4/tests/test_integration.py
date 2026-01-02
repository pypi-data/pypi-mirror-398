from __future__ import annotations

from collections.abc import Iterable
from io import StringIO
from typing import cast

import numpy as np
import pytest

from gsdesign import gridpts, h1, hupdate

GRIDPTS_SNAPSHOT = "gridpts_r5_mu0.5_a-2_b2"
H1_SNAPSHOT = "h1_r5_theta0.5_info2_a-2_b2"
HUPDATE_SNAPSHOT = "hupdate_r5_theta0.5_info2.5_thetaprev0.3_infoprev1.5_a-2_b2"
NORMALIZE_PRECISION = 12


def _normalize_matrix_text(text: str) -> str:
    data = np.loadtxt(StringIO(text))
    if data.ndim == 1:
        data = data[:, np.newaxis]
    lines = []
    for row in data:
        parts = [
            np.format_float_positional(
                float(value),
                precision=NORMALIZE_PRECISION,
                unique=False,
                trim="-",
            )
            for value in row
        ]
        lines.append(" ".join(parts))
    return "\n".join(lines)


def _columns_to_text(*columns: np.ndarray) -> str:
    buffer = StringIO()
    np.savetxt(buffer, np.column_stack(columns), fmt="%.16f")
    return buffer.getvalue().strip()


def _assert_snapshot_matrix(r_snapshot, name: str, *columns: np.ndarray) -> None:
    actual = _columns_to_text(*columns)
    r_snapshot.assert_match_text(
        actual,
        name=name,
        normalize=_normalize_matrix_text,
    )


@pytest.mark.r_snapshot(GRIDPTS_SNAPSHOT)
def test_gridpts_matches_reference(r_snapshot) -> None:
    # ```{r, gridpts_r5_mu0.5_a-2_b2}
    # options(digits = 16, scipen = 999)
    # suppressPackageStartupMessages(library(gsDesign2))
    # g <- gsDesign2:::gridpts(r = 5, mu = 0.5, a = -2, b = 2)
    # write.table(
    #   cbind(g$z, g$w),
    #   file = "",
    #   row.names = FALSE,
    #   col.names = FALSE,
    #   quote = FALSE
    # )
    # ```
    z, w = gridpts(r=5, mu=0.5, a=-2.0, b=2.0)
    _assert_snapshot_matrix(r_snapshot, GRIDPTS_SNAPSHOT, z, w)


@pytest.mark.r_snapshot(H1_SNAPSHOT)
def test_h1_matches_reference(r_snapshot) -> None:
    # ```{r, h1_r5_theta0.5_info2_a-2_b2}
    # options(digits = 16, scipen = 999)
    # suppressPackageStartupMessages(library(gsDesign2))
    # h1_ref <- gsDesign2:::h1(r = 5, theta = 0.5, info = 2, a = -2, b = 2)
    # write.table(
    #   cbind(h1_ref$z, h1_ref$w, h1_ref$h),
    #   file = "",
    #   row.names = FALSE,
    #   col.names = FALSE,
    #   quote = FALSE
    # )
    # ```
    z, w, h_vals = h1(r=5, theta=0.5, info=2.0, a=-2.0, b=2.0)
    _assert_snapshot_matrix(r_snapshot, H1_SNAPSHOT, z, w, h_vals)


@pytest.mark.r_snapshot(HUPDATE_SNAPSHOT)
def test_hupdate_matches_reference(r_snapshot) -> None:
    # ```{r, hupdate_r5_theta0.5_info2.5_thetaprev0.3_infoprev1.5_a-2_b2}
    # options(digits = 16, scipen = 999)
    # suppressPackageStartupMessages(library(gsDesign2))
    # gm1 <- gsDesign2:::h1(r = 5, theta = 0.3, info = 1.5, a = -2, b = 2)
    # hupdate_ref <- gsDesign2:::hupdate(
    #   r = 5,
    #   theta = 0.5,
    #   info = 2.5,
    #   a = -2,
    #   b = 2,
    #   thetam1 = 0.3,
    #   im1 = 1.5,
    #   gm1 = gm1
    # )
    # write.table(
    #   cbind(hupdate_ref$z, hupdate_ref$w, hupdate_ref$h),
    #   file = "",
    #   row.names = FALSE,
    #   col.names = FALSE,
    #   quote = FALSE
    # )
    # ```
    gm1 = h1(r=5, theta=0.3, info=1.5, a=-2.0, b=2.0)
    z, w, h_vals = hupdate(
        r=5,
        theta=0.5,
        info=2.5,
        a=-2.0,
        b=2.0,
        theta_prev=0.3,
        info_prev=1.5,
        gm1=gm1,
    )
    _assert_snapshot_matrix(r_snapshot, HUPDATE_SNAPSHOT, z, w, h_vals)


def test_gridpts_supports_infinite_bounds() -> None:
    z, w = gridpts(r=3, mu=0.0, a=-np.inf, b=np.inf)
    assert np.isfinite(z).all()
    np.testing.assert_allclose(z, -z[::-1], rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(w, w[::-1], rtol=0.0, atol=1e-12)
    assert np.all(w > 0)


def test_gridpts_single_point_when_bounds_extreme() -> None:
    z, w = gridpts(r=3, mu=0.0, a=100.0, b=101.0)
    assert z.shape == (1,)
    assert w.shape == (1,)
    np.testing.assert_allclose(z, np.array([100.0]))
    np.testing.assert_allclose(w, np.array([1.0]))


def test_gridpts_requires_r_at_least_two() -> None:
    with pytest.raises(ValueError, match="r must be at least 2"):
        gridpts(r=1)


def test_gridpts_requires_increasing_bounds() -> None:
    with pytest.raises(ValueError, match="Lower limit 'a' must be strictly less"):
        gridpts(r=2, a=1.0, b=1.0)


def test_h1_requires_positive_info() -> None:
    with pytest.raises(ValueError, match="Information 'info' must be positive"):
        h1(info=0.0)


def test_h1_infinite_bounds_integrates_to_one() -> None:
    _, _, h_vals = h1(r=3, theta=0.0, info=1.0, a=-np.inf, b=np.inf)
    assert pytest.approx(1.0, rel=1e-3) == float(np.sum(h_vals))


def test_hupdate_requires_increasing_info() -> None:
    gm1 = h1()
    with pytest.raises(
        ValueError, match="Current information must exceed previous information"
    ):
        hupdate(
            r=18,
            theta=0.0,
            info=1.0,
            a=-np.inf,
            b=np.inf,
            theta_prev=0.0,
            info_prev=1.0,
            gm1=gm1,
        )


def test_hupdate_requires_positive_previous_info() -> None:
    gm1 = (np.array([0.0]), np.array([1.0]), np.array([1.0]))
    with pytest.raises(ValueError, match="Previous information must be positive"):
        hupdate(
            r=2,
            theta=0.0,
            info=1.0,
            a=-np.inf,
            b=np.inf,
            theta_prev=0.0,
            info_prev=0.0,
            gm1=gm1,
        )


def test_hupdate_rejects_bad_gm1_structure() -> None:
    with pytest.raises(ValueError, match="gm1 must unpack"):
        bad_gm1 = cast(
            tuple[Iterable[float], Iterable[float], Iterable[float]],
            (np.array([0.0]),),
        )
        hupdate(
            r=2,
            theta=0.0,
            info=2.0,
            a=-np.inf,
            b=np.inf,
            theta_prev=0.0,
            info_prev=1.0,
            gm1=bad_gm1,
        )


def test_hupdate_rejects_shape_mismatch() -> None:
    gm1 = cast(
        tuple[Iterable[float], Iterable[float], Iterable[float]],
        (np.array([0.0, 1.0]), np.array([1.0, 1.0]), np.array([1.0])),
    )
    with pytest.raises(ValueError, match="Previous grid points and weights must share"):
        hupdate(
            r=2,
            theta=0.0,
            info=2.0,
            a=-np.inf,
            b=np.inf,
            theta_prev=0.0,
            info_prev=1.0,
            gm1=gm1,
        )


def test_hupdate_infinite_bounds_preserves_mass() -> None:
    gm1 = h1(r=3, theta=0.0, info=1.0, a=-np.inf, b=np.inf)
    _, _, h_vals = hupdate(
        r=3,
        theta=0.0,
        info=2.0,
        a=-np.inf,
        b=np.inf,
        theta_prev=0.0,
        info_prev=1.0,
        gm1=gm1,
    )
    assert pytest.approx(1.0, rel=1e-3) == float(np.sum(h_vals))
