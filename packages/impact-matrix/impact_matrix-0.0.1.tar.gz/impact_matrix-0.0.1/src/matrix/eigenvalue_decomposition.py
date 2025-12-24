#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Eigenvalues and eigenvectors of a real matrix.

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

class EigenvalueDecomposition:
    """
    Eigenvalues and eigenvectors of a real matrix.
    
    If A is symmetric, then A = V * D * V' where the eigenvalue matrix D is diagonal
    and the eigenvector matrix V is orthogonal. I.e. A = V.times(D.times(V.transpose()))
    and V.times(V.transpose()) equals the identity matrix.
    
    If A is not symmetric, then the eigenvalue matrix D is block diagonal with
    the real eigenvalues in 1-by-1 blocks and any complex eigenvalues, lambda + i*mu,
    in 2-by-2 blocks, [lambda, mu; -mu, lambda]. The columns of V represent
    the eigenvectors in the sense that A*V = V*D, i.e. A.times(V) equals V.times(D).
    The matrix V may be badly conditioned, or even singular, so the validity of the
    equation A = V*D*inverse(V) depends upon V.cond().
    """
    
    def __init__(self, Arg: 'Matrix'):
        """
        Check for symmetry, then construct the eigenvalue decomposition.
        
        Args:
            Arg: Square matrix.
        """
        A = Arg.get_array()
        self._n = Arg.get_column_dimension()
        n = self._n
        self._V = [[0.0] * n for _ in range(n)]
        self._d = [0.0] * n
        self._e = [0.0] * n
        
        # For complex scalar division
        self._cdivr = 0.0
        self._cdivi = 0.0
        
        self._issymmetric = True
        
        for j in range(n):
            if not self._issymmetric:
                break
            for i in range(n):
                if A[i][j] != A[j][i]:
                    self._issymmetric = False
                    break
        
        if self._issymmetric:
            for i in range(n):
                for j in range(n):
                    self._V[i][j] = A[i][j]
            
            # Tridiagonalize
            self._tred2()
            
            # Diagonalize
            self._tql2()
        else:
            self._H = [[0.0] * n for _ in range(n)]
            self._ort = [0.0] * n
            
            for j in range(n):
                for i in range(n):
                    self._H[i][j] = A[i][j]
            
            # Reduce to Hessenberg form
            self._orthes()
            
            # Reduce Hessenberg to real Schur form
            self._hqr2()
    
    def _cdiv(self, xr: float, xi: float, yr: float, yi: float) -> None:
        """Complex scalar division."""
        if abs(yr) > abs(yi):
            r = yi / yr
            d = yr + r * yi
            self._cdivr = (xr + r * xi) / d
            self._cdivi = (xi - r * xr) / d
        else:
            r = yr / yi
            d = yi + r * yr
            self._cdivr = (r * xr + xi) / d
            self._cdivi = (r * xi - xr) / d
    
    def get_V(self) -> 'Matrix':
        """
        Return the eigenvector matrix.
        
        Returns:
            V
        """
        return Matrix.from_array_with_dims(
            [[self._V[i][j] for j in range(self._n)] for i in range(self._n)],
            self._n, self._n
        )
    
    def get_real_eigenvalues(self) -> List[float]:
        """
        Return the real parts of the eigenvalues.
        
        Returns:
            real(diag(D))
        """
        return self._d.copy()
    
    def get_imag_eigenvalues(self) -> List[float]:
        """
        Return the imaginary parts of the eigenvalues.
        
        Returns:
            imag(diag(D))
        """
        return self._e.copy()
    
    def get_D(self) -> 'Matrix':
        """
        Return the block diagonal eigenvalue matrix.
        
        Returns:
            D
        """
        X = Matrix(self._n, self._n)
        D = X.get_array()
        
        for i in range(self._n):
            for j in range(self._n):
                D[i][j] = 0.0
            D[i][i] = self._d[i]
            
            if self._e[i] > 0:
                D[i][i + 1] = self._e[i]
            elif self._e[i] < 0:
                D[i][i - 1] = self._e[i]
        
        return X
    
    def _tred2(self) -> None:
        """Symmetric Householder reduction to tridiagonal form."""
        n = self._n
        V = self._V
        d = self._d
        e = self._e
        
        for j in range(n):
            d[j] = V[n - 1][j]
        
        # Householder reduction to tridiagonal form
        for i in range(n - 1, 0, -1):
            # Scale to avoid under/overflow
            scale = 0.0
            h = 0.0
            
            for k in range(i):
                scale += abs(d[k])
            
            if scale == 0.0:
                e[i] = d[i - 1]
                
                for j in range(i):
                    d[j] = V[i - 1][j]
                    V[i][j] = 0.0
                    V[j][i] = 0.0
            else:
                # Generate Householder vector
                for k in range(i):
                    d[k] /= scale
                    h += d[k] * d[k]
                
                f = d[i - 1]
                g = math.sqrt(h)
                
                if f > 0:
                    g = -g
                
                e[i] = scale * g
                h = h - f * g
                d[i - 1] = f - g
                
                for j in range(i):
                    e[j] = 0.0
                
                # Apply similarity transformation to remaining columns
                for j in range(i):
                    f = d[j]
                    V[j][i] = f
                    g = e[j] + V[j][j] * f
                    
                    for k in range(j + 1, i):
                        g += V[k][j] * d[k]
                        e[k] += V[k][j] * f
                    
                    e[j] = g
                
                f = 0.0
                
                for j in range(i):
                    e[j] /= h
                    f += e[j] * d[j]
                
                hh = f / (h + h)
                
                for j in range(i):
                    e[j] -= hh * d[j]
                
                for j in range(i):
                    f = d[j]
                    g = e[j]
                    
                    for k in range(j, i):
                        V[k][j] -= (f * e[k] + g * d[k])
                    
                    d[j] = V[i - 1][j]
                    V[i][j] = 0.0
            
            d[i] = h
        
        # Accumulate transformations
        for i in range(n - 1):
            V[n - 1][i] = V[i][i]
            V[i][i] = 1.0
            
            h = d[i + 1]
            
            if h != 0.0:
                for k in range(i + 1):
                    d[k] = V[k][i + 1] / h
                
                for j in range(i + 1):
                    g = 0.0
                    
                    for k in range(i + 1):
                        g += V[k][i + 1] * V[k][j]
                    
                    for k in range(i + 1):
                        V[k][j] -= g * d[k]
            
            for k in range(i + 1):
                V[k][i + 1] = 0.0
        
        for j in range(n):
            d[j] = V[n - 1][j]
            V[n - 1][j] = 0.0
        
        V[n - 1][n - 1] = 1.0
        e[0] = 0.0
    
    def _tql2(self) -> None:
        """Symmetric tridiagonal QL algorithm."""
        n = self._n
        V = self._V
        d = self._d
        e = self._e
        
        for i in range(1, n):
            e[i - 1] = e[i]
        e[n - 1] = 0.0
        
        f = 0.0
        tst1 = 0.0
        eps = 2.0 ** -52.0
        
        for l in range(n):
            # Find small subdiagonal element
            tst1 = max(tst1, abs(d[l]) + abs(e[l]))
            
            m = l
            while m < n:
                if abs(e[m]) <= eps * tst1:
                    break
                m += 1
            
            # If m == l, d[l] is an eigenvalue, otherwise iterate
            if m > l:
                iter_count = 0
                
                while True:
                    iter_count += 1
                    
                    # Compute implicit shift
                    g = d[l]
                    p = (d[l + 1] - g) / (2.0 * e[l])
                    r = Maths.hypot(p, 1.0)
                    
                    if p < 0:
                        r = -r
                    
                    d[l] = e[l] / (p + r)
                    d[l + 1] = e[l] * (p + r)
                    
                    dl1 = d[l + 1]
                    h = g - d[l]
                    
                    for i in range(l + 2, n):
                        d[i] -= h
                    
                    f += h
                    
                    # Implicit QL transformation
                    p = d[m]
                    c = 1.0
                    c2 = c
                    c3 = c
                    el1 = e[l + 1]
                    s = 0.0
                    s2 = 0.0
                    
                    for i in range(m - 1, l - 1, -1):
                        c3 = c2
                        c2 = c
                        s2 = s
                        g = c * e[i]
                        h = c * p
                        r = Maths.hypot(p, e[i])
                        e[i + 1] = s * r
                        s = e[i] / r
                        c = p / r
                        p = c * d[i] - s * g
                        d[i + 1] = h + s * (c * g + s * d[i])
                        
                        # Accumulate transformation
                        for k in range(n):
                            h = V[k][i + 1]
                            V[k][i + 1] = s * V[k][i] + c * h
                            V[k][i] = c * V[k][i] - s * h
                    
                    p = -s * s2 * c3 * el1 * e[l] / dl1
                    e[l] = s * p
                    d[l] = c * p
                    
                    # Check for convergence
                    if abs(e[l]) <= eps * tst1:
                        break
            
            d[l] = d[l] + f
            e[l] = 0.0
        
        # Sort eigenvalues and corresponding vectors
        for i in range(n - 1):
            k = i
            p = d[i]
            
            for j in range(i + 1, n):
                if d[j] < p:
                    k = j
                    p = d[j]
            
            if k != i:
                d[k] = d[i]
                d[i] = p
                
                for j in range(n):
                    p = V[j][i]
                    V[j][i] = V[j][k]
                    V[j][k] = p
    
    def _orthes(self) -> None:
        """Nonsymmetric reduction to Hessenberg form."""
        n = self._n
        V = self._V
        H = self._H
        ort = self._ort
        
        low = 0
        high = n - 1
        
        for m in range(low + 1, high):
            # Scale column
            scale = 0.0
            
            for i in range(m, high + 1):
                scale += abs(H[i][m - 1])
            
            if scale != 0.0:
                # Compute Householder transformation
                h = 0.0
                
                for i in range(high, m - 1, -1):
                    ort[i] = H[i][m - 1] / scale
                    h += ort[i] * ort[i]
                
                g = math.sqrt(h)
                
                if ort[m] > 0:
                    g = -g
                
                h = h - ort[m] * g
                ort[m] = ort[m] - g
                
                # Apply Householder similarity transformation
                # H = (I - u*u'/h) * H * (I - u*u'/h)
                for j in range(m, n):
                    f = 0.0
                    
                    for i in range(high, m - 1, -1):
                        f += ort[i] * H[i][j]
                    
                    f = f / h
                    
                    for i in range(m, high + 1):
                        H[i][j] -= f * ort[i]
                
                for i in range(high + 1):
                    f = 0.0
                    
                    for j in range(high, m - 1, -1):
                        f += ort[j] * H[i][j]
                    
                    f = f / h
                    
                    for j in range(m, high + 1):
                        H[i][j] -= f * ort[j]
                
                ort[m] = scale * ort[m]
                H[m][m - 1] = scale * g
        
        # Accumulate transformations (Algol's ortran)
        for i in range(n):
            for j in range(n):
                V[i][j] = 1.0 if i == j else 0.0
        
        for m in range(high - 1, low, -1):
            if H[m][m - 1] != 0.0:
                for i in range(m + 1, high + 1):
                    ort[i] = H[i][m - 1]
                
                for j in range(m, high + 1):
                    g = 0.0
                    
                    for i in range(m, high + 1):
                        g += ort[i] * V[i][j]
                    
                    # Double division avoids possible underflow
                    g = (g / ort[m]) / H[m][m - 1]
                    
                    for i in range(m, high + 1):
                        V[i][j] += g * ort[i]
    
    def _hqr2(self) -> None:
        """Nonsymmetric reduction from Hessenberg to real Schur form."""
        nn = self._n
        V = self._V
        H = self._H
        d = self._d
        e = self._e
        
        n = nn - 1
        low = 0
        high = nn - 1
        eps = 2.0 ** -52.0
        exshift = 0.0
        p = 0.0
        q = 0.0
        r = 0.0
        s = 0.0
        z = 0.0
        
        # Store roots isolated by balanc and compute matrix norm
        norm = 0.0
        
        for i in range(nn):
            if i < low or i > high:
                d[i] = H[i][i]
                e[i] = 0.0
            
            for j in range(max(i - 1, 0), nn):
                norm += abs(H[i][j])
        
        # Outer loop over eigenvalue index
        iter_count = 0
        
        while n >= low:
            # Look for single small sub-diagonal element
            l = n
            
            while l > low:
                s = abs(H[l - 1][l - 1]) + abs(H[l][l])
                
                if s == 0.0:
                    s = norm
                
                if abs(H[l][l - 1]) < eps * s:
                    break
                
                l -= 1
            
            # Check for convergence
            # One root found
            if l == n:
                H[n][n] = H[n][n] + exshift
                d[n] = H[n][n]
                e[n] = 0.0
                n -= 1
                iter_count = 0
            
            # Two roots found
            elif l == n - 1:
                w = H[n][n - 1] * H[n - 1][n]
                p = (H[n - 1][n - 1] - H[n][n]) / 2.0
                q = p * p + w
                z = math.sqrt(abs(q))
                H[n][n] = H[n][n] + exshift
                H[n - 1][n - 1] = H[n - 1][n - 1] + exshift
                x = H[n][n]
                
                # Real pair
                if q >= 0:
                    if p >= 0:
                        z = p + z
                    else:
                        z = p - z
                    
                    d[n - 1] = x + z
                    d[n] = d[n - 1]
                    
                    if z != 0.0:
                        d[n] = x - w / z
                    
                    e[n - 1] = 0.0
                    e[n] = 0.0
                    x = H[n][n - 1]
                    s = abs(x) + abs(z)
                    p = x / s
                    q = z / s
                    r = math.sqrt(p * p + q * q)
                    p = p / r
                    q = q / r
                    
                    # Row modification
                    for j in range(n - 1, nn):
                        z = H[n - 1][j]
                        H[n - 1][j] = q * z + p * H[n][j]
                        H[n][j] = q * H[n][j] - p * z
                    
                    # Column modification
                    for i in range(n + 1):
                        z = H[i][n - 1]
                        H[i][n - 1] = q * z + p * H[i][n]
                        H[i][n] = q * H[i][n] - p * z
                    
                    # Accumulate transformations
                    for i in range(low, high + 1):
                        z = V[i][n - 1]
                        V[i][n - 1] = q * z + p * V[i][n]
                        V[i][n] = q * V[i][n] - p * z
                
                # Complex pair
                else:
                    d[n - 1] = x + p
                    d[n] = x + p
                    e[n - 1] = z
                    e[n] = -z
                
                n = n - 2
                iter_count = 0
            
            # No convergence yet
            else:
                # Form shift
                x = H[n][n]
                y = 0.0
                w = 0.0
                
                if l < n:
                    y = H[n - 1][n - 1]
                    w = H[n][n - 1] * H[n - 1][n]
                
                # Wilkinson's original ad hoc shift
                if iter_count == 10:
                    exshift += x
                    
                    for i in range(low, n + 1):
                        H[i][i] -= x
                    
                    s = abs(H[n][n - 1]) + abs(H[n - 1][n - 2])
                    x = y = 0.75 * s
                    w = -0.4375 * s * s
                
                # MATLAB's new ad hoc shift
                if iter_count == 30:
                    s = (y - x) / 2.0
                    s = s * s + w
                    
                    if s > 0:
                        s = math.sqrt(s)
                        
                        if y < x:
                            s = -s
                        
                        s = x - w / ((y - x) / 2.0 + s)
                        
                        for i in range(low, n + 1):
                            H[i][i] -= s
                        
                        exshift += s
                        x = y = w = 0.964
                
                iter_count += 1
                
                # Look for two consecutive small sub-diagonal elements
                m = n - 2
                
                while m >= l:
                    z = H[m][m]
                    r = x - z
                    s = y - z
                    p = (r * s - w) / H[m + 1][m] + H[m][m + 1]
                    q = H[m + 1][m + 1] - z - r - s
                    r = H[m + 2][m + 1]
                    s = abs(p) + abs(q) + abs(r)
                    p = p / s
                    q = q / s
                    r = r / s
                    
                    if m == l:
                        break
                    
                    if (abs(H[m][m - 1]) * (abs(q) + abs(r)) < 
                        eps * abs(p) * (abs(H[m - 1][m - 1]) + abs(z) + abs(H[m + 1][m + 1]))):
                        break
                    
                    m -= 1
                
                for i in range(m + 2, n + 1):
                    H[i][i - 2] = 0.0
                    
                    if i > m + 2:
                        H[i][i - 3] = 0.0
                
                # Double QR step involving rows l:n and columns m:n
                for k in range(m, n):
                    notlast = (k != n - 1)
                    
                    if k != m:
                        p = H[k][k - 1]
                        q = H[k + 1][k - 1]
                        r = H[k + 2][k - 1] if notlast else 0.0
                        x = abs(p) + abs(q) + abs(r)
                        
                        if x != 0.0:
                            p = p / x
                            q = q / x
                            r = r / x
                    
                    if x == 0.0:
                        break
                    
                    s = math.sqrt(p * p + q * q + r * r)
                    
                    if p < 0:
                        s = -s
                    
                    if s != 0:
                        if k != m:
                            H[k][k - 1] = -s * x
                        elif l != m:
                            H[k][k - 1] = -H[k][k - 1]
                        
                        p = p + s
                        x = p / s
                        y = q / s
                        z = r / s
                        q = q / p
                        r = r / p
                        
                        # Row modification
                        for j in range(k, nn):
                            p = H[k][j] + q * H[k + 1][j]
                            
                            if notlast:
                                p = p + r * H[k + 2][j]
                                H[k + 2][j] = H[k + 2][j] - p * z
                            
                            H[k][j] = H[k][j] - p * x
                            H[k + 1][j] = H[k + 1][j] - p * y
                        
                        # Column modification
                        for i in range(min(n, k + 3) + 1):
                            p = x * H[i][k] + y * H[i][k + 1]
                            
                            if notlast:
                                p = p + z * H[i][k + 2]
                                H[i][k + 2] = H[i][k + 2] - p * r
                            
                            H[i][k] = H[i][k] - p
                            H[i][k + 1] = H[i][k + 1] - p * q
                        
                        # Accumulate transformations
                        for i in range(low, high + 1):
                            p = x * V[i][k] + y * V[i][k + 1]
                            
                            if notlast:
                                p = p + z * V[i][k + 2]
                                V[i][k + 2] = V[i][k + 2] - p * r
                            
                            V[i][k] = V[i][k] - p
                            V[i][k + 1] = V[i][k + 1] - p * q
        
        # Backsubstitute to find vectors of upper triangular form
        if norm == 0.0:
            return
        
        for n in range(nn - 1, -1, -1):
            p = d[n]
            q = e[n]
            
            # Real vector
            if q == 0:
                l = n
                H[n][n] = 1.0
                
                for i in range(n - 1, -1, -1):
                    w = H[i][i] - p
                    r = 0.0
                    
                    for j in range(l, n + 1):
                        r = r + H[i][j] * H[j][n]
                    
                    if e[i] < 0.0:
                        z = w
                        s = r
                    else:
                        l = i
                        
                        if e[i] == 0.0:
                            if w != 0.0:
                                H[i][n] = -r / w
                            else:
                                H[i][n] = -r / (eps * norm)
                        
                        # Solve real equations
                        else:
                            x = H[i][i + 1]
                            y = H[i + 1][i]
                            q = (d[i] - p) * (d[i] - p) + e[i] * e[i]
                            t = (x * s - z * r) / q
                            H[i][n] = t
                            
                            if abs(x) > abs(z):
                                H[i + 1][n] = (-r - w * t) / x
                            else:
                                H[i + 1][n] = (-s - y * t) / z
                        
                        # Overflow control
                        t = abs(H[i][n])
                        
                        if (eps * t) * t > 1:
                            for j in range(i, n + 1):
                                H[j][n] = H[j][n] / t
            
            # Complex vector
            elif q < 0:
                l = n - 1
                
                # Last vector component imaginary so matrix is triangular
                if abs(H[n][n - 1]) > abs(H[n - 1][n]):
                    H[n - 1][n - 1] = q / H[n][n - 1]
                    H[n - 1][n] = -(H[n][n] - p) / H[n][n - 1]
                else:
                    self._cdiv(0.0, -H[n - 1][n], H[n - 1][n - 1] - p, q)
                    H[n - 1][n - 1] = self._cdivr
                    H[n - 1][n] = self._cdivi
                
                H[n][n - 1] = 0.0
                H[n][n] = 1.0
                
                for i in range(n - 2, -1, -1):
                    ra = 0.0
                    sa = 0.0
                    
                    for j in range(l, n + 1):
                        ra = ra + H[i][j] * H[j][n - 1]
                        sa = sa + H[i][j] * H[j][n]
                    
                    w = H[i][i] - p
                    
                    if e[i] < 0.0:
                        z = w
                        r = ra
                        s = sa
                    else:
                        l = i
                        
                        if e[i] == 0:
                            self._cdiv(-ra, -sa, w, q)
                            H[i][n - 1] = self._cdivr
                            H[i][n] = self._cdivi
                        else:
                            # Solve complex equations
                            x = H[i][i + 1]
                            y = H[i + 1][i]
                            vr = (d[i] - p) * (d[i] - p) + e[i] * e[i] - q * q
                            vi = (d[i] - p) * 2.0 * q
                            
                            if vr == 0.0 and vi == 0.0:
                                vr = eps * norm * (abs(w) + abs(q) + abs(x) + abs(y) + abs(z))
                            
                            self._cdiv(x * r - z * ra + q * sa,
                                       x * s - z * sa - q * ra, vr, vi)
                            H[i][n - 1] = self._cdivr
                            H[i][n] = self._cdivi
                            
                            if abs(x) > abs(z) + abs(q):
                                H[i + 1][n - 1] = (-ra - w * H[i][n - 1] + q * H[i][n]) / x
                                H[i + 1][n] = (-sa - w * H[i][n] - q * H[i][n - 1]) / x
                            else:
                                self._cdiv(-r - y * H[i][n - 1], -s - y * H[i][n], z, q)
                                H[i + 1][n - 1] = self._cdivr
                                H[i + 1][n] = self._cdivi
                        
                        # Overflow control
                        t = max(abs(H[i][n - 1]), abs(H[i][n]))
                        
                        if (eps * t) * t > 1:
                            for j in range(i, n + 1):
                                H[j][n - 1] = H[j][n - 1] / t
                                H[j][n] = H[j][n] / t
        
        # Vectors of isolated roots
        for i in range(nn):
            if i < low or i > high:
                for j in range(i, nn):
                    V[i][j] = H[i][j]
        
        # Back transformation to get eigenvectors of original matrix
        for j in range(nn - 1, low - 1, -1):
            for i in range(low, high + 1):
                z = 0.0
                
                for k in range(low, min(j, high) + 1):
                    z = z + V[i][k] * H[k][j]
                
                V[i][j] = z


# =============================================================================

