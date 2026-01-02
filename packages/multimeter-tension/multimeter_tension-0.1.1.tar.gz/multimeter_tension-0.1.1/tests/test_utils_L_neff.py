import numpy as np
import pytest

from multimeter.utils.utils import n_eff_to_L_iso, L_iso_to_n_eff


@pytest.mark.parametrize("gauss_scale", ["1sigma", "2sigma"])
@pytest.mark.parametrize("n", [0.0, 0.5, 1.0, 2.0, 3.0, 5.0])
def test_neff_L_roundtrip(n, gauss_scale):
    L = n_eff_to_L_iso(n=n, d=2, sigma2=0.5, gauss_scale=gauss_scale)
    n_back = float(L_iso_to_n_eff(L=L, d=2, sigma2=0.5, gauss_scale=gauss_scale))
    assert np.isfinite(L)
    assert L >= 0.0
    assert np.isfinite(n_back)
    # Interpolation grid is coarse (100 points): allow small absolute error
    assert n_back == pytest.approx(n, abs=0.05)


@pytest.mark.parametrize("gauss_scale", ["1sigma", "2sigma"])
def test_neff_to_L_monotonic(gauss_scale):
    n = np.array([0.0, 1.0, 2.0, 3.0, 5.0])
    L = np.array([n_eff_to_L_iso(n=ni, d=2, sigma2=0.5, gauss_scale=gauss_scale) for ni in n])
    assert np.all(np.isfinite(L))
    assert np.all(np.diff(L) >= 0.0)


@pytest.mark.parametrize("gauss_scale", ["1sigma", "2sigma"])
def test_L_to_neff_monotonic(gauss_scale):
    L = np.array([0.0, 1.0, 2.0, 4.0, 8.0])
    n = np.array([float(L_iso_to_n_eff(L=Li, d=2, sigma2=0.5, gauss_scale=gauss_scale)) for Li in L])
    assert np.all(np.isfinite(n))
    assert np.all(np.diff(n) >= 0.0)
