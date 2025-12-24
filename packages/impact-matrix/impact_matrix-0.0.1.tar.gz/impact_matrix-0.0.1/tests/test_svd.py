#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

import pytest


# -----------------------------------------------------------------------------

from mat import Matrix, SingularValueDecomposition


# -----------------------------------------------------------------------------

def test_svd_rectangular_reconstruction_and_orthogonality():
    A = Matrix.from_2d_array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    svd = SingularValueDecomposition(A)

    U = svd.get_U()
    S = svd.get_S()
    V = svd.get_V()

    recon = U.times(S).times(V.transpose())
    assert (A.minus(recon)).norm_f() < 1e-10

    UtU = U.transpose().times(U)
    Iu = Matrix.identity(U.get_column_dimension(), U.get_column_dimension())
    assert (UtU.minus(Iu)).norm_f() < 1e-10

    VtV = V.transpose().times(V)
    Iv = Matrix.identity(V.get_column_dimension(), V.get_column_dimension())
    assert (VtV.minus(Iv)).norm_f() < 1e-10

# -----------------------------------------------------------------------------

def test_svd_square_reconstruction():
    B = Matrix.from_2d_array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 10.0]])
    svd = SingularValueDecomposition(B)

    U = svd.get_U()
    S = svd.get_S()
    V = svd.get_V()

    recon = U.times(S).times(V.transpose())
    assert (B.minus(recon)).norm_f() < 1e-10

# -----------------------------------------------------------------------------

def test_svd_rank_deficient_rank_is_one():
    C = Matrix.from_2d_array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
    svd = SingularValueDecomposition(C)
    assert svd.rank() == 1


# -----------------------------------------------------------------------------

def test_svd_wide_matrix_reconstruction():
    W = Matrix.from_2d_array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    svd = SingularValueDecomposition(W)

    U = svd.get_U()
    S = svd.get_S()
    V = svd.get_V()

    recon = U.times(S).times(V.transpose())
    assert (W.minus(recon)).norm_f() < 1e-10

# -----------------------------------------------------------------------------
