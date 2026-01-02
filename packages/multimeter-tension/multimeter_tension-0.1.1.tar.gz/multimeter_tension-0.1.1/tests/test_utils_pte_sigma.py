import numpy as np
import pytest

from multimeter.utils.utils import PTE_to_n_sigma, n_sigma_to_PTE


@pytest.mark.parametrize("pte", [0.9, 0.5, 0.32, 0.1, 0.05, 1e-3, 1e-6])
def test_pte_sigma_roundtrip(pte):
    n = PTE_to_n_sigma(pte)
    p_back = n_sigma_to_PTE(n)
    assert np.isfinite(n)
    assert np.isfinite(p_back)
    assert p_back == pytest.approx(pte, rel=0, abs=1e-12)


@pytest.mark.parametrize("n", [0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0])
def test_sigma_pte_roundtrip(n):
    p = n_sigma_to_PTE(n)
    n_back = PTE_to_n_sigma(p)
    assert np.isfinite(p)
    assert 0.0 < p <= 1.0
    assert np.isfinite(n_back)
    assert n_back == pytest.approx(n, rel=0, abs=1e-12)


def test_n_sigma_to_PTE_monotonic():
    n = np.array([0.0, 1.0, 2.0, 3.0, 5.0])
    p = n_sigma_to_PTE(n)
    assert np.all(np.isfinite(p))
    assert np.all((p > 0.0) & (p <= 1.0))
    assert np.all(np.diff(p) < 0.0)
