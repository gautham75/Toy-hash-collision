"""
Toy Hash Collision Oracle Implementation for Simon's Algorithm.

Problem: A 3-bit hash function f: {0,1}^3 -> {0,1}^3 has a hidden period s = '110'
creating systematic collisions such that:
    f(x) = f(y) <=> x ⊕ y ∈ {000, s}
"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister

class ToyHashOracle:
    """
    Constructs classical and quantum representations of the 3-bit toy hash function.
    """
    def __init__(self, s: str = "110", n: int = 3):
        self.n = n
        self.s = s
        self.s_int = int(s, 2)
        self.truth_table = self._build_truth_table()

    def _build_truth_table(self):
        """
        Builds the explicit truth table for the 2-to-1 hash function.
        f(x) maps {0,1}^n to {0,1}^n such that f(x) = f(x ⊕ s).
        For canonical s = '110', uses exact standard table.
        For general non-zero s, uses consistent linear projection f(x) = x ⊕ (x_j * s),
        where j is the first bit index (from LSB) where s_j == 1.
        """
        if self.s == "110" and self.n == 3:
            return {
                "000": "000", "001": "001", "010": "010", "011": "011",
                "100": "010", "101": "011", "110": "000", "111": "001"
            }

        # Find first bit index j (from LSB) where s has '1'
        j = None
        for bit_idx in range(self.n):
            if self.s[self.n - 1 - bit_idx] == "1":
                j = bit_idx
                break

        table = {}
        for x_val in range(2**self.n):
            x_bin = format(x_val, f"0{self.n}b")
            xj = int(x_bin[self.n - 1 - j])
            fx_val = x_val ^ (xj * self.s_int)
            table[x_bin] = format(fx_val, f"0{self.n}b")
        return table

    def classical_evaluate(self, x: str) -> str:
        """Evaluates the hash function classically."""
        return self.truth_table[x]

    def get_collisions(self):
        """Returns all colliding input pairs."""
        collisions = {}
        for x_bin, out_bin in self.truth_table.items():
            if out_bin not in collisions:
                collisions[out_bin] = []
            collisions[out_bin].append(x_bin)
        return collisions

    def build_quantum_oracle_circuit(self) -> QuantumCircuit:
        """
        Builds the reversible quantum oracle U_f mapping |x>|0> -> |x>|f(x)>.
        For s = '110' (q2=1, q1=1, q0=0 in little-endian):
          - Output bit 0 receives x0 (via CX(q0, target0))
          - Output bit 1 receives x1 ⊕ x2 (via CX(q1, target1) and CX(q2, target1))
          - Output bit 2 remains |0>
        For general non-zero s:
          - Copy x to y via CX(x_i, y_i)
          - For each bit where s has '1', apply CX(x_j, y_i)
        This ensures f(x) = f(x ⊕ s) with exact 2-to-1 collision structure.
        """
        qr_in = QuantumRegister(self.n, name='input')
        qr_out = QuantumRegister(self.n, name='hash_out')
        oracle_qc = QuantumCircuit(qr_in, qr_out, name="U_hash")

        if self.s == "110" and self.n == 3:
            oracle_qc.cx(qr_in[0], qr_out[0])
            oracle_qc.cx(qr_in[1], qr_out[1])
            oracle_qc.cx(qr_in[2], qr_out[1])
        else:
            j = None
            for bit_idx in range(self.n):
                if self.s[self.n - 1 - bit_idx] == "1":
                    j = bit_idx
                    break
            # Copy x to y
            for i in range(self.n):
                oracle_qc.cx(qr_in[i], qr_out[i])
            # For each bit where s has '1', XOR with x_j
            for i in range(self.n):
                if self.s[self.n - 1 - i] == "1":
                    oracle_qc.cx(qr_in[j], qr_out[i])

        return oracle_qc

if __name__ == "__main__":
    oracle = ToyHashOracle(s="110")
    print(f"Secret period s: {oracle.s}")
    print("Truth Table [x -> f(x)]:")
    for x, fx in sorted(oracle.truth_table.items()):
        print(f"  Hash({x}) = {fx}")
    print("\nColliding Pairs:")
    for fx, pair in oracle.get_collisions().items():
        print(f"  f({pair[0]}) = f({pair[1]}) = {fx} | XOR difference: {format(int(pair[0], 2) ^ int(pair[1], 2), '03b')}")
