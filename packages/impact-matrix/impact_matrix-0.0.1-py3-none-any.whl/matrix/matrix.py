#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
Matrix - Python port of JAMA Matrix class.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

The Java Matrix Class provides the fundamental operations of numerical linear
algebra. Various constructors create Matrices from two dimensional arrays of
double precision floating point numbers. Various "gets" and "sets" provide
access to submatrices and matrix elements. Several methods implement basic
matrix arithmetic, including matrix addition and multiplication, matrix
norms, and element-by-element array operations.

Original authors: The MathWorks, Inc. and the National Institute of Standards
and Technology.
"""
# -----------------------------------------------------------------------------

from __future__ import annotations

import math
import random
import copy

from typing import (
    List,
    Optional,
    TextIO,
    Union,
    Sequence
)

from io import StringIO


# -----------------------------------------------------------------------------

if __name__ == "__main__":

    from maths                         import Maths

else:

    from .maths                         import Maths


# =============================================================================
# Stub classes for uka package references (to be implemented later)
# =============================================================================

class Printable:
    """Stub for uka.util.Printable interface."""
    pass


class ToString:
    """Stub for uka.util.ToString."""
    def append(self, name: str, value) -> None:
        pass


class Transportable:
    """Stub for uka.transport.Transportable interface."""
    pass


class Patchable:
    """Stub for uka.patch.Patchable interface."""
    pass


class PatchOutput:
    """Stub for uka.patch.PatchOutput."""
    def write_diff(self, diff: float, default: float) -> bool:
        return False


class PatchInput:
    """Stub for uka.patch.PatchInput."""
    def has_diff(self) -> bool:
        return False
    
    def get_diff_as_double(self) -> float:
        return 0.0


class ReferenceConsumer:
    """Stub for uka.patch.ReferenceConsumer."""
    pass


class ReferenceFilter:
    """Stub for uka.patch.ReferenceFilter."""
    pass


# =============================================================================
# Matrix class
# -----------------------------------------------------------------------------

class Matrix:
    """
    Jama = Java Matrix class (Python port).
    
    The Matrix Class provides the fundamental operations of numerical linear
    algebra. Various constructors create Matrices from two dimensional arrays of
    double precision floating point numbers. Various "gets" and "sets" provide
    access to submatrices and matrix elements. Several methods implement basic
    matrix arithmetic, including matrix addition and multiplication, matrix
    norms, and element-by-element array operations.
    
    Five fundamental matrix decompositions, which consist of pairs or triples of
    matrices, permutation vectors, and the like, produce results in five
    decomposition classes. These decompositions are accessed by the Matrix class
    to compute solutions of simultaneous linear equations, determinants, inverses
    and other matrix functions.
    
    Example of use:
        Solve a linear system A x = b and compute the residual norm, ||b - A x||.
        
        vals = [[1., 2., 3], [4., 5., 6.], [7., 8., 10.]]
        A = Matrix.from_2d_array(vals)
        b = Matrix.random(3, 1)
        x = A.solve(b)
        r = A.times(x).minus(b)
        rnorm = r.norm_inf()
    """
    # -------------------------------------------------------------------------
    
    def __init__(self, m: int, n: int, s: Optional[float] = None):
        """
        Construct an m-by-n matrix.
        
        Args:
            m: Number of rows.
            n: Number of columns.
            s: Optional scalar value to fill the matrix. If None, fills with zeros.
        """
        self._m = m
        self._n = n
        if s is None:
            self._A = [[0.0] * n for _ in range(m)]
        else:
            self._A = [[s] * n for _ in range(m)]
    
    # -------------------------------------------------------------------------
    # Alternative constructors (class methods)
    # -------------------------------------------------------------------------
    
    @classmethod
    def from_2d_array(cls, A: List[List[float]], copy: bool = False) -> Matrix:
        """
        Construct a matrix from a 2-D array.
        
        Args:
            A: Two-dimensional array of floats.
            copy: If True, makes a deep copy of the array.
        
        Returns:
            A new Matrix instance.
        
        Raises:
            ValueError: If all rows don't have the same length.
        """
        m = len(A)
        if m == 0:
            return cls(0, 0)
        n = len(A[0])
        
        for i in range(m):
            if len(A[i]) != n:
                raise ValueError("All rows must have the same length.")
        
        matrix = cls(m, n)
        if copy:
            matrix._A = [[float(A[i][j]) for j in range(n)] for i in range(m)]
        else:
            matrix._A = A
        return matrix
    
    # -------------------------------------------------------------------------

    @classmethod
    def from_1d_packed(cls, vals: List[float], m: int) -> Matrix:
        """
        Construct a matrix from a one-dimensional packed array.
        
        Args:
            vals: One-dimensional array of floats, packed by columns (Fortran style).
            m: Number of rows.
        
        Returns:
            A new Matrix instance.
        
        Raises:
            ValueError: If array length is not a multiple of m.
        """
        n = len(vals) // m if m != 0 else 0
        
        if m * n != len(vals):
            raise ValueError("Array length must be a multiple of m.")
        
        matrix = cls(m, n)
        for i in range(m):
            for j in range(n):
                matrix._A[i][j] = vals[i + j * m]
        
        return matrix
    
    # -------------------------------------------------------------------------

    @classmethod
    def from_array_with_dims(cls, A: List[List[float]], m: int, n: int) -> Matrix:
        """
        Construct a matrix quickly without checking arguments.
        
        Args:
            A: Two-dimensional array of floats.
            m: Number of rows.
            n: Number of columns.
        
        Returns:
            A new Matrix instance.
        """
        matrix = cls.__new__(cls)
        matrix._A = A
        matrix._m = m
        matrix._n = n
        return matrix

    # -------------------------------------------------------------------------
    
    @classmethod
    def construct_with_copy(cls, A: List[List[float]]) -> Matrix:
        """
        Construct a matrix from a copy of a 2-D array.
        
        Args:
            A: Two-dimensional array of floats.
        
        Returns:
            A new Matrix instance with copied data.
        
        Raises:
            ValueError: If all rows don't have the same length.
        """
        return cls.from_2d_array(A, copy=True)
    
    # -------------------------------------------------------------------------
    # Static factory methods
    # -------------------------------------------------------------------------
    
    @staticmethod
    def identity(m: int, n: int) -> Matrix:
        """
        Generate identity matrix.
        
        Args:
            m: Number of rows.
            n: Number of columns.
        
        Returns:
            An m-by-n matrix with ones on the diagonal and zeros elsewhere.
        """
        A = Matrix(m, n)
        for i in range(min(m, n)):
            A._A[i][i] = 1.0
        return A
    
    # -------------------------------------------------------------------------
    
    @staticmethod
    def random(m: int, n: int) -> Matrix:
        """
        Generate matrix with random elements.
        
        Args:
            m: Number of rows.
            n: Number of columns.
        
        Returns:
            An m-by-n matrix with uniformly distributed random elements in [0, 1).
        """
        A = Matrix(m, n)
        for i in range(m):
            for j in range(n):
                A._A[i][j] = random.random()
        return A
    
    # -------------------------------------------------------------------------
    
    @staticmethod
    def read(input_stream: TextIO) -> Matrix:
        """
        Read a matrix from a stream.
        
        Elements are separated by whitespace, all the elements for each row
        appear on a single line, the last row is followed by a blank line.
        
        Args:
            input_stream: Input text stream.
        
        Returns:
            A new Matrix instance.
        
        Raises:
            IOError: If there's an error reading or parsing the input.
        """
        rows = []
        n = None
        
        for line in input_stream:
            line = line.strip()
            if not line:
                if rows:  # End of matrix
                    break
                continue  # Skip initial empty lines
            
            values = [float(x) for x in line.split()]
            if n is None:
                n = len(values)
            elif len(values) != n:
                raise IOError(f"Row {len(rows) + 1} has {len(values)} elements, expected {n}")
            rows.append(values)
        
        if not rows:
            raise IOError("Unexpected EOF on matrix read.")
        
        return Matrix.from_2d_array(rows)
    
    # -------------------------------------------------------------------------
    # Dimension accessors
    # -------------------------------------------------------------------------
    
    @property
    def m(self) -> int:
        """Number of rows."""
        return self._m
    
    # -------------------------------------------------------------------------
    
    @property
    def n(self) -> int:
        """Number of columns."""
        return self._n
    
    # -------------------------------------------------------------------------
    
    def get_row_dimension(self) -> int:
        """Get row dimension."""
        return self._m
    
    # -------------------------------------------------------------------------
    
    def get_column_dimension(self) -> int:
        """Get column dimension."""
        return self._n
    
    # -------------------------------------------------------------------------
    # Element access
    # -------------------------------------------------------------------------
    
    def get(self, i: int, j: int) -> float:
        """
        Get a single element.
        
        Args:
            i: Row index.
            j: Column index.
        
        Returns:
            A(i,j)
        """
        return self._A[i][j]
    
    # -------------------------------------------------------------------------
    
    def set(self, i: int, j: int, s: float) -> None:
        """
        Set a single element.
        
        Args:
            i: Row index.
            j: Column index.
            s: Value to set at A(i,j).
        """
        self._A[i][j] = s
    
    # -------------------------------------------------------------------------
    
    def get_array(self) -> List[List[float]]:
        """
        Access the internal two-dimensional array.
        
        Returns:
            Pointer to the two-dimensional array of matrix elements.
        """
        return self._A
    
    # -------------------------------------------------------------------------
    
    def get_array_copy(self) -> List[List[float]]:
        """
        Copy the internal two-dimensional array.
        
        Returns:
            Two-dimensional array copy of matrix elements.
        """
        return [[self._A[i][j] for j in range(self._n)] for i in range(self._m)]
    
    # -------------------------------------------------------------------------
    
    def get_column_packed_copy(self) -> List[float]:
        """
        Make a one-dimensional column packed copy of the internal array.
        
        Returns:
            Matrix elements packed in a one-dimensional array by columns.
        """
        vals = [0.0] * (self._m * self._n)
        for i in range(self._m):
            for j in range(self._n):
                vals[i + j * self._m] = self._A[i][j]
        return vals
    
    # -------------------------------------------------------------------------
    
    def get_row_packed_copy(self) -> List[float]:
        """
        Make a one-dimensional row packed copy of the internal array.
        
        Returns:
            Matrix elements packed in a one-dimensional array by rows.
        """
        vals = [0.0] * (self._m * self._n)
        for i in range(self._m):
            for j in range(self._n):
                vals[i * self._n + j] = self._A[i][j]
        return vals
    
    # -------------------------------------------------------------------------
    # Submatrix access
    # -------------------------------------------------------------------------
    
    def get_matrix(self, i0: int, i1: int, j0: int, j1: int) -> Matrix:
        """
        Get a submatrix.
        
        Args:
            i0: Initial row index.
            i1: Final row index (inclusive).
            j0: Initial column index.
            j1: Final column index (inclusive).
        
        Returns:
            A(i0:i1, j0:j1)
        """
        X = Matrix(i1 - i0 + 1, j1 - j0 + 1)
        try:
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    X._A[i - i0][j - j0] = self._A[i][j]
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
        return X
    
    # -------------------------------------------------------------------------
    
    def get_matrix_by_indices(self, r: List[int], c: List[int]) -> Matrix:
        """
        Get a submatrix.
        
        Args:
            r: Array of row indices.
            c: Array of column indices.
        
        Returns:
            A(r(:), c(:))
        """
        X = Matrix(len(r), len(c))
        try:
            for i, ri in enumerate(r):
                for j, cj in enumerate(c):
                    X._A[i][j] = self._A[ri][cj]
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
        return X
    
    # -------------------------------------------------------------------------
    
    def get_matrix_rows_cols(self, i0: int, i1: int, c: List[int]) -> Matrix:
        """
        Get a submatrix.
        
        Args:
            i0: Initial row index.
            i1: Final row index (inclusive).
            c: Array of column indices.
        
        Returns:
            A(i0:i1, c(:))
        """
        X = Matrix(i1 - i0 + 1, len(c))
        try:
            for i in range(i0, i1 + 1):
                for j, cj in enumerate(c):
                    X._A[i - i0][j] = self._A[i][cj]
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
        return X
    
    # -------------------------------------------------------------------------
    
    def get_matrix_indices_cols(self, r: List[int], j0: int, j1: int) -> Matrix:
        """
        Get a submatrix.
        
        Args:
            r: Array of row indices.
            j0: Initial column index.
            j1: Final column index (inclusive).
        
        Returns:
            A(r(:), j0:j1)
        """
        X = Matrix(len(r), j1 - j0 + 1)
        try:
            for i, ri in enumerate(r):
                for j in range(j0, j1 + 1):
                    X._A[i][j - j0] = self._A[ri][j]
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
        return X
    
    # -------------------------------------------------------------------------
    # Submatrix setters
    # -------------------------------------------------------------------------
    
    def set_matrix(self, X: Matrix) -> None:
        """
        Set the complete data from another matrix.
        
        Args:
            X: Other matrix.
        """
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] = X.get(i, j)
    
    # -------------------------------------------------------------------------
    
    def set_matrix_range(self, i0: int, i1: int, j0: int, j1: int, X: Matrix) -> None:
        """
        Set a submatrix.
        
        Args:
            i0: Initial row index.
            i1: Final row index (inclusive).
            j0: Initial column index.
            j1: Final column index (inclusive).
            X: Submatrix A(i0:i1, j0:j1).
        """
        try:
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    self._A[i][j] = X.get(i - i0, j - j0)
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
    
    # -------------------------------------------------------------------------
    
    def set_matrix_by_indices(self, r: List[int], c: List[int], X: Matrix) -> None:
        """
        Set a submatrix.
        
        Args:
            r: Array of row indices.
            c: Array of column indices.
            X: Submatrix A(r(:), c(:)).
        """
        try:
            for i, ri in enumerate(r):
                for j, cj in enumerate(c):
                    self._A[ri][cj] = X.get(i, j)
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
    
    # -------------------------------------------------------------------------
    
    def set_matrix_rows_cols(self, i0: int, i1: int, c: List[int], X: Matrix) -> None:
        """
        Set a submatrix.
        
        Args:
            i0: Initial row index.
            i1: Final row index (inclusive).
            c: Array of column indices.
            X: Submatrix A(i0:i1, c(:)).
        """
        try:
            for i in range(i0, i1 + 1):
                for j, cj in enumerate(c):
                    self._A[i][cj] = X.get(i - i0, j)
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
    
    # -------------------------------------------------------------------------
    
    def set_matrix_indices_cols(self, r: List[int], j0: int, j1: int, X: Matrix) -> None:
        """
        Set a submatrix.
        
        Args:
            r: Array of row indices.
            j0: Initial column index.
            j1: Final column index (inclusive).
            X: Submatrix A(r(:), j0:j1).
        """
        try:
            for i, ri in enumerate(r):
                for j in range(j0, j1 + 1):
                    self._A[ri][j] = X.get(i, j - j0)
        except IndexError:
            raise IndexError("Submatrix indices out of bounds")
    
    # -------------------------------------------------------------------------
    # Matrix operations
    # -------------------------------------------------------------------------
    
    def copy(self) -> Matrix:
        """Make a deep copy of the matrix."""
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = self._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def __copy__(self) -> Matrix:
        """Shallow copy (returns deep copy for consistency)."""
        return self.copy()
    
    # -------------------------------------------------------------------------
    
    def __deepcopy__(self, memo) -> Matrix:
        """Deep copy."""
        return self.copy()
    
    # -------------------------------------------------------------------------
    
    def transpose(self) -> Matrix:
        """
        Matrix transpose.
        
        Returns:
            A' (transpose of A)
        """
        X = Matrix(self._n, self._m)
        for i in range(self._m):
            for j in range(self._n):
                X._A[j][i] = self._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def uminus(self) -> Matrix:
        """
        Unary minus.
        
        Returns:
            -A
        """
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = -self._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def __neg__(self) -> Matrix:
        """Unary minus operator."""
        return self.uminus()
    
    # -------------------------------------------------------------------------
    # Matrix arithmetic
    # -------------------------------------------------------------------------
    
    def plus(self, B: Matrix) -> Matrix:
        """
        C = A + B
        
        Args:
            B: Another matrix.
        
        Returns:
            A + B
        """
        self._check_matrix_dimensions(B)
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = self._A[i][j] + B._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def __add__(self, B: Matrix) -> Matrix:
        """Addition operator."""
        return self.plus(B)
    
    # -------------------------------------------------------------------------
    
    def plus_equals(self, B: Matrix) -> Matrix:
        """
        A = A + B
        
        Args:
            B: Another matrix.
        
        Returns:
            A + B (modifies self in place)
        """
        self._check_matrix_dimensions(B)
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] += B._A[i][j]
        return self
    
    # -------------------------------------------------------------------------
    
    def __iadd__(self, B: Matrix) -> Matrix:
        """In-place addition operator."""
        return self.plus_equals(B)
    
    # -------------------------------------------------------------------------
    
    def minus(self, B: Matrix) -> Matrix:
        """
        C = A - B
        
        Args:
            B: Another matrix.
        
        Returns:
            A - B
        """
        self._check_matrix_dimensions(B)
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = self._A[i][j] - B._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def __sub__(self, B: Matrix) -> Matrix:
        """Subtraction operator."""
        return self.minus(B)
    
    # -------------------------------------------------------------------------
    
    def minus_equals(self, B: Matrix) -> Matrix:
        """
        A = A - B
        
        Args:
            B: Another matrix.
        
        Returns:
            A - B (modifies self in place)
        """
        self._check_matrix_dimensions(B)
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] -= B._A[i][j]
        return self
    
    # -------------------------------------------------------------------------
    
    def __isub__(self, B: Matrix) -> Matrix:
        """In-place subtraction operator."""
        return self.minus_equals(B)
    
    # -------------------------------------------------------------------------
    
    def times(self, B: Union[Matrix, float]) -> Matrix:
        """
        Matrix multiplication or scalar multiplication.
        
        Args:
            B: Another matrix or a scalar.
        
        Returns:
            A * B (matrix product) or s * A (scalar multiplication)
        """
        if isinstance(B, (int, float)):
            return self._times_scalar(B)
        return self._times_matrix(B)
    
    # -------------------------------------------------------------------------
    
    def _times_scalar(self, s: float) -> Matrix:
        """Multiply matrix by a scalar, C = s * A"""
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = s * self._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def _times_matrix(self, B: Matrix) -> Matrix:
        """Linear algebraic matrix multiplication, A * B"""
        if B._m != self._n:
            raise ValueError("Matrix inner dimensions must agree.")
        
        X = Matrix(self._m, B._n)
        Bcolj = [0.0] * self._n
        
        for j in range(B._n):
            for k in range(self._n):
                Bcolj[k] = B._A[k][j]
            
            for i in range(self._m):
                Arowi = self._A[i]
                s = 0.0
                for k in range(self._n):
                    s += Arowi[k] * Bcolj[k]
                X._A[i][j] = s
        
        return X
    
    # -------------------------------------------------------------------------
    
    def __mul__(self, B: Union[Matrix, float]) -> Matrix:
        """Multiplication operator."""
        return self.times(B)
    
    # -------------------------------------------------------------------------
    
    def __rmul__(self, s: float) -> Matrix:
        """Right multiplication by scalar."""
        return self._times_scalar(s)
    
    # -------------------------------------------------------------------------
    
    def times_equals(self, s: float) -> Matrix:
        """
        Multiply matrix by a scalar in place, A = s * A
        
        Args:
            s: Scalar.
        
        Returns:
            s * A (modifies self in place)
        """
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] *= s
        return self
    
    # -------------------------------------------------------------------------
    
    def __imul__(self, s: float) -> Matrix:
        """In-place scalar multiplication."""
        return self.times_equals(s)
    
    # -------------------------------------------------------------------------
    # Element-by-element operations
    # -------------------------------------------------------------------------
    
    def array_times(self, B: Matrix) -> Matrix:
        """
        Element-by-element multiplication, C = A .* B
        
        Args:
            B: Another matrix.
        
        Returns:
            A .* B
        """
        self._check_matrix_dimensions(B)
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = self._A[i][j] * B._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def array_times_equals(self, B: Matrix) -> Matrix:
        """
        Element-by-element multiplication in place, A = A .* B
        
        Args:
            B: Another matrix.
        
        Returns:
            A .* B (modifies self in place)
        """
        self._check_matrix_dimensions(B)
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] *= B._A[i][j]
        return self
    
    # -------------------------------------------------------------------------
    
    def array_right_divide(self, B: Matrix) -> Matrix:
        """
        Element-by-element right division, C = A ./ B
        
        Args:
            B: Another matrix.
        
        Returns:
            A ./ B
        """
        self._check_matrix_dimensions(B)
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = self._A[i][j] / B._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def array_right_divide_equals(self, B: Matrix) -> Matrix:
        """
        Element-by-element right division in place, A = A ./ B
        
        Args:
            B: Another matrix.
        
        Returns:
            A ./ B (modifies self in place)
        """
        self._check_matrix_dimensions(B)
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] /= B._A[i][j]
        return self
    
    # -------------------------------------------------------------------------
    
    def array_left_divide(self, B: Matrix) -> Matrix:
        """
        Element-by-element left division, C = A .\\ B
        
        Args:
            B: Another matrix.
        
        Returns:
            A .\\ B (i.e., B ./ A)
        """
        self._check_matrix_dimensions(B)
        X = Matrix(self._m, self._n)
        for i in range(self._m):
            for j in range(self._n):
                X._A[i][j] = B._A[i][j] / self._A[i][j]
        return X
    
    # -------------------------------------------------------------------------
    
    def array_left_divide_equals(self, B: Matrix) -> Matrix:
        """
        Element-by-element left division in place, A = A .\\ B
        
        Args:
            B: Another matrix.
        
        Returns:
            A .\\ B (modifies self in place)
        """
        self._check_matrix_dimensions(B)
        for i in range(self._m):
            for j in range(self._n):
                self._A[i][j] = B._A[i][j] / self._A[i][j]
        return self
    
    # -------------------------------------------------------------------------
    # Matrix norms
    # -------------------------------------------------------------------------
    
    def norm1(self) -> float:
        """
        One norm.
        
        Returns:
            Maximum column sum.
        """
        f = 0.0
        for j in range(self._n):
            s = sum(abs(self._A[i][j]) for i in range(self._m))
            f = max(f, s)
        return f
    
    # -------------------------------------------------------------------------
    
    def norm2(self) -> float:
        """
        Two norm.
        
        Returns:
            Maximum singular value.
        """
        from .singular_value_decomposition import SingularValueDecomposition
        return SingularValueDecomposition(self).norm2()
    
    # -------------------------------------------------------------------------
    
    def norm_inf(self) -> float:
        """
        Infinity norm.
        
        Returns:
            Maximum row sum.
        """
        f = 0.0
        for i in range(self._m):
            s = sum(abs(self._A[i][j]) for j in range(self._n))
            f = max(f, s)
        return f
    
    # -------------------------------------------------------------------------
    
    def norm_f(self) -> float:
        """
        Frobenius norm.
        
        Returns:
            sqrt of sum of squares of all elements.
        """
        f = 0.0
        for i in range(self._m):
            for j in range(self._n):
                f = Maths.hypot(f, self._A[i][j])
        return f
    
    # -------------------------------------------------------------------------
    
    def trace(self) -> float:
        """
        Matrix trace.
        
        Returns:
            Sum of the diagonal elements.
        """
        t = 0.0
        for i in range(min(self._m, self._n)):
            t += self._A[i][i]
        return t
    
    # -------------------------------------------------------------------------
    # Matrix decompositions and solvers
    # -------------------------------------------------------------------------
    
    def chol(self) -> CholeskyDecomposition:
        """
        Cholesky Decomposition.
        
        Returns:
            CholeskyDecomposition
        """
        from .cholesky_decomposition import CholeskyDecomposition
        return CholeskyDecomposition(self)
    
    # -------------------------------------------------------------------------
    
    def lu(self) -> LUDecomposition:
        """
        LU Decomposition.
        
        Returns:
            LUDecomposition
        """
        from .lu_decomposition import LUDecomposition
        return LUDecomposition(self)
    
    # -------------------------------------------------------------------------
    
    def qr(self) -> QRDecomposition:
        """
        QR Decomposition.
        
        Returns:
            QRDecomposition
        """
        from .qr_decomposition import QRDecomposition
        return QRDecomposition(self)
    
    # -------------------------------------------------------------------------
    
    def svd(self) -> SingularValueDecomposition:
        """
        Singular Value Decomposition.
        
        Returns:
            SingularValueDecomposition
        """
        from .singular_value_decomposition import SingularValueDecomposition
        return SingularValueDecomposition(self)
    
    # -------------------------------------------------------------------------
    
    def eig(self) -> EigenvalueDecomposition:
        """
        Eigenvalue Decomposition.
        
        Returns:
            EigenvalueDecomposition
        """
        from .eigenvalue_decomposition import EigenvalueDecomposition
        return EigenvalueDecomposition(self)
    
    # -------------------------------------------------------------------------
    
    def det(self) -> float:
        """
        Matrix determinant.
        
        Returns:
            Determinant.
        """
        from .lu_decomposition import LUDecomposition
        return LUDecomposition(self).det()
    
    # -------------------------------------------------------------------------
    
    def rank(self) -> int:
        """
        Matrix rank.
        
        Returns:
            Effective numerical rank, obtained from SVD.
        """
        from .singular_value_decomposition import SingularValueDecomposition
        return SingularValueDecomposition(self).rank()
    
    # -------------------------------------------------------------------------
    
    def cond(self) -> float:
        """
        Matrix condition (2 norm).
        
        Returns:
            Ratio of largest to smallest singular value.
        """
        from .singular_value_decomposition import SingularValueDecomposition
        return SingularValueDecomposition(self).cond()
    
    # -------------------------------------------------------------------------
    
    def inverse(self) -> Matrix:
        """
        Matrix inverse or pseudoinverse.
        
        Returns:
            inverse(A) if A is square, pseudoinverse otherwise.
        """
        return self.solve(Matrix.identity(self._m, self._m))
    
    # -------------------------------------------------------------------------
    
    def solve(self, B: Matrix) -> Matrix:
        """
        Solve A * X = B
        
        Args:
            B: Right hand side.
        
        Returns:
            Solution if A is square, least squares solution otherwise.
        """
        if self._m == self._n:
            from .lu_decomposition import LUDecomposition
            return LUDecomposition(self).solve(B)
        else:
            from .qr_decomposition import QRDecomposition
            return QRDecomposition(self).solve(B)
    
    # -------------------------------------------------------------------------
    
    def solve_transpose(self, B: Matrix) -> Matrix:
        """
        Solve X * A = B, which is also A' * X' = B'
        
        Args:
            B: Right hand side.
        
        Returns:
            Solution if A is square, least squares solution otherwise.
        """
        return self.transpose().solve(B.transpose())
    
    # -------------------------------------------------------------------------
    # Vector operations (for 3D vectors stored as column matrices)
    # -------------------------------------------------------------------------
    
    def length(self) -> float:
        """
        Returns the length of the vector (for 3D column vectors only).
        
        Returns:
            Vector length.
        
        Raises:
            ValueError: If not a 3D column vector.
        """
        if self._n != 1:
            raise ValueError(
                "Vector lengths can only be applied to vectors. "
                "There can only be one column."
            )
        if self._m != 3:
            raise ValueError(
                "The length method currently applies only to "
                "three dimensional vectors."
            )
        
        return math.sqrt(
            self._A[0][0] ** 2 +
            self._A[1][0] ** 2 +
            self._A[2][0] ** 2
        )
    
    # -------------------------------------------------------------------------
    
    def vector_product(self, B: Matrix) -> Matrix:
        """
        Calculate the vector (cross) product between two 3D vectors.
        
        Args:
            B: Another 3D column vector.
        
        Returns:
            The cross product A × B.
        
        Raises:
            ValueError: If inputs are not 3D column vectors.
        """
        if B._n != 1 or self._n != 1:
            raise ValueError(
                "Vector products can only be applied to vectors. "
                "There can only be one column."
            )
        if B._m != 3 or self._m != 3:
            raise ValueError("Matrix inner dimensions must agree.")
        
        result = Matrix(3, 1)
        result._A[0][0] = self._A[1][0] * B._A[2][0] - B._A[1][0] * self._A[2][0]
        result._A[1][0] = self._A[2][0] * B._A[0][0] - B._A[2][0] * self._A[0][0]
        result._A[2][0] = self._A[0][0] * B._A[1][0] - B._A[0][0] * self._A[1][0]
        return result
    
    # -------------------------------------------------------------------------
    # Print methods
    # -------------------------------------------------------------------------
    
    def print(self, w: int = 10, d: int = 4, output: Optional[TextIO] = None) -> None:
        """
        Print the matrix. Line the elements up in columns with a
        Fortran-like 'Fw.d' style format.
        
        Args:
            w: Column width.
            d: Number of digits after the decimal.
            output: Output stream (defaults to stdout).
        """
        import sys
        if output is None:
            output = sys.stdout
        
        output.write('\n')
        for i in range(self._m):
            for j in range(self._n):
                s = f'{self._A[i][j]:{w}.{d}f}'
                padding = max(1, w + 2 - len(s))
                output.write(' ' * padding + s)
            output.write('\n')
        output.write('\n')
    
    # -------------------------------------------------------------------------
    
    def __str__(self) -> str:
        """String representation of the matrix."""
        output = StringIO()
        self.print(output=output)
        return output.getvalue()
    
    # -------------------------------------------------------------------------
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Matrix({self._m}, {self._n})"
    
    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------
    
    def _check_matrix_dimensions(self, B: Matrix) -> None:
        """Check if size(A) == size(B)."""
        if B._m != self._m or B._n != self._n:
            raise ValueError("Matrix dimensions must agree.")
    
    # -------------------------------------------------------------------------
    # Stub methods for uka package compatibility
    # -------------------------------------------------------------------------
    
    def append_to(self, s: ToString) -> None:
        """Stub for uka.util.Printable interface."""
        s.append("A", self._A)
    
    # -------------------------------------------------------------------------
    
    def create_patch(self, _copy: Matrix, po: PatchOutput) -> None:
        """Stub for uka.patch.Patchable interface."""
        if self._n != _copy._n or self._m != _copy._m:
            raise AssertionError("Matrix dimension has changed")
        
        for row in range(self._m):
            for col in range(self._n):
                if po.write_diff(self.get(row, col) - _copy.get(row, col), 0.0):
                    _copy.set(row, col, self.get(row, col))
    
    # -------------------------------------------------------------------------
    
    def apply_patch(self, _copy: Matrix, pi: PatchInput) -> None:
        """Stub for uka.patch.Patchable interface."""
        if self._n != _copy._n or self._m != _copy._m:
            raise AssertionError("Matrix dimension has changed")
        
        for row in range(self._m):
            for col in range(self._n):
                if pi.has_diff():
                    dd = pi.get_diff_as_double()
                    self.set(row, col, self.get(row, col) + dd)
                    _copy.set(row, col, _copy.get(row, col) + dd)
    
    # -------------------------------------------------------------------------
    
    def descend_references(self, c: ReferenceConsumer) -> None:
        """Stub for uka.patch.Patchable interface."""
        pass
    
    # -------------------------------------------------------------------------
    
    def filter_references(self, f: ReferenceFilter) -> None:
        """Stub for uka.patch.Patchable interface."""
        pass
    
    # -------------------------------------------------------------------------
    
    def flat_clone(self) -> Matrix:
        """Stub for uka.transport.Transportable interface."""
        return self.copy()

    # -------------------------------------------------------------------------

    @classmethod
    def demo(cls):

        # Example: Create matrices and perform basic operations
        print("Matrix class demonstration")
        print("=" * 40)
    
        # Create a 3x3 matrix from a 2D array
        vals = [[1., 2., 3.], [4., 5., 6.], [7., 8., 10.]]
        A = Matrix.from_2d_array(vals)
        print("Matrix A:")
        A.print()
    
        # Create identity matrix
        I = Matrix.identity(3, 3)
        print("Identity matrix I:")
        I.print()
    
        # Matrix addition
        B = A.plus(I)
        print("A + I:")
        B.print()
    
        # Matrix multiplication
        C = A.times(A)
        print("A * A:")
        C.print()
    
        # Transpose
        At = A.transpose()
        print("A transpose:")
        At.print()
    
        # Matrix norms
        print(f"One norm: {A.norm1()}")
        print(f"Infinity norm: {A.norm_inf()}")
        print(f"Frobenius norm: {A.norm_f()}")
        print(f"Trace: {A.trace()}")
    
        # Random matrix
        R = Matrix.random(2, 3)
        print("\nRandom 2x3 matrix:")
        R.print()


# =============================================================================
# Example usage
# =============================================================================

if __name__ == "__main__":

    Matrix.demo()


