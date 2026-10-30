"""
GF(2) Linear Algebra Solver for Simon's Algorithm.
Solves the homogeneous system M * s = 0 (mod 2) to reconstruct the secret period s.
"""

import numpy as np
from typing import List, Optional, Tuple

class GF2Solver:
    """
    Gaussian elimination and null-space solver over Galois Field GF(2).
    """
    def __init__(self, n: int = 3):
        self.n = n

    def dot_product(self, s: str, y: str) -> int:
        """Computes s · y (mod 2)."""
        return sum(int(a) * int(b) for a, b in zip(s, y)) % 2

    def solve(self, bitstrings: List[str]) -> Tuple[Optional[str], int, List[str]]:
        """
        Takes measurement samples y and recovers the secret s != 0^n.
        Returns:
            recovered_s: The unique non-zero secret period string, or None if insufficient equations.
            rank: The rank of the linear system over GF(2).
            independent_equations: The linearly independent basis vectors obtained.
        """
        # Convert bitstrings to unique non-zero vectors
        unique_samples = [y for y in set(bitstrings) if y != '0' * self.n]
        
        matrix = []
        independent_eqs = []
        
        for y_str in unique_samples:
            row = [int(c) for c in y_str]
            # Try adding this row to the matrix and check if it increases rank
            test_mat = matrix + [row]
            r = self._matrix_rank_gf2(test_mat)
            if r > len(matrix):
                matrix.append(row)
                independent_eqs.append(y_str)
                if r == self.n - 1:
                    break

        rank = len(matrix)
        if rank < self.n - 1:
            return None, rank, independent_eqs

        # Find the non-zero candidate s in {0,1}^n such that M * s = 0 (mod 2)
        valid_candidates = []
        for cand_val in range(1, 2**self.n):
            cand_str = format(cand_val, f'0{self.n}b')
            cand_vec = [int(c) for c in cand_str]
            # Check if M * cand_vec == 0 (mod 2)
            satisfies = True
            for row in matrix:
                if sum(r * c for r, c in zip(row, cand_vec)) % 2 != 0:
                    satisfies = False
                    break
            if satisfies:
                valid_candidates.append(cand_str)

        if len(valid_candidates) == 1:
            return valid_candidates[0], rank, independent_eqs
        # Underdetermined (more than 1 non-zero vector in null space) or inconsistent
        return None, rank, independent_eqs

    def _matrix_rank_gf2(self, mat: List[List[int]]) -> int:
        """Computes rank of a binary matrix over GF(2) using Gaussian elimination."""
        if not mat:
            return 0
        A = [row[:] for row in mat]
        rows = len(A)
        cols = len(A[0])
        r = 0
        for col in range(cols):
            # Pivot search
            pivot_row = None
            for row in range(r, rows):
                if A[row][col] == 1:
                    pivot_row = row
                    break
            if pivot_row is None:
                continue
            # Swap
            A[r], A[pivot_row] = A[pivot_row], A[r]
            # Eliminate
            for row in range(rows):
                if row != r and A[row][col] == 1:
                    for c in range(col, cols):
                        A[row][c] ^= A[r][c]
            r += 1
            if r == rows or r == cols:
                break
        return r

if __name__ == "__main__":
    solver = GF2Solver(n=3)
    # Test with vectors orthogonal to s = '110'
    # Orthogonal vectors: '001', '110', '111'
    samples = ['001', '110']
    s_rec, rank, eqs = solver.solve(samples)
    print(f"Independent equations: {eqs}")
    print(f"System Rank over GF(2): {rank}")
    print(f"Recovered secret s: {s_rec}")
