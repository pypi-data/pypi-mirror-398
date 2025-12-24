#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""

"""
# -----------------------------------------------------------------------------

import math

from typing import (
    List,
    Optional,
    TextIO,
    Union,
    Sequence
)


# -----------------------------------------------------------------------------

from .matrix import Matrix


# =============================================================================

class CholeskyDecomposition:
    """
    Cholesky Decomposition.
    
    For a symmetric, positive definite matrix A, the Cholesky decomposition is a
    lower triangular matrix L so that A = L * L'.
    
    If the matrix is not symmetric or positive definite, the constructor returns
    a partial decomposition and sets an internal flag that may be queried by the
    is_spd() method.
    """
    
    def __init__(self, Arg: 'Matrix'):
        """
        Cholesky algorithm for symmetric and positive definite matrix.
        
        Args:
            Arg: Square, symmetric matrix.
        """
        # Initialize
        A = Arg.get_array()
        self._n = Arg.get_row_dimension()
        n = self._n
        self._L = [[0.0] * n for _ in range(n)]
        L = self._L
        self._isspd = (Arg.get_column_dimension() == n)
        
        # Main loop
        for j in range(n):
            Lrowj = L[j]
            d = 0.0
            
            for k in range(j):
                Lrowk = L[k]
                s = 0.0
                
                for i in range(k):
                    s += Lrowk[i] * Lrowj[i]
                
                Lrowj[k] = s = (A[j][k] - s) / L[k][k]
                d = d + s * s
                self._isspd = self._isspd and (A[k][j] == A[j][k])
            
            d = A[j][j] - d
            self._isspd = self._isspd and (d > 0.0)
            L[j][j] = math.sqrt(max(d, 0.0))
            
            for k in range(j + 1, n):
                L[j][k] = 0.0
    
    def get_L(self) -> 'Matrix':
        """
        Return triangular factor.
        
        Returns:
            L (lower triangular matrix)
        """
        return Matrix.from_array_with_dims(self._L, self._n, self._n)
    
    def is_spd(self) -> bool:
        """
        Is the matrix symmetric and positive definite?
        
        Returns:
            True if A is symmetric and positive definite.
        """
        return self._isspd
    
    def solve(self, B: 'Matrix') -> 'Matrix':
        """
        Solve A * X = B
        
        Args:
            B: A Matrix with as many rows as A and any number of columns.
        
        Returns:
            X so that L * L' * X = B
        
        Raises:
            ValueError: If matrix row dimensions don't agree.
            RuntimeError: If matrix is not symmetric positive definite.
        """
        if B.get_row_dimension() != self._n:
            raise ValueError("Matrix row dimensions must agree.")
        
        if not self._isspd:
            raise RuntimeError("Matrix is not symmetric positive definite.")
        
        # Copy right hand side
        X = B.get_array_copy()
        nx = B.get_column_dimension()
        n = self._n
        L = self._L
        
        # Solve L * Y = B
        for k in range(n):
            for j in range(nx):
                X[k][j] /= L[k][k]

            for i in range(k + 1, n):
                for j in range(nx):
                    X[i][j] -= X[k][j] * L[i][k]
        
        # Solve L' * X = Y
        for k in range(n - 1, -1, -1):
            for j in range(nx):
                X[k][j] /= L[k][k]
            
            for i in range(k):
                for j in range(nx):
                    X[i][j] -= X[k][j] * L[k][i]
        
        return Matrix.from_array_with_dims(X, n, nx)


# =============================================================================

