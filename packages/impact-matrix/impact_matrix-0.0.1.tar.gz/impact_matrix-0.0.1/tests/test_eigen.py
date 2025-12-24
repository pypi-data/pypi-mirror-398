#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

import pytest


# -----------------------------------------------------------------------------

from mat import Matrix, EigenvalueDecomposition


# -----------------------------------------------------------------------------

def test_eigen_symmetric_av_equals_vd_and_reconstruction():
    A = Matrix.from_2d_array([[4.0, 1.0, 1.0], [1.0, 2.0, 3.0], [1.0, 3.0, 6.0]])
    eig = EigenvalueDecomposition(A)

    V = eig.get_V()
    D = eig.get_D()

    AV = A.times(V)
    VD = V.times(D)
    assert (AV.minus(VD)).norm_f() < 1e-10

    VtV = V.transpose().times(V)
    I = Matrix.identity(V.get_row_dimension(), V.get_column_dimension())
    assert (VtV.minus(I)).norm_f() < 1e-10

    A_recon = V.times(D).times(V.transpose())
    assert (A.minus(A_recon)).norm_f() < 1e-10

# -----------------------------------------------------------------------------

def test_eigen_nonsymmetric_av_equals_vd_in_real_block_form():
    B = Matrix.from_2d_array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
    eig = EigenvalueDecomposition(B)
    V = eig.get_V()
    D = eig.get_D()

    BV = B.times(V)
    VD = V.times(D)
    assert (BV.minus(VD)).norm_f() < 1e-10

# -----------------------------------------------------------------------------
