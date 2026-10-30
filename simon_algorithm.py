"""
Simon's Quantum Algorithm Implementation, Circuit Synthesis & GF(2) Recovery.
Problem Statement 14: Toy Hash Collision Structure via Simon's Quantum Algorithm.

Implements:
- Reversible quantum oracle mapping |x>|0> -> |x>|f(x)>
- Full 6-qubit Simon circuit (Hadamard, Oracle, Hadamard, Measurement)
- Ideal execution via Qiskit AerSimulator
- Linear system solving over GF(2) via Gaussian elimination
- Verification of orthogonality s · y ≡ 0 (mod 2)
- Multi-period validation across all 7 non-zero periods
"""

import os
import json
from typing import Dict, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator

from hash_function import ToyHashFunction, PRIMARY_TRUTH_TABLE

class SimonAlgorithm:
    """
    Simon's Algorithm pipeline for finding hidden period s of an n-bit hash function.
    """
    def __init__(self, s: str = "110", n: int = 3):
        self.n = n
        self.s = s
        self.s_int = int(s, 2)
        self.hash_fn = ToyHashFunction(s=s, n=n)
        self.simulator = AerSimulator()
        self.oracle_circuit = self._build_oracle()
        self.full_circuit = self._build_circuit()

    def _build_oracle(self) -> QuantumCircuit:
        """
        Synthesizes the reversible quantum oracle U_f mapping |x>|0> -> |x>|f(x)>.
        Qubits 0..(n-1): Input register |x>
        Qubits n..(2n-1): Target register |y>

        For primary case s = '110':
            q3 (target 0) <= x0 via CX(0, 3)
            q4 (target 1) <= x1 ⊕ x2 via CX(1, 4) and CX(2, 4)
            q5 (target 2) <= 0
        """
        qr_x = QuantumRegister(self.n, name="x")
        qr_y = QuantumRegister(self.n, name="y")
        qc = QuantumCircuit(qr_x, qr_y, name="Oracle_Uf")

        if self.s == "110" and self.n == 3:
            qc.cx(qr_x[0], qr_y[0])
            qc.cx(qr_x[1], qr_y[1])
            qc.cx(qr_x[2], qr_y[1])
        else:
            # Generalized reversible oracle construction for arbitrary s != 0^n
            # Find first index j (from LSB) where s_j == 1
            j = None
            for bit_idx in range(self.n):
                if self.s[self.n - 1 - bit_idx] == "1":
                    j = bit_idx
                    break
            # Copy x to y
            for i in range(self.n):
                qc.cx(qr_x[i], qr_y[i])
            # For each bit where s has '1', XOR with x_j
            for i in range(self.n):
                if self.s[self.n - 1 - i] == "1":
                    qc.cx(qr_x[j], qr_y[i])

        return qc

    def verify_oracle_basis_states(self) -> Dict[str, bool]:
        """
        Verifies that U_f |x>|0> == |x>|f(x)> for all 2^n computational basis states.
        Also verifies reversibility: U_f applied twice returns to the initial state.
        """
        sim = AerSimulator()
        mismatches = 0
        reversibility_failures = 0

        for x_val in range(2**self.n):
            x_bin = format(x_val, f"0{self.n}b")
            expected_fx = self.hash_fn.hash(x_bin)

            # Test forward evaluation
            qc_eval = QuantumCircuit(2 * self.n, self.n)
            for i in range(self.n):
                if x_bin[self.n - 1 - i] == "1":
                    qc_eval.x(i)
            qc_eval.compose(self.oracle_circuit, inplace=True)
            qc_eval.measure(range(self.n, 2 * self.n), range(self.n))
            counts = sim.run(qc_eval, shots=10).result().get_counts()
            measured_fx = list(counts.keys())[0]

            if measured_fx != expected_fx:
                mismatches += 1

            # Test reversibility: U_f is self-inverse when target starts in |0>
            qc_rev = QuantumCircuit(2 * self.n, 2 * self.n)
            for i in range(self.n):
                if x_bin[self.n - 1 - i] == "1":
                    qc_rev.x(i)
            qc_rev.compose(self.oracle_circuit, inplace=True)
            qc_rev.compose(self.oracle_circuit, inplace=True)
            qc_rev.measure(range(2 * self.n), range(2 * self.n))
            rev_counts = sim.run(qc_rev, shots=10).result().get_counts()
            meas_rev = list(rev_counts.keys())[0]
            # Expected: target bits 0^n on left (c5..c3), input bits x on right (c2..c0)
            expected_init = ("0" * self.n) + format(x_val, f"0{self.n}b")
            if meas_rev != expected_init:
                reversibility_failures += 1

        return {
            "all_basis_states_correct": mismatches == 0,
            "reversible": reversibility_failures == 0,
            "mismatch_count": mismatches
        }

    def _build_circuit(self) -> QuantumCircuit:
        """
        Constructs the full Simon's Algorithm quantum circuit:
        1. Initialize input register |0^n> and target register |0^n>.
        2. Apply H^⊗n to the input register.
        3. Apply Oracle U_f mapping |x>|0> -> |x>|f(x)>.
        4. Apply second H^⊗n to the input register.
        5. Measure the input register into classical bits c0..c(n-1).
        """
        qr_x = QuantumRegister(self.n, name="x")
        qr_y = QuantumRegister(self.n, name="y")
        cr = ClassicalRegister(self.n, name="meas_x")
        qc = QuantumCircuit(qr_x, qr_y, cr, name="Simons_Algorithm")

        # Step 1: Superposition
        qc.h(qr_x)
        qc.barrier(label="H_in")

        # Step 2: Oracle
        qc.compose(self.oracle_circuit, qubits=list(qr_x) + list(qr_y), inplace=True)
        qc.barrier(label="Oracle")

        # Step 3: Interference
        qc.h(qr_x)
        qc.barrier(label="H_out")

        # Step 4: Measurement
        qc.measure(qr_x, cr)
        return qc

    def run_simulation(self, shots: int = 1024, seed: Optional[int] = 42) -> Dict[str, int]:
        """
        Executes the circuit on AerSimulator and returns complete 8-bin counts.
        Guarantees all 2^n states are present (with 0 for unobserved states).
        """
        job = self.simulator.run(self.full_circuit, shots=shots, seed_simulator=seed)
        raw_counts = job.result().get_counts()
        
        # Build complete dictionary of all 2^n bins
        full_counts = {}
        for val in range(2**self.n):
            b_str = format(val, f"0{self.n}b")
            full_counts[b_str] = raw_counts.get(b_str, 0)

        # Assertion: counts must sum to shots
        assert sum(full_counts.values()) == shots, f"Counts sum {sum(full_counts.values())} != shots {shots}"
        return full_counts

    def verify_orthogonality(self, counts: Dict[str, int]) -> Dict[str, bool]:
        """
        Verifies that all observed bitstrings y satisfy s · y ≡ 0 (mod 2).
        For an ideal simulator, non-orthogonal states must have count 0.
        """
        all_orthogonal = True
        for bitstr, count in counts.items():
            if count > 0:
                dot_prod = sum(int(a) * int(b) for a, b in zip(self.s, bitstr)) % 2
                if dot_prod != 0:
                    all_orthogonal = False
                    break
        return {"all_observed_orthogonal": all_orthogonal}

    def solve_hidden_period(self, measured_samples: List[str]) -> Tuple[Optional[str], int, List[str]]:
        """
        Extracts linearly independent equations over GF(2) and solves M * s = 0 (mod 2).
        Excludes trivial string 0^n.
        Returns:
            recovered_s: Recovered non-zero period, or None if rank < n-1.
            rank: Rank of the equation matrix over GF(2).
            independent_equations: List of linearly independent row bitstrings.
        """
        unique_samples = [y for y in set(measured_samples) if y != "0" * self.n]
        matrix = []
        independent_eqs = []

        for y_str in unique_samples:
            row = [int(c) for c in y_str]
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

        # Find unique non-zero vector s in {0,1}^n satisfying M * s = 0 (mod 2)
        candidates = []
        for cand_val in range(1, 2**self.n):
            cand_str = format(cand_val, f"0{self.n}b")
            cand_vec = [int(c) for c in cand_str]
            satisfies = True
            for row in matrix:
                if sum(r * c for r, c in zip(row, cand_vec)) % 2 != 0:
                    satisfies = False
                    break
            if satisfies:
                candidates.append(cand_str)

        if len(candidates) == 1:
            return candidates[0], rank, independent_eqs
        return None, rank, independent_eqs

    def execute_and_recover(self, initial_shots: int = 10, max_additional_shots: int = 50) -> Dict:
        """
        Proper post-processing loop:
        Collects measurement shots, attempts to solve over GF(2).
        If rank < n - 1, collects additional shots iteratively rather than guessing!
        """
        total_queries = 0
        collected_samples = []
        
        # Initial run
        counts = self.run_simulation(shots=initial_shots, seed=None)
        total_queries += initial_shots
        for bitstr, cnt in counts.items():
            collected_samples.extend([bitstr] * cnt)

        rec_s, rank, eqs = self.solve_hidden_period(collected_samples)
        additional_runs = 0

        # Loop if rank insufficient
        while rank < self.n - 1 and additional_runs < max_additional_shots:
            additional_runs += 1
            extra_counts = self.run_simulation(shots=2, seed=None)
            total_queries += 2
            for bitstr, cnt in extra_counts.items():
                collected_samples.extend([bitstr] * cnt)
            rec_s, rank, eqs = self.solve_hidden_period(collected_samples)

        valid = (rec_s == self.s)
        return {
            "expected_s": self.s,
            "recovered_s": rec_s,
            "rank": rank,
            "equations": eqs,
            "total_queries": total_queries,
            "additional_runs": additional_runs,
            "success": valid
        }

    def _matrix_rank_gf2(self, mat: List[List[int]]) -> int:
        """Computes rank of binary matrix over GF(2) using row elimination."""
        if not mat:
            return 0
        A = [row[:] for row in mat]
        rows, cols = len(A), len(A[0])
        r = 0
        for col in range(cols):
            pivot = None
            for row in range(r, rows):
                if A[row][col] == 1:
                    pivot = row
                    break
            if pivot is None:
                continue
            A[r], A[pivot] = A[pivot], A[r]
            for row in range(rows):
                if row != r and A[row][col] == 1:
                    for c in range(col, cols):
                        A[row][c] ^= A[r][c]
            r += 1
            if r == rows or r == cols:
                break
        return r

    def plot_histogram(self, counts: Dict[str, int], save_path: str = "figures/measurement_histogram.png"):
        """Plots measurement counts displaying all 8 bins and destructive interference."""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        all_states = [format(i, f"0{self.n}b") for i in range(2**self.n)]
        frequencies = [counts.get(s, 0) for s in all_states]
        colors = ["#2563eb" if counts.get(s, 0) > 0 else "#dc2626" for s in all_states]

        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        bars = ax.bar(all_states, frequencies, color=colors, edgecolor="black", width=0.55)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=10, fontweight="bold")

        total_shots = sum(frequencies)
        ax.set_title(f"Simon's Algorithm Measurement Distribution (Total Shots: {total_shots}, Secret s = '{self.s}')",
                     fontsize=12, pad=14, fontweight="bold")
        ax.set_xlabel("Measured Output String y ∈ {0,1}³ (Register meas_x)", fontsize=11)
        ax.set_ylabel("Measurement Counts", fontsize=11)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#2563eb", edgecolor="black", label=r"Constructive Interference ($s \cdot y \equiv 0$ mod 2)"),
            Patch(facecolor="#dc2626", edgecolor="black", label=r"Destructive Interference ($s \cdot y \equiv 1$ mod 2, Count = 0)")
        ]
        ax.legend(handles=legend_elements, loc="upper right")
        fig.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)

