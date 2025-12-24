#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""

"""
# -----------------------------------------------------------------------------

from typing import (
    List,
    Optional,
    TextIO,
    Union,
    Sequence
)

from .matrix import Matrix


# =============================================================================

class LUDecomposition:
    """
    LU Decomposition.
    
    For an m-by-n matrix A with m >= n, the LU decomposition is an m-by-n unit
    lower triangular matrix L, an n-by-n upper triangular matrix U, and a
    permutation vector piv of length m so that A(piv,:) = L*U. If m < n, then L
    is m-by-m and U is m-by-n.
    
    The LU decomposition with pivoting always exists, even if the matrix is
    singular, so the constructor will never fail. The primary use of the LU
    decomposition is in the solution of square systems of simultaneous linear
    equations. This will fail if is_nonsingular() returns False.
    """
    
    def __init__(self, A: 'Matrix'):
        """
        LU Decomposition using a "left-looking", dot-product, Crout/Doolittle algorithm.
        
        Args:
            A: Rectangular matrix.
        """
        # Use a "left-looking", dot-product, Crout/Doolittle algorithm.
        self._LU = A.get_array_copy()
        self._m = A.get_row_dimension()
        self._n = A.get_column_dimension()
        m = self._m
        n = self._n
        LU = self._LU
        
        self._piv = list(range(m))
        self._pivsign = 1
        
        LUcolj = [0.0] * m
        
        # Outer loop
        for j in range(n):
            # Make a copy of the j-th column to localize references
            for i in range(m):
                LUcolj[i] = LU[i][j]
            
            # Apply previous transformations
            for i in range(m):
                LUrowi = LU[i]
                
                # Most of the time is spent in the following dot product
                kmax = min(i, j)
                s = 0.0
                
                for k in range(kmax):
                    s += LUrowi[k] * LUcolj[k]
                
                LUrowi[j] = LUcolj[i] = LUcolj[i] - s
            
            # Find pivot and exchange if necessary
            p = j
            
            for i in range(j + 1, m):
                if abs(LUcolj[i]) > abs(LUcolj[p]):
                    p = i
            
            if p != j:
                for k in range(n):
                    t = LU[p][k]
                    LU[p][k] = LU[j][k]
                    LU[j][k] = t
                
                k = self._piv[p]
                self._piv[p] = self._piv[j]
                self._piv[j] = k
                self._pivsign = -self._pivsign
            
            # Compute multipliers
            if j < m and LU[j][j] != 0.0:
                for i in range(j + 1, m):
                    LU[i][j] /= LU[j][j]
    
    def is_nonsingular(self) -> bool:
        """
        Is the matrix nonsingular?
        
        Returns:
            True if U, and hence A, is nonsingular.
        """
        for j in range(self._n):
            if self._LU[j][j] == 0:
                return False
        return True
    
    def get_L(self) -> 'Matrix':
        """
        Return lower triangular factor.
        
        Returns:
            L
        """
        X = Matrix(self._m, self._n)
        L = X.get_array()
        
        for i in range(self._m):
            for j in range(self._n):
                if i > j:
                    L[i][j] = self._LU[i][j]
                elif i == j:
                    L[i][j] = 1.0
                else:
                    L[i][j] = 0.0
        
        return X
    
    def get_U(self) -> 'Matrix':
        """
        Return upper triangular factor.
        
        Returns:
            U
        """
        X = Matrix(self._n, self._n)
        U = X.get_array()
        
        for i in range(self._n):
            for j in range(self._n):
                if i <= j:
                    U[i][j] = self._LU[i][j]
                else:
                    U[i][j] = 0.0
        
        return X
    
    def get_pivot(self) -> List[int]:
        """
        Return pivot permutation vector.
        
        Returns:
            piv
        """
        return self._piv.copy()
    
    def get_double_pivot(self) -> List[float]:
        """
        Return pivot permutation vector as a one-dimensional double array.
        
        Returns:
            (double) piv
        """
        return [float(p) for p in self._piv]
    
    def det(self) -> float:
        """
        Determinant.
        
        Returns:
            det(A)
        
        Raises:
            ValueError: If matrix is not square.
        """
        if self._m != self._n:
            raise ValueError("Matrix must be square.")
        
        d = float(self._pivsign)
        
        for j in range(self._n):
            d *= self._LU[j][j]
        
        return d
    
    def solve(self, B: 'Matrix') -> 'Matrix':
        """
        Solve A * X = B
        
        Args:
            B: A Matrix with as many rows as A and any number of columns.
        
        Returns:
            X so that L * U * X = B(piv, :)
        
        Raises:
            ValueError: If matrix row dimensions don't agree.
            RuntimeError: If matrix is singular.
        """
        if B.get_row_dimension() != self._m:
            raise ValueError("Matrix row dimensions must agree.")
        
        if not self.is_nonsingular():
            raise RuntimeError("Matrix is singular.")
        
        # Copy right hand side with pivoting
        nx = B.get_column_dimension()
        Xmat = B.get_matrix_indices_cols(self._piv, 0, nx - 1)
        X = Xmat.get_array()
        
        # Solve L * Y = B(piv, :)
        for k in range(self._n):
            for i in range(k + 1, self._n):
                for j in range(nx):
                    X[i][j] -= X[k][j] * self._LU[i][k]
        
        # Solve U * X = Y
        for k in range(self._n - 1, -1, -1):
            for j in range(nx):
                X[k][j] /= self._LU[k][k]
            
            for i in range(k):
                for j in range(nx):
                    X[i][j] -= X[k][j] * self._LU[i][k]
        
        return Xmat


# =============================================================================

