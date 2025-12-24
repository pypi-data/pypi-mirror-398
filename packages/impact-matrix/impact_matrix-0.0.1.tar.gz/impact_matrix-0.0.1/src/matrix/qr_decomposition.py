#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
 QR Decomposition.

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
from .maths import Maths

# =============================================================================

class QRDecomposition:
    """
    QR Decomposition.
    
    For an m-by-n matrix A with m >= n, the QR decomposition is an m-by-n
    orthogonal matrix Q and an n-by-n upper triangular matrix R so that A = Q*R.
    
    The QR decomposition always exists, even if the matrix does not have full
    rank, so the constructor will never fail. The primary use of the QR
    decomposition is in the least squares solution of nonsquare systems of
    simultaneous linear equations. This will fail if is_full_rank() returns False.
    """
    
    def __init__(self, A: 'Matrix'):
        """
        QR Decomposition, computed by Householder reflections.
        
        Args:
            A: Rectangular matrix.
        """
        # Initialize
        self._QR = A.get_array_copy()
        self._m = A.get_row_dimension()
        self._n = A.get_column_dimension()
        m = self._m
        n = self._n
        QR = self._QR
        
        self._Rdiag = [0.0] * n
        
        # Main loop
        for k in range(n):
            # Compute 2-norm of k-th column without under/overflow
            nrm = 0.0
            
            for i in range(k, m):
                nrm = Maths.hypot(nrm, QR[i][k])
            
            if nrm != 0.0:
                # Form k-th Householder vector
                if QR[k][k] < 0:
                    nrm = -nrm
                
                for i in range(k, m):
                    QR[i][k] /= nrm
                
                QR[k][k] += 1.0
                
                # Apply transformation to remaining columns
                for j in range(k + 1, n):
                    s = 0.0
                    
                    for i in range(k, m):
                        s += QR[i][k] * QR[i][j]
                    
                    s = -s / QR[k][k]
                    
                    for i in range(k, m):
                        QR[i][j] += s * QR[i][k]
            
            self._Rdiag[k] = -nrm
    
    def is_full_rank(self) -> bool:
        """
        Is the matrix full rank?
        
        Returns:
            True if R, and hence A, has full rank.
        """
        for j in range(self._n):
            if self._Rdiag[j] == 0:
                return False
        return True
    
    def get_H(self) -> 'Matrix':
        """
        Return the Householder vectors.
        
        Returns:
            Lower trapezoidal matrix whose columns define the reflections.
        """
        X = Matrix(self._m, self._n)
        H = X.get_array()
        
        for i in range(self._m):
            for j in range(self._n):
                if i >= j:
                    H[i][j] = self._QR[i][j]
                else:
                    H[i][j] = 0.0
        
        return X
    
    def get_R(self) -> 'Matrix':
        """
        Return the upper triangular factor.
        
        Returns:
            R
        """
        X = Matrix(self._n, self._n)
        R = X.get_array()
        
        for i in range(self._n):
            for j in range(self._n):
                if i < j:
                    R[i][j] = self._QR[i][j]
                elif i == j:
                    R[i][j] = self._Rdiag[i]
                else:
                    R[i][j] = 0.0
        
        return X
    
    def get_Q(self) -> 'Matrix':
        """
        Generate and return the (economy-sized) orthogonal factor.
        
        Returns:
            Q
        """
        X = Matrix(self._m, self._n)
        Q = X.get_array()
        
        for k in range(self._n - 1, -1, -1):
            for i in range(self._m):
                Q[i][k] = 0.0
            
            Q[k][k] = 1.0
            
            for j in range(k, self._n):
                if self._QR[k][k] != 0:
                    s = 0.0
                    
                    for i in range(k, self._m):
                        s += self._QR[i][k] * Q[i][j]
                    
                    s = -s / self._QR[k][k]
                    
                    for i in range(k, self._m):
                        Q[i][j] += s * self._QR[i][k]
        
        return X
    
    def solve(self, B: 'Matrix') -> 'Matrix':
        """
        Least squares solution of A * X = B
        
        Args:
            B: A Matrix with as many rows as A and any number of columns.
        
        Returns:
            X that minimizes the two norm of Q*R*X - B.
        
        Raises:
            ValueError: If matrix row dimensions don't agree.
            RuntimeError: If matrix is rank deficient.
        """
        if B.get_row_dimension() != self._m:
            raise ValueError("Matrix row dimensions must agree.")
        
        if not self.is_full_rank():
            raise RuntimeError("Matrix is rank deficient.")
        
        # Copy right hand side
        nx = B.get_column_dimension()
        X = B.get_array_copy()
        
        # Compute Y = transpose(Q) * B
        for k in range(self._n):
            for j in range(nx):
                s = 0.0
                
                for i in range(k, self._m):
                    s += self._QR[i][k] * X[i][j]
                
                s = -s / self._QR[k][k]
                
                for i in range(k, self._m):
                    X[i][j] += s * self._QR[i][k]
        
        # Solve R * X = Y
        for k in range(self._n - 1, -1, -1):
            for j in range(nx):
                X[k][j] /= self._Rdiag[k]
            
            for i in range(k):
                for j in range(nx):
                    X[i][j] -= X[k][j] * self._QR[i][k]
        
        return Matrix.from_array_with_dims(X, self._n, nx).get_matrix(0, self._n - 1, 0, nx - 1)


# =============================================================================

