"""
Classical Collision Attack vs Quantum Simon's Algorithm: Complexity & Empirical Scaling.
Problem Statement 14: Toy Hash Collision Structure via Simon's Quantum Algorithm.

Mathematical Framework:
- Classical Birthday Attack: O(2^(n/2)) queries expected (~1.253 * sqrt(2^n))
- Quantum Simon's Algorithm: O(n) oracle queries under Simon's promise
- Demonstrates why n=3 is an illustrative toy proof-of-concept rather than a practical speedup
"""

import os
import json
import random
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt

from hash_function import ToyHashFunction
from simon_algorithm import SimonAlgorithm

class ClassicalCollisionFinder:
    """
    Simulates classical collision search on an n-bit hash function with hidden period s.
    """
    def __init__(self, hash_fn: ToyHashFunction):
        self.hash_fn = hash_fn
        self.n = hash_fn.n
        self.s = hash_fn.s
        self.s_int = hash_fn.s_int

    def find_collision_randomized(self, seed: int = None) -> Tuple[int, str, str, str]:
        """
        Executes a randomized classical birthday attack without replacement.
        Queries random inputs x until an identical hash output is observed.
        Returns:
            queries: Total function evaluations.
            x1: First input.
            x2: Second input.
            recovered_s: x1 ⊕ x2.
        """
        if seed is not None:
            random.seed(seed)

        all_inputs = [format(i, f"0{self.n}b") for i in range(2**self.n)]
        random.shuffle(all_inputs)

        seen_outputs: Dict[str, str] = {}
        queries = 0

        for x in all_inputs:
            queries += 1
            h = self.hash_fn.hash(x)
            if h in seen_outputs:
                x_prev = seen_outputs[h]
                recovered_s = format(int(x, 2) ^ int(x_prev, 2), f"0{self.n}b")
                return queries, x_prev, x, recovered_s
            seen_outputs[h] = x

        raise RuntimeError("Exhaustive domain searched without finding collision!")

    def deterministic_worst_case(self) -> int:
        """
        Deterministic upper bound:
        In a 2-to-1 function with 2^(n-1) unique outputs, an adversary can query
        at most 2^(n-1) unique outputs before being guaranteed a collision on query 2^(n-1) + 1.
        """
        return 2**(self.n - 1) + 1

    def run_monte_carlo(self, trials: int = 10000, seed: int = 12345) -> Dict:
        """
        Runs Monte Carlo evaluation with fixed seed for rigorous reproducibility.
        Definition of queries: Number of f-evaluations made up to and including
        the one that reveals the collision (min 2, max 2^(n-1)+1 = 5 for n=3).
        Exact expectation for 2-to-1 function on 8 inputs: 128/35 ≈ 3.657.
        """
        random.seed(seed)
        query_counts = []
        for _ in range(trials):
            q, x1, x2, rec_s = self.find_collision_randomized()
            assert rec_s == self.s, f"Recovered period {rec_s} != true period {self.s}"
            query_counts.append(q)

        exact_exp = 128.0 / 35.0 if self.n == 3 else float(np.sqrt(np.pi * 2**(self.n - 1)))
        theoretical_birthday = float(np.sqrt(np.pi * 2**(self.n - 1)))

        return {
            "n": self.n,
            "trials": trials,
            "seed": seed,
            "mean_queries": float(np.mean(query_counts)),
            "std_queries": float(np.std(query_counts)),
            "min_queries": int(np.min(query_counts)),
            "max_queries": int(np.max(query_counts)),
            "exact_theoretical_expectation": float(exact_exp),
            "theoretical_birthday_bound": theoretical_birthday,
            "worst_case_bound": self.deterministic_worst_case(),
            "query_definition": "Number of f-evaluations made up to and including the one revealing collision"
        }