def test_all_nonzero_periods(n: int = 3) -> List[Dict]:
    """
    Rigorously tests Simon's algorithm across all 2^n - 1 non-zero periods.
    """
    results = []
    print(f"\n--- Testing All {2**n - 1} Non-Zero Hidden Periods (n={n}) ---")
    for s_val in range(1, 2**n):
        s_cand = format(s_val, f"0{n}b")
        simon = SimonAlgorithm(s=s_cand, n=n)
        res = simon.execute_and_recover(initial_shots=12, max_additional_shots=30)
        results.append(res)
        status_str = "PASS" if res["success"] else "FAIL"
        print(f"  Target s='{s_cand}' | Recovered s='{res['recovered_s']}' | Rank={res['rank']} | Queries={res['total_queries']} | [{status_str}]")
    return results

if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    simon = SimonAlgorithm(s="110", n=3)
    
    # 1. Oracle basis verification
    oracle_check = simon.verify_oracle_basis_states()
    print("Oracle Basis State Verification:", oracle_check)
    
    # 2. Measurement simulation
    counts = simon.run_simulation(shots=1024, seed=42)
    print("Measurement Counts (1024 shots):", counts)
    simon.plot_histogram(counts)

    # 3. Orthogonality check
    ortho_check = simon.verify_orthogonality(counts)
    print("Orthogonality Verification:", ortho_check)

    # 4. Hidden period recovery
    recovery_result = simon.execute_and_recover()
    print("Recovery Result:", recovery_result)

    # 5. Test all 7 non-zero periods
    all_period_results = test_all_nonzero_periods(n=3)
    with open("results/all_periods_validation.json", "w") as f:
        json.dump(all_period_results, f, indent=2)
    print("All period validation saved to: results/all_periods_validation.json")
