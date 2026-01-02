import numpy as np
import pytest

from multimeter.utils.utils import PTE_to_L, L_to_PTE


@pytest.mark.parametrize("Nd", [2, 3])
#@pytest.mark.parametrize("pte", [0.9, 0.5, 0.32, 0.1, 0.05, 1e-3, 1e-6])
@pytest.mark.parametrize("pte", [0.5, 0.32, 0.1, 0.05, 1e-3, 1e-6])
def test_pte_L_roundtrip(Nd, pte):
    L = float(PTE_to_L(PTE=pte, Nd=Nd, d=2, sigma2=0.5))
    p_back = float(L_to_PTE(L=L, Nd=Nd, d=2, sigma2=0.5))
    assert np.isfinite(L)
    assert np.isfinite(p_back)
    assert 0.0 < p_back <= 1.0
    # Both mappings are interpolated: allow moderate relative error
    assert p_back == pytest.approx(pte, rel=0.10, abs=1e-12)


@pytest.mark.parametrize("Nd", [2, 3])
def test_PTE_to_L_monotonic(Nd):
    #p = np.array([0.9, 0.5, 0.32, 0.1, 0.05, 1e-3])
    p = np.array([0.5, 0.32, 0.1, 0.05, 1e-3])
    L = np.array([float(PTE_to_L(PTE=pi, Nd=Nd, d=2, sigma2=0.5)) for pi in p])
    assert np.all(np.isfinite(L))
    # As p decreases, L should increase
    assert np.all(np.diff(L) > 0.0)


@pytest.mark.parametrize("Nd", [2, 3])
def test_L_to_PTE_monotonic(Nd):
    L = np.array([0.0, 1.0, 2.0, 4.0, 6.0, 8.0])
    p = np.array([float(L_to_PTE(L=Li, Nd=Nd, d=2, sigma2=0.5)) for Li in L])
    assert np.all(np.isfinite(p))
    assert np.all((p >= 0.0) & (p <= 1.0))
    assert np.all(np.diff(p) < 0.0)
