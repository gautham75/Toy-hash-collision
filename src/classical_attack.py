"""
Classical Collision Attack Simulation (Birthday Attack).
Simulates classical brute-force and birthday attacks to find collisions in the hash function.
"""

import os
import sys
import random
import numpy as np
from typing import Tuple, Dict, Optional

# Ensure project root in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.oracle import ToyHashOracle

class ClassicalCollisionAttack:
    """
    Simulates classical attacks against the n-bit hash function with hidden period s.
    """
    def __init__(self, oracle: ToyHashOracle):
        self.oracle = oracle
        self.n = oracle.n
        self.s = oracle.s

    def random_birthday_attack(self) -> Tuple[int, str, str, str]:
        """
        Executes a random birthday attack:
        Repeatedly selects random unseen inputs, queries the hash oracle,
        and checks for a collision f(x1) == f(x2).
        Returns:
            queries: Total queries consumed until first collision.
            x1: First input.
            x2: Second colliding input.
            recovered_s: x1 ⊕ x2.
        """
        seen_hashes: Dict[str, str] = {}
        all_possible_inputs = [format(i, f'0{self.n}b') for i in range(2**self.n)]
        random.shuffle(all_possible_inputs)
        
        queries = 0
        for x in all_possible_inputs:
            queries += 1
            h = self.oracle.classical_evaluate(x)
            if h in seen_hashes:
                x_prev = seen_hashes[h]
                recovered_s = format(int(x, 2) ^ int(x_prev, 2), f'0{self.n}b')
                return queries, x_prev, x, recovered_s
            seen_hashes[h] = x

        raise RuntimeError("No collision found despite exhaustive search!")

    def deterministic_worst_case_queries(self) -> int:
        """
        Maximum queries required in the worst-case classical query strategy:
        In a 2-to-1 function with 2^(n-1) unique outputs, adversary may query
        one element from each pair before encountering a collision on query 2^(n-1) + 1.
        """
        return 2**(self.n - 1) + 1

    def run_monte_carlo(self, trials: int = 10000, seed: int = 12345) -> Dict[str, float]:
        """
        Runs Monte Carlo evaluation to compute empirical query statistics.
        Definition of queries: Number of f-evaluations made up to and including
        the one that reveals the collision (min 2, max 2^(n-1)+1 = 5 for n=3).
        Exact expectation for 2-to-1 function on 8 inputs: 128/35 ≈ 3.657.
        """
        if seed is not None:
            random.seed(seed)
        query_counts = []
        for _ in range(trials):
            q, x1, x2, rec_s = self.random_birthday_attack()
            assert rec_s == self.s, f"Recovered period {rec_s} != true period {self.s}"
            query_counts.append(q)

        exact_exp = 128.0 / 35.0 if self.n == 3 else float(np.sqrt(np.pi * 2**(self.n - 1)))

        return {
            "n": self.n,
            "trials": trials,
            "seed": seed,
            "mean_queries": float(np.mean(query_counts)),
            "std_queries": float(np.std(query_counts)),
            "min_queries": int(np.min(query_counts)),
            "max_queries": int(np.max(query_counts)),
            "exact_theoretical_expectation": float(exact_exp),
            "theoretical_birthday_bound": float(np.sqrt(np.pi * 2**(self.n - 1))),
            "query_definition": "Number of f-evaluations made up to and including the one revealing collision"
        }

if __name__ == "__main__":
    oracle = ToyHashOracle(s="110", n=3)
    attack = ClassicalCollisionAttack(oracle)
    print("Running 10,000 Monte Carlo classical birthday attack trials for n=3 (s='110')...")
    stats = attack.run_monte_carlo(trials=10000, seed=12345)
    for k, v in stats.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    print(f"  worst_case_bound (2^(n-1)+1): {attack.deterministic_worst_case_queries()}")
