#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

import pytest


# -----------------------------------------------------------------------------

from mat import Matrix, LUDecomposition


# -----------------------------------------------------------------------------

def test_lu_factor_solve_det_and_pivot_relation():
    A = Matrix.from_2d_array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 10.0]])
    lu = LUDecomposition(A)
    assert lu.is_nonsingular() is True

    L = lu.get_L()
    U = lu.get_U()
    piv = lu.get_pivot()

    PA = A.get_matrix_indices_cols(piv, 0, A.get_column_dimension() - 1)
    assert (PA.minus(L.times(U))).norm_f() < 1e-10

    assert abs(lu.det() - (-3.0)) < 1e-12

    b = Matrix.from_2d_array([[1.0], [2.0], [3.0]])
    x = lu.solve(b)
    assert (b.minus(A.times(x))).norm_f() < 1e-10

# -----------------------------------------------------------------------------

def test_lu_singular_raises_on_solve():
    S = Matrix.from_2d_array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0]])
    lu = LUDecomposition(S)
    assert lu.is_nonsingular() is False

    b = Matrix.from_2d_array([[1.0], [2.0], [3.0]])
    with pytest.raises(RuntimeError):
        lu.solve(b)

# -----------------------------------------------------------------------------