class ComplexityComparison:
    """
    Theoretical and empirical comparison between Classical and Quantum approaches.
    """
    def __init__(self, output_dir: str = "figures"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def get_comparison_table() -> List[Dict]:
        """
        Returns structured comparison table across key cryptographic and toy bit lengths.
        Assumptions:
        - Classical Expected: E[Q] ≈ sqrt(pi * 2^(n-1)) ≈ 1.253 * 2^(n/2); exact for n=3 is 128/35 ≈ 3.66
        - Quantum Minimum: n - 1 linearly independent equations
        - Quantum Expected Runs: E[Runs] = (n - 1) + 1.61 ≈ n + 0.6 runs to collect rank n-1
        """
        n_values = [3, 4, 5, 6, 8, 10, 15, 20, 30, 32, 64, 128, 256]
        rows = []
        for n in n_values:
            classical_worst = 2**(n - 1) + 1
            classical_exp = 128.0 / 35.0 if n == 3 else np.sqrt(np.pi * 2.0**(n - 1))
            quantum_min = n - 1
            quantum_exp = n + 0.6  # (n-1) + 1.61
            speedup = classical_exp / quantum_exp
            rows.append({
                "n": n,
                "domain_size": f"2^{n}",
                "classical_worst": f"{classical_worst:.2e}" if classical_worst > 1e6 else str(classical_worst),
                "classical_expected": f"{classical_exp:.2e}" if classical_exp > 1e6 else f"{classical_exp:.2f}",
                "quantum_min_eqs": quantum_min,
                "quantum_expected": f"{quantum_exp:.1f}",
                "speedup_factor": f"{speedup:.2e}x" if speedup > 1e4 else f"{speedup:.2f}x",
                "practical_notes": "Toy scale (classical ≈ 3.66, quantum ~3.6; educational only)" if n == 3 else
                                   "Near parity (classical ~5.0, quantum ~4.6)" if n == 4 else
                                   "Crossover begins (classical exceeds quantum from n ≈ 5-6)" if n in (5, 6) else
                                   "Clear advantage manifest" if n <= 30 else
                                   "Exponential advantage manifest" if n <= 64 else
                                   "Classically intractable (e.g., SHA-256 scale)"
            })
        return rows

    def plot_theoretical_scaling(self, save_path: str = "figures/query_complexity_comparison.png"):
        """
        Plots semi-log theoretical query comparison from n=2 to n=32.
        Separates theoretical curves from empirical points.
        """
        n_range = np.arange(2, 33, 1)
        classical_birthday = np.sqrt(np.pi * (2.0**(n_range - 1)))
        classical_worst = 2.0**(n_range - 1) + 1
        quantum_simon = n_range + 0.6

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

        # Panel 1: Semi-log
        ax1.semilogy(n_range, classical_worst, "r--", linewidth=1.8, label=r"Classical Worst-Case ($2^{n-1} + 1$)")
        ax1.semilogy(n_range, classical_birthday, color="darkorange", linewidth=2.5,
                     label=r"Classical Birthday Expectation ($\approx 1.253 \cdot 2^{n/2}$)")
        ax1.semilogy(n_range, quantum_simon, color="royalblue", linewidth=2.5,
                     label=r"Quantum Simon Oracle Queries ($n + \mathcal{O}(1)$)")
        ax1.axvline(x=3, color="gray", linestyle=":", label="Assigned Toy Problem ($n=3$)")
        ax1.scatter([3], [np.sqrt(np.pi * 4)], color="darkorange", s=70, zorder=5)
        ax1.scatter([3], [3.6], color="royalblue", s=70, zorder=5)

        ax1.set_title("Theoretical Query Complexity vs Hash Bit-Length (Log Scale)", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Hash Bit-Length $n$", fontsize=10)
        ax1.set_ylabel("Oracle Queries Required (Log10)", fontsize=10)
        ax1.grid(True, which="both", linestyle="--", alpha=0.5)
        ax1.legend(fontsize=9, loc="upper left")

        # Panel 2: Linear scale for small n (2 to 8) showing that at n=3 queries are similar
        small_n = np.arange(2, 9, 1)
        c_small = np.sqrt(np.pi * (2.0**(small_n - 1)))
        q_small = small_n + 0.6

        ax2.plot(small_n, c_small, "o-", color="darkorange", linewidth=2.2, label=r"Classical Birthday ($\sim 1.25 \cdot 2^{n/2}$)")
        ax2.plot(small_n, q_small, "s-", color="royalblue", linewidth=2.2, label=r"Quantum Simon ($n + 0.6$)")
        ax2.axvline(x=3, color="gray", linestyle=":", label="Toy Scale ($n=3$)")

        for i, (cn, qn) in enumerate(zip(c_small, q_small)):
            ax2.annotate(f"{cn:.1f}", (small_n[i], cn), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8, color="darkorange")
            ax2.annotate(f"{qn:.1f}", (small_n[i], qn), textcoords="offset points", xytext=(0, -12), ha="center", fontsize=8, color="royalblue")

        ax2.set_title("Small Scale Behavior ($n=2$ to $8$): Crossover Analysis", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Hash Bit-Length $n$", fontsize=10)
        ax2.set_ylabel("Oracle Queries Required (Linear)", fontsize=10)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend(fontsize=9, loc="upper left")

        plt.suptitle("Quantum vs Classical Query Complexity for Toy Hash Collision", fontsize=13, fontweight="bold", y=0.98)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close(fig)

    def run_empirical_scaling(self, max_n: int = 9, trials_per_n: int = 30, seed: int = 42,
                              save_path: str = "figures/empirical_scaling_benchmark.png") -> Dict:
        """
        Runs empirical Monte Carlo benchmarks of classical collision searches across n=3 to max_n.
        Compares with quantum query bounds and records raw data.
        """
        random.seed(seed)
        n_values = list(range(3, max_n + 1))
        empirical_means = []
        empirical_stds = []
        theoretical_birthday = []
        quantum_expected = []

        for n in n_values:
            s_val = (1 << (n - 1)) | 1
            s_cand = format(s_val, f"0{n}b")
            hash_fn = ToyHashFunction(s=s_cand, n=n)
            finder = ClassicalCollisionFinder(hash_fn)

            queries = []
            for _ in range(trials_per_n):
                q, _, _, _ = finder.find_collision_randomized()
                queries.append(q)

            m_q = float(np.mean(queries))
            s_q = float(np.std(queries))
            empirical_means.append(m_q)
            empirical_stds.append(s_q)
            theoretical_birthday.append(float(np.sqrt(np.pi * 2**(n - 1))))
            quantum_expected.append(float(n + 0.6))

        # Plot empirical data
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.errorbar(n_values, empirical_means, yerr=empirical_stds, fmt="o-", color="darkorange",
                    ecolor="peru", elinewidth=1.8, capsize=3.5, label="Empirical Classical Queries (Mean ± 1 SD)")
        ax.plot(n_values, theoretical_birthday, "--", color="brown", linewidth=2,
                label=r"Theoretical Birthday Bound ($\sqrt{\pi \cdot 2^{n-1}}$)")
        ax.plot(n_values, quantum_expected, "s-", color="royalblue", linewidth=2.2,
                label=r"Quantum Simon Oracle Queries ($n + \mathcal{O}(1)$)")

        ax.set_title(f"Empirical Classical Birthday Attack vs Quantum Bound ($n=3$ to {max_n})", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("Hash Bit-Length $n$", fontsize=10)
        ax.set_ylabel("Oracle Queries Consumed", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(save_path, dpi=300)
        plt.close(fig)

        return {
            "n_values": n_values,
            "empirical_means": empirical_means,
            "empirical_stds": empirical_stds,
            "theoretical_birthday": theoretical_birthday,
            "quantum_expected": quantum_expected,
            "trials_per_n": trials_per_n,
            "seed": seed
        }

if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    
    # 1. Classical Monte Carlo for n=3
    toy_hash = ToyHashFunction(s="110", n=3)
    finder = ClassicalCollisionFinder(toy_hash)
    mc_results = finder.run_monte_carlo(trials=1000, seed=12345)
    print("Classical Birthday Attack (n=3, 1000 trials):", mc_results)
    with open("results/classical_monte_carlo.json", "w") as f:
        json.dump(mc_results, f, indent=2)

    # 2. Complexity Scaling Plots
    comp = ComplexityComparison()
    comp.plot_theoretical_scaling()
    
    # 3. Empirical Scaling Experiment
    scaling_data = comp.run_empirical_scaling(max_n=9, trials_per_n=30, seed=42)
    with open("results/complexity_scaling.json", "w") as f:
        json.dump(scaling_data, f, indent=2)
    print("Complexity scaling data saved to: results/complexity_scaling.json")

    # 4. Display Comparison Table
    print("\n--- Theoretical Complexity Table ---")
    for r in comp.get_comparison_table():
        print(f"n={r['n']:3d} | Domain: {r['domain_size']:>6s} | Classical Exp: {r['classical_expected']:>10s} | Quantum: {r['quantum_expected']:>6s} | Speedup: {r['speedup_factor']:>10s} | {r['practical_notes']}")
