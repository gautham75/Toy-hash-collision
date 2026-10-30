"""
Quantum vs Classical Query Complexity and Scaling Analysis.
Compares Classical O(2^(n/2)) Birthday Attack vs Quantum O(n) Simon's Algorithm.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure project root in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.oracle import ToyHashOracle
from src.classical_attack import ClassicalCollisionAttack
from src.simon_circuit import SimonAlgorithm

class ComplexityAnalyzer:
    def __init__(self, output_dir: str = "figures"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_theoretical_comparison_table(self):
        """
        Generates comparative metrics table across diverse bit sizes n.
        Assumptions:
        - Classical Expected: 128/35 ≈ 3.66 for n=3; sqrt(pi * 2^(n-1)) for n > 3
        - Quantum Minimum: n - 1 linearly independent equations
        - Quantum Expected Runs: (n - 1) + 1.61 ≈ n + 0.6 runs
        - Crossover: Classical exceeds quantum from n ≈ 5-6
        """
        n_values = [3, 4, 5, 6, 8, 10, 16, 30, 32, 64, 128, 256]
        rows = []
        for n in n_values:
            space_size = 2**n
            classical_worst = 2**(n - 1) + 1
            classical_expected = 128.0 / 35.0 if n == 3 else np.sqrt(np.pi * 2**(n - 1))
            quantum_min = n - 1
            quantum_expected = n + 0.6  # (n-1) + 1.61
            speedup = classical_expected / quantum_expected
            rows.append({
                "n": n,
                "domain_size": f"2^{n}",
                "classical_worst": f"{classical_worst:.2e}" if classical_worst > 1e6 else str(classical_worst),
                "classical_expected": f"{classical_expected:.2e}" if classical_expected > 1e6 else f"{classical_expected:.2f}",
                "quantum_min_eqs": quantum_min,
                "quantum_expected": f"{quantum_expected:.1f}",
                "speedup_factor": f"{speedup:.2e}x" if speedup > 1e4 else f"{speedup:.2f}x"
            })
        return rows

    def plot_theoretical_scaling(self, save_path: str = "figures/query_complexity_comparison.png"):
        """
        Generates high-resolution plot showing exponential separation between O(2^(n/2)) and O(n).
        """
        n_range = np.arange(2, 33, 1)
        classical_birthday = np.sqrt(np.pi * (2.0**(n_range - 1)))
        classical_worst = 2.0**(n_range - 1) + 1
        quantum_simon = n_range + 0.6

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Panel 1: Semi-log scale (Log10 Queries vs n)
        ax1.semilogy(n_range, classical_worst, 'r--', label=r'Classical Worst-Case: $O(2^{n-1})$', linewidth=2)
        ax1.semilogy(n_range, classical_birthday, 'darkorange', label=r'Classical Birthday Collision: $O(2^{n/2})$', linewidth=2.5)
        ax1.semilogy(n_range, quantum_simon, 'royalblue', label=r"Quantum Simon's Expected Runs: $\approx n + 0.6$", linewidth=2.5)
        ax1.axvline(x=3, color='grey', linestyle=':', label='Our Toy Hash Problem ($n=3$)')
        ax1.scatter([3], [128.0 / 35.0], color='darkorange', s=80, zorder=5)
        ax1.scatter([3], [3.6], color='royalblue', s=80, zorder=5)

        ax1.set_title("Query Complexity vs Hash Bit-Length $n$ (Log Scale)", fontsize=13, fontweight='bold')
        ax1.set_xlabel("Hash Bit Length $n$", fontsize=11)
        ax1.set_ylabel("Oracle Queries Required (Log10 Scale)", fontsize=11)
        ax1.grid(True, which="both", ls="--", alpha=0.5)
        ax1.legend(fontsize=10, loc='upper left')

        # Panel 2: Linear scale focus for small n (2 to 8) showing crossover at n ≈ 5-6
        small_n = np.arange(2, 9, 1)
        c_b_small = [np.sqrt(np.pi * (2.0**(n - 1))) if n != 3 else 128.0 / 35.0 for n in small_n]
        q_s_small = small_n + 0.6
        q_min_small = small_n - 1

        ax2.plot(small_n, c_b_small, 'o-', color='darkorange', label=r'Classical Birthday (Exact $n=3$: $3.66$)', linewidth=2.5)
        ax2.plot(small_n, q_s_small, 's-', color='royalblue', label=r"Quantum Expected Runs ($\approx (n-1)+1.61$)", linewidth=2.5)
        ax2.plot(small_n, q_min_small, '^--', color='cornflowerblue', label=r"Quantum Minimum Equations ($n-1$)", linewidth=1.8)
        ax2.axvline(x=3, color='grey', linestyle=':', label='n=3 Assignment')
        ax2.axvspan(4.8, 6.2, color='green', alpha=0.1, label='Crossover Region ($n \\approx 5-6$)')

        for i, txt in enumerate(c_b_small):
            ax2.annotate(f"{txt:.2f}", (small_n[i], txt), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=9, color='darkorange', fontweight='bold')
        for i, txt in enumerate(q_s_small):
            ax2.annotate(f"{txt:.1f}", (small_n[i], txt), textcoords="offset points", xytext=(0, -14), ha='center', fontsize=9, color='royalblue', fontweight='bold')

        ax2.set_title("Small Scale Behavior & Crossover Analysis ($n = 2$ to $8$)", fontsize=13, fontweight='bold')
        ax2.set_xlabel("Hash Bit Length $n$", fontsize=11)
        ax2.set_ylabel("Queries / Runs Required (Linear Scale)", fontsize=11)
        ax2.grid(True, ls="--", alpha=0.5)
        ax2.legend(fontsize=9, loc='upper left')

        plt.suptitle("Quantum vs. Classical Query Complexity for Toy Hash Collision Structure", fontsize=15, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"Complexity scaling plot saved to: {save_path}")

    def run_empirical_scaling_experiment(self, max_n: int = 10, trials_per_n: int = 50, save_path: str = "figures/empirical_scaling_benchmark.png"):
        """
        Runs empirical Monte Carlo simulations of Classical Birthday attack across n = 3 to max_n
        and compares with theoretical and quantum bounds.
        """
        n_values = list(range(3, max_n + 1))
        empirical_classical_means = []
        empirical_classical_stds = []
        theoretical_classical = []
        quantum_queries = []

        print(f"Running Empirical Collision Benchmarks (n=3 to {max_n}, {trials_per_n} trials each)...")
        for n in n_values:
            # Random secret s
            s_val = (1 << (n - 1)) | 1 # e.g. 10..01
            s_str = format(s_val, f'0{n}b')
            oracle = ToyHashOracle(s=s_str, n=n)
            attacker = ClassicalCollisionAttack(oracle)
            
            queries = []
            for _ in range(trials_per_n):
                q, _, _, _ = attacker.random_birthday_attack()
                queries.append(q)
            
            mean_q = np.mean(queries)
            std_q = np.std(queries)
            empirical_classical_means.append(mean_q)
            empirical_classical_stds.append(std_q)
            theoretical_classical.append(np.sqrt(np.pi * 2**(n - 1)))
            quantum_queries.append(n + 0.6)
            print(f"  n={n}: Classical Empirical Mean = {mean_q:.2f} +/- {std_q:.2f} | Theory = {theoretical_classical[-1]:.2f} | Quantum = {quantum_queries[-1]:.2f}")

        # Plot empirical results
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.errorbar(n_values, empirical_classical_means, yerr=empirical_classical_stds, fmt='o-', color='darkorange', 
                    ecolor='tan', elinewidth=2, capsize=4, label='Empirical Classical Birthday Attack (Monte Carlo)', linewidth=2)
        ax.plot(n_values, theoretical_classical, '--', color='brown', label=r'Theoretical Birthday Expectation ($\sqrt{\pi 2^{n-1}}$)', linewidth=2)
        ax.plot(n_values, quantum_queries, 's-', color='royalblue', label=r"Quantum Simon's Algorithm ($O(n)$)", linewidth=2.5)

        ax.set_title("Empirical Classical Query Scaling vs Quantum Query Bound", fontsize=13, fontweight='bold', pad=12)
        ax.set_xlabel("Hash Length $n$ (bits)", fontsize=11)
        ax.set_ylabel("Average Oracle Queries to Find Collision", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(fontsize=10)

        fig.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)
        print(f"Empirical scaling plot saved to: {save_path}")

        return n_values, empirical_classical_means, theoretical_classical, quantum_queries

if __name__ == "__main__":
    analyzer = ComplexityAnalyzer()
    analyzer.plot_theoretical_scaling()
    table = analyzer.generate_theoretical_comparison_table()
    print("\n--- Theoretical Complexity Table ---")
    for r in table:
        print(f"n={r['n']:3d} | Domain: {r['domain_size']:>6s} | Classical Worst: {r['classical_worst']:>10s} | Classical Exp: {r['classical_expected']:>10s} | Quantum: {r['quantum_expected']:>6s} | Speedup: {r['speedup_factor']:>10s}")
    
    analyzer.run_empirical_scaling_experiment(max_n=9, trials_per_n=30)
