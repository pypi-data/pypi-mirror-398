import numpy as np

from analysis3054.physics_forecaster import KoopmanSpectralDecomposer


def test_constant_window_handles_rank_deficiency_without_instability():
    decomposer = KoopmanSpectralDecomposer(hankel_rows=3)
    window = [5.0] * 6  # constant signal yields rank-deficient Hankel snapshot matrix

    result = decomposer.decompose(window)

    assert np.all(np.isfinite(result.eigenvalues))
    assert np.isfinite(result.instability_index)


def test_decompose_rejects_non_finite_values():
    decomposer = KoopmanSpectralDecomposer(hankel_rows=3)

    try:
        decomposer.decompose([1.0, np.nan, 2.0, 3.0])
    except ValueError as exc:  # noqa: PERF203
        assert "non-finite" in str(exc)
    else:  # pragma: no cover
        assert False, "Expected ValueError when window contains NaN"
