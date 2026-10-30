"""
Simon's Quantum Circuit Builder and Execution Pipeline.
Builds the 2n-qubit circuit, executes on AerSimulator, and recovers the hidden period s.
"""

import os
import sys

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from src.oracle import ToyHashOracle
from src.gf2_solver import GF2Solver

class SimonAlgorithm:
    def __init__(self, s: str = "110", n: int = 3):
        self.n = n
        self.s = s
        self.oracle_obj = ToyHashOracle(s=s, n=n)
        self.solver = GF2Solver(n=n)
        self.simulator = AerSimulator()
        self.circuit = self._build_full_circuit()

    def _build_full_circuit(self) -> QuantumCircuit:
        """
        Constructs the complete Simon's Algorithm quantum circuit:
        1. Initialize n input qubits and n target qubits in |0>.
        2. Apply Hadamard gates H^⊗n to the input register.
        3. Apply Oracle U_f mapping |x>|0> -> |x>|f(x)>.
        4. Apply second layer of Hadamard gates H^⊗n to the input register.
        5. Measure the input register into classical register.
        """
        qr_in = QuantumRegister(self.n, name='x')
        qr_out = QuantumRegister(self.n, name='f_x')
        cr = ClassicalRegister(self.n, name='meas_x')
        
        qc = QuantumCircuit(qr_in, qr_out, cr, name="Simon_Algorithm")

        # Step 1: Create superposition across input register
        qc.h(qr_in)
        qc.barrier(label="Hadamard_In")

        # Step 2: Query Oracle
        oracle_qc = self.oracle_obj.build_quantum_oracle_circuit()
        oracle_qubits = list(qr_in) + list(qr_out)
        qc.compose(oracle_qc, qubits=oracle_qubits, inplace=True)
        qc.barrier(label="Oracle_Uf")

        # Step 3: Second Hadamard layer on input register
        qc.h(qr_in)
        qc.barrier(label="Hadamard_Out")

        # Step 4: Measurement of input register
        # Qiskit registers: measure qr_in[i] to cr[i]
        qc.measure(qr_in, cr)

        return qc

    def draw_circuit(self, save_path: str = "figures/simon_circuit.png"):
        """Renders and saves the quantum circuit diagram."""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Decomposed version showing actual CNOT gates for clarity
        decomposed = self.circuit.decompose()
        fig = decomposed.draw(output='mpl', style='iqp')
        fig.savefig(save_path, bbox_inches='tight', dpi=300)
        plt.close(fig)
        print(f"Circuit diagram saved to: {save_path}")

    def run_simulation(self, shots: int = 1024):
        """
        Executes the circuit on AerSimulator and returns measurement counts.
        """
        job = self.simulator.run(self.circuit, shots=shots)
        result = job.result()
        counts = result.get_counts()
        return counts

    def plot_histogram(self, counts: dict, save_path: str = "figures/measurement_histogram.png"):
        """Plots the measurement counts histogram showing destructive interference."""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # All possible 3-bit strings
        all_states = [format(i, f'0{self.n}b') for i in range(2**self.n)]
        frequencies = [counts.get(s, 0) for s in all_states]
        colors = ['#1f77b4' if counts.get(s, 0) > 0 else '#d62728' for s in all_states]

        fig, ax = plt.subplots(figsize=(9, 5))
        bars = ax.bar(all_states, frequencies, color=colors, edgecolor='black', width=0.6)
        
        # Label values on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontweight='bold')

        ax.set_title(f"Simon's Algorithm Output Distribution for Secret s = '{self.s}'", fontsize=14, pad=15)
        ax.set_xlabel("Measured Output String y ∈ {0,1}³", fontsize=12)
        ax.set_ylabel("Measurement Counts (out of 1024 shots)", fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Custom legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#1f77b4', edgecolor='black', label=f'Constructive Interference (s · y ≡ 0 mod 2)'),
            Patch(facecolor='#d62728', edgecolor='black', label=f'Destructive Interference (s · y ≡ 1 mod 2)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', framealpha=0.9)

        fig.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)
        print(f"Measurement histogram saved to: {save_path}")

    def query_until_solved(self) -> int:
        """
        Simulates individual sequential single-shot quantum queries until
        a set of n-1 linearly independent vectors is gathered and s is solved.
        Returns the exact number of quantum queries consumed.
        """
        collected_samples = []
        queries = 0
        while True:
            queries += 1
            # 1 shot = 1 quantum oracle query
            job = self.simulator.run(self.circuit, shots=1)
            sample = list(job.result().get_counts().keys())[0]
            collected_samples.append(sample)
            
            s_cand, rank, _ = self.solver.solve(collected_samples)
            if rank == self.n - 1 and s_cand is not None:
                return queries

if __name__ == "__main__":
    simon = SimonAlgorithm(s="110", n=3)
    simon.draw_circuit()
    counts = simon.run_simulation(shots=1024)
    print("Simulation Counts:", counts)
    simon.plot_histogram(counts)
    
    # Solve from counts
    recovered_s, rank, eqs = simon.solver.solve(list(counts.keys()))
    print(f"Orthogonal basis equations: {eqs}")
    print(f"Rank: {rank}")
    print(f"Recovered Secret s: {recovered_s} (Expected: {simon.s})")
    
    # Run sequential query trials
    trial_queries = [simon.query_until_solved() for _ in range(100)]
    print(f"Mean quantum queries to reconstruct s over 100 trials: {sum(trial_queries)/len(trial_queries):.2f}")
