#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Singular Value Decomposition.

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

from .matrix import Matrix
from .maths import Maths


# =============================================================================

class SingularValueDecomposition:
    """
    Singular Value Decomposition.
    
    For an m-by-n matrix A with m >= n, the singular value decomposition is an
    m-by-n orthogonal matrix U, an n-by-n diagonal matrix S, and an n-by-n
    orthogonal matrix V so that A = U * S * V'.
    
    The singular values, sigma[k] = S[k][k], are ordered so that
    sigma[0] >= sigma[1] >= ... >= sigma[n-1].
    
    The singular value decomposition always exists, so the constructor will never
    fail. The matrix condition number and the effective numerical rank can be
    computed from this decomposition.

    Updated for m < n case. (2025-12-21)
    """
    
    def __init__(self, Arg: 'Matrix'):
        """
        Construct the singular value decomposition.
        
        Args:
            Arg: Rectangular matrix.
        """
        if Arg.get_row_dimension() < Arg.get_column_dimension():
            svd_t = SingularValueDecomposition(Arg.transpose())

            self._m = Arg.get_row_dimension()
            self._n = Arg.get_column_dimension()
            m = self._m
            n = self._n
            nu = min(m, n)

            self._s = svd_t._s.copy()

            # A^T = U_t * S_t * V_t^T
            # A   = V_t * S_t^T * U_t^T
            # So U = V_t (m x m)
            self._U = [row[:] for row in svd_t._V]

            # V should be n x n. We use the n x nu thin left singular vectors of A^T
            # as the first nu columns and orthonormal-complete the rest.
            U_t = svd_t._U  # n x nu
            V_full = [[0.0] * n for _ in range(n)]

            # Copy first nu columns from U_t
            for i in range(n):
                for j in range(nu):
                    V_full[i][j] = U_t[i][j]

            # Orthonormal completion for remaining columns
            cols = [[V_full[i][j] for i in range(n)] for j in range(nu)]
            eps = 2.0 ** -52.0
            tol = 100.0 * eps

            for target_col in range(nu, n):
                v = None
                for basis_idx in range(n):
                    candidate = [0.0] * n
                    candidate[basis_idx] = 1.0

                    # Modified Gram-Schmidt against existing cols
                    for c in cols:
                        dot = sum(candidate[i] * c[i] for i in range(n))
                        for i in range(n):
                            candidate[i] -= dot * c[i]

                    norm = math.sqrt(sum(candidate[i] * candidate[i] for i in range(n)))
                    if norm > tol:
                        v = [candidate[i] / norm for i in range(n)]
                        break

                if v is None:
                    v = [0.0] * n
                    v[target_col] = 1.0

                cols.append(v)
                for i in range(n):
                    V_full[i][target_col] = v[i]

            self._V = V_full
            return

        # Derived from LINPACK code.
        # Initialize.
        A = Arg.get_array_copy()
        self._m = Arg.get_row_dimension()
        self._n = Arg.get_column_dimension()
        m = self._m
        n = self._n
        
        nu = min(m, n)
        self._s = [0.0] * min(m + 1, n)
        self._U = [[0.0] * nu for _ in range(m)]
        self._V = [[0.0] * n for _ in range(n)]
        s = self._s
        U = self._U
        V = self._V
        
        e = [0.0] * n
        work = [0.0] * m
        wantu = True
        wantv = True
        
        # Reduce A to bidiagonal form, storing the diagonal elements
        # in s and the super-diagonal elements in e.
        nct = min(m - 1, n)
        nrt = max(0, min(n - 2, m))
        
        for k in range(max(nct, nrt)):
            if k < nct:
                # Compute the transformation for the k-th column and
                # place the k-th diagonal in s[k].
                # Compute 2-norm of k-th column without under/overflow.
                s[k] = 0.0
                
                for i in range(k, m):
                    s[k] = Maths.hypot(s[k], A[i][k])
                
                if s[k] != 0.0:
                    if A[k][k] < 0.0:
                        s[k] = -s[k]
                    
                    for i in range(k, m):
                        A[i][k] /= s[k]
                    
                    A[k][k] += 1.0
                
                s[k] = -s[k]
            
            for j in range(k + 1, n):
                if k < nct and s[k] != 0.0:
                    # Apply the transformation.
                    t = 0.0
                    
                    for i in range(k, m):
                        t += A[i][k] * A[i][j]
                    
                    t = -t / A[k][k]
                    
                    for i in range(k, m):
                        A[i][j] += t * A[i][k]
                
                # Place the k-th row of A into e for the
                # subsequent calculation of the row transformation.
                e[j] = A[k][j]
            
            if wantu and k < nct:
                # Place the transformation in U for subsequent back
                # multiplication.
                for i in range(k, m):
                    U[i][k] = A[i][k]
            
            if k < nrt:
                # Compute the k-th row transformation and place the
                # k-th super-diagonal in e[k].
                # Compute 2-norm without under/overflow.
                e[k] = 0.0
                
                for i in range(k + 1, n):
                    e[k] = Maths.hypot(e[k], e[i])
                
                if e[k] != 0.0:
                    if e[k + 1] < 0.0:
                        e[k] = -e[k]
                    
                    for i in range(k + 1, n):
                        e[i] /= e[k]
                    
                    e[k + 1] += 1.0
                
                e[k] = -e[k]
                
                if k + 1 < m and e[k] != 0.0:
                    # Apply the transformation.
                    for i in range(k + 1, m):
                        work[i] = 0.0
                    
                    for j in range(k + 1, n):
                        for i in range(k + 1, m):
                            work[i] += e[j] * A[i][j]
                    
                    for j in range(k + 1, n):
                        t = -e[j] / e[k + 1]
                        
                        for i in range(k + 1, m):
                            A[i][j] += t * work[i]
                
                if wantv:
                    # Place the transformation in V for subsequent
                    # back multiplication.
                    for i in range(k + 1, n):
                        V[i][k] = e[i]
        
        # Set up the final bidiagonal matrix of order p.
        p = min(n, m + 1)
        
        if nct < n:
            s[nct] = A[nct][nct]
        
        if m < p:
            s[p - 1] = 0.0
        
        if nrt + 1 < p:
            e[nrt] = A[nrt][p - 1]
        
        e[p - 1] = 0.0
        
        # If required, generate U.
        if wantu:
            for j in range(nct, nu):
                for i in range(m):
                    U[i][j] = 0.0
                U[j][j] = 1.0
            
            for k in range(nct - 1, -1, -1):
                if s[k] != 0.0:
                    for j in range(k + 1, nu):
                        t = 0.0
                        
                        for i in range(k, m):
                            t += U[i][k] * U[i][j]
                        
                        t = -t / U[k][k]
                        
                        for i in range(k, m):
                            U[i][j] += t * U[i][k]
                    
                    for i in range(k, m):
                        U[i][k] = -U[i][k]
                    
                    U[k][k] = 1.0 + U[k][k]
                    
                    for i in range(k - 1):
                        U[i][k] = 0.0
                else:
                    for i in range(m):
                        U[i][k] = 0.0
                    U[k][k] = 1.0
        
        # If required, generate V.
        if wantv:
            for k in range(n - 1, -1, -1):
                if k < nrt and e[k] != 0.0:
                    for j in range(k + 1, nu):
                        t = 0.0
                        
                        for i in range(k + 1, n):
                            t += V[i][k] * V[i][j]
                        
                        t = -t / V[k + 1][k]
                        
                        for i in range(k + 1, n):
                            V[i][j] += t * V[i][k]
                
                for i in range(n):
                    V[i][k] = 0.0
                V[k][k] = 1.0
        
        # Main iteration loop for the singular values.
        pp = p - 1
        iter_count = 0
        eps = 2.0 ** -52.0
        
        while p > 0:
            # Here is where a test for too many iterations would go.
            # This section of the program inspects for
            # negligible elements in the s and e arrays. On
            # completion the variables kase and k are set as follows.
            # kase = 1 if s(p) and e[k-1] are negligible and k<p
            # kase = 2 if s(k) is negligible and k<p
            # kase = 3 if e[k-1] is negligible, k<p, and
            #           s(k), ..., s(p) are not negligible (qr step).
            # kase = 4 if e(p-1) is negligible (convergence).
            
            k = p - 2
            while k >= -1:
                if k == -1:
                    break
                
                if abs(e[k]) <= eps * (abs(s[k]) + abs(s[k + 1])):
                    e[k] = 0.0
                    break
                
                k -= 1
            
            if k == p - 2:
                kase = 4
            else:
                ks = p - 1
                while ks >= k:
                    if ks == k:
                        break
                    
                    t = (abs(e[ks]) if ks != p else 0.0) + (abs(e[ks - 1]) if ks != k + 1 else 0.0)
                    
                    if abs(s[ks]) <= eps * t:
                        s[ks] = 0.0
                        break
                    
                    ks -= 1
                
                if ks == k:
                    kase = 3
                elif ks == p - 1:
                    kase = 1
                else:
                    kase = 2
                    k = ks
            
            k += 1
            
            # Perform the task indicated by kase.
            if kase == 1:
                # Deflate negligible s(p).
                f = e[p - 2]
                e[p - 2] = 0.0
                
                for j in range(p - 2, k - 1, -1):
                    t = Maths.hypot(s[j], f)
                    cs = s[j] / t
                    sn = f / t
                    s[j] = t
                    
                    if j != k:
                        f = -sn * e[j - 1]
                        e[j - 1] = cs * e[j - 1]
                    
                    if wantv:
                        for i in range(n):
                            t = cs * V[i][j] + sn * V[i][p - 1]
                            V[i][p - 1] = -sn * V[i][j] + cs * V[i][p - 1]
                            V[i][j] = t
            
            elif kase == 2:
                # Split at negligible s(k).
                f = e[k - 1]
                e[k - 1] = 0.0
                
                for j in range(k, p):
                    t = Maths.hypot(s[j], f)
                    cs = s[j] / t
                    sn = f / t
                    s[j] = t
                    f = -sn * e[j]
                    e[j] = cs * e[j]
                    
                    if wantu:
                        for i in range(m):
                            t = cs * U[i][j] + sn * U[i][k - 1]
                            U[i][k - 1] = -sn * U[i][j] + cs * U[i][k - 1]
                            U[i][j] = t
            
            elif kase == 3:
                # Perform one qr step.
                # Calculate the shift.
                scale = max(max(max(max(abs(s[p - 1]), abs(s[p - 2])), abs(e[p - 2])), abs(s[k])), abs(e[k]))
                sp = s[p - 1] / scale
                spm1 = s[p - 2] / scale
                epm1 = e[p - 2] / scale
                sk = s[k] / scale
                ek = e[k] / scale
                b = ((spm1 + sp) * (spm1 - sp) + epm1 * epm1) / 2.0
                c = (sp * epm1) * (sp * epm1)
                shift = 0.0
                
                if b != 0.0 or c != 0.0:
                    shift = math.sqrt(b * b + c)
                    
                    if b < 0.0:
                        shift = -shift
                    
                    shift = c / (b + shift)
                
                f = (sk + sp) * (sk - sp) + shift
                g = sk * ek
                
                # Chase zeros.
                for j in range(k, p - 1):
                    t = Maths.hypot(f, g)
                    cs = f / t
                    sn = g / t
                    
                    if j != k:
                        e[j - 1] = t
                    
                    f = cs * s[j] + sn * e[j]
                    e[j] = cs * e[j] - sn * s[j]
                    g = sn * s[j + 1]
                    s[j + 1] = cs * s[j + 1]
                    
                    if wantv:
                        for i in range(n):
                            t = cs * V[i][j] + sn * V[i][j + 1]
                            V[i][j + 1] = -sn * V[i][j] + cs * V[i][j + 1]
                            V[i][j] = t
                    
                    t = Maths.hypot(f, g)
                    cs = f / t
                    sn = g / t
                    s[j] = t
                    f = cs * e[j] + sn * s[j + 1]
                    s[j + 1] = -sn * e[j] + cs * s[j + 1]
                    g = sn * e[j + 1]
                    e[j + 1] = cs * e[j + 1]
                    
                    if wantu and j < m - 1:
                        for i in range(m):
                            t = cs * U[i][j] + sn * U[i][j + 1]
                            U[i][j + 1] = -sn * U[i][j] + cs * U[i][j + 1]
                            U[i][j] = t
                
                e[p - 2] = f
                iter_count += 1
            
            elif kase == 4:
                # Convergence.
                # Make the singular values positive.
                if s[k] <= 0.0:
                    s[k] = -s[k] if s[k] < 0.0 else 0.0
                    
                    if wantv:
                        for i in range(pp + 1):
                            V[i][k] = -V[i][k]
                
                # Order the singular values.
                while k < pp:
                    if s[k] >= s[k + 1]:
                        break
                    
                    t = s[k]
                    s[k] = s[k + 1]
                    s[k + 1] = t
                    
                    if wantv and k < n - 1:
                        for i in range(n):
                            t = V[i][k + 1]
                            V[i][k + 1] = V[i][k]
                            V[i][k] = t
                    
                    if wantu and k < m - 1:
                        for i in range(m):
                            t = U[i][k + 1]
                            U[i][k + 1] = U[i][k]
                            U[i][k] = t
                    
                    k += 1
                
                iter_count = 0
                p -= 1
    
    def get_U(self) -> 'Matrix':
        """
        Return the left singular vectors.
        
        Returns:
            U
        """
        ucols = len(self._U[0]) if self._m > 0 else 0
        return Matrix.from_array_with_dims(
            [[self._U[i][j] for j in range(ucols)] for i in range(self._m)],
            self._m, ucols
        )
    
    def get_V(self) -> 'Matrix':
        """
        Return the right singular vectors.
        
        Returns:
            V
        """
        return Matrix.from_array_with_dims(
            [[self._V[i][j] for j in range(self._n)] for i in range(self._n)],
            self._n, self._n
        )
    
    def get_singular_values(self) -> List[float]:
        """
        Return the one-dimensional array of singular values.
        
        Returns:
            diagonal of S.
        """
        return self._s.copy()
    
    def get_S(self) -> 'Matrix':
        """
        Return the diagonal matrix of singular values.
        
        Returns:
            S
        """
        nu = min(self._m, self._n)
        X = Matrix(nu, self._n)
        S = X.get_array()
        
        for i in range(nu):
            for j in range(self._n):
                S[i][j] = 0.0
            S[i][i] = self._s[i]
        
        return X
    
    def norm2(self) -> float:
        """
        Two norm.
        
        Returns:
            max(S)
        """
        return self._s[0]
    
    def cond(self) -> float:
        """
        Two norm condition number.
        
        Returns:
            max(S) / min(S)
        """
        return self._s[0] / self._s[min(self._m, self._n) - 1]
    
    def rank(self) -> int:
        """
        Effective numerical matrix rank.
        
        Returns:
            Number of nonnegligible singular values.
        """
        eps = 2.0 ** -52.0
        tol = max(self._m, self._n) * self._s[0] * eps
        r = 0
        
        for i in range(len(self._s)):
            if self._s[i] > tol:
                r += 1
        
        return r


# =============================================================================

