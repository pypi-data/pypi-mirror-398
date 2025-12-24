#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

import pytest


# -----------------------------------------------------------------------------

from mat import Matrix, CholeskyDecomposition


# -----------------------------------------------------------------------------

def test_cholesky_factor_and_solve():
    vals = [[4.0, 12.0, -16.0], [12.0, 37.0, -43.0], [-16.0, -43.0, 98.0]]
    A = Matrix.from_2d_array(vals)

    chol = CholeskyDecomposition(A)
    assert chol.is_spd() is True

    L = chol.get_L()
    LLt = L.times(L.transpose())

    assert_f = (A.minus(LLt)).norm_f()
    assert assert_f < 1e-10

    b = Matrix.from_2d_array([[1.0], [2.0], [3.0]])
    x = chol.solve(b)
    r = b.minus(A.times(x))
    assert r.norm_f() < 1e-10

# -----------------------------------------------------------------------------

def test_cholesky_rejects_non_spd():
    A = Matrix.from_2d_array([[1.0, 2.0], [2.0, 1.0]])
    chol = CholeskyDecomposition(A)
    assert chol.is_spd() is False

    b = Matrix.from_2d_array([[1.0], [1.0]])
    with pytest.raises(RuntimeError):
        chol.solve(b)

# -----------------------------------------------------------------------------
