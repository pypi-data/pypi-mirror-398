#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

import pytest


# -----------------------------------------------------------------------------

from mat import Matrix, QRDecomposition


# -----------------------------------------------------------------------------

def test_qr_rectangular_reconstruction_orthogonality_and_solve():
    A = Matrix.from_2d_array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    qr = QRDecomposition(A)
    assert qr.is_full_rank() is True

    Q = qr.get_Q()
    R = qr.get_R()

    assert (A.minus(Q.times(R))).norm_f() < 1e-10

    QtQ = Q.transpose().times(Q)
    I = Matrix.identity(Q.get_column_dimension(), Q.get_column_dimension())
    assert (QtQ.minus(I)).norm_f() < 1e-10

    b = Matrix.from_2d_array([[1.0], [2.0], [3.0]])
    x = qr.solve(b)
    r = b.minus(A.times(x))
    assert r.norm_f() < 1e-10

# -----------------------------------------------------------------------------

def test_qr_rank_deficient_raises_on_solve():
    C = Matrix.from_2d_array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
    qr = QRDecomposition(C)
    assert qr.is_full_rank() is False

    b = Matrix.from_2d_array([[1.0], [2.0], [3.0]])
    with pytest.raises(RuntimeError):
        qr.solve(b)

# -----------------------------------------------------------------------------
