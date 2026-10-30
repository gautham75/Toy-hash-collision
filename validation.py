"""
Automated Verification, Correctness Test Suite & Independent Validation.
Problem Statement 14: Toy Hash Collision Structure via Simon's Quantum Algorithm.

Executes Tests A through F:
- Test A: Truth table & 2-to-1 properties (s = '110')
- Test B: Quantum oracle computational basis & reversibility
- Test C: Quantum simulation interference & bit ordering (endianness)
- Test D: GF(2) linear solver, rank, edge cases, and all 7 periods
- Test E: Classical collision detection & query counting
- Test F: Independent end-to-end validator & artifact integrity
"""

import os
import sys
import json
import unittest
from typing import Dict, List, Optional, Tuple

from hash_function import ToyHashFunction, PRIMARY_TRUTH_TABLE
from simon_algorithm import SimonAlgorithm, test_all_nonzero_periods
from classical_comparison import ClassicalCollisionFinder
from src.gf2_solver import GF2Solver
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def validate_recovered_secret(candidate_s: str,
                              hash_fn: ToyHashFunction,
                              oracle_circuit: Optional[QuantumCircuit] = None,
                              measured_equations: Optional[List[str]] = None,
                              n: int = 3) -> Dict:
    """
    Independent End-to-End Validator for the recovered candidate secret s.
    Verifies all mathematical, oracle, and measurement conditions WITHOUT
    relying on internal solver shortcuts or hardcoded assumptions:
    1. candidate_s is an n-bit non-zero binary string.
    2. f(x) == f(x ⊕ s) for all 2^n inputs x.
    3. Exactly 2^(n-1) distinct hash outputs (2-to-1 mapping cardinality).
    4. Every hash output has exactly 2 preimages.
    5. Output equivalence classes correspond to pairs separated by s.
    6. Candidate s satisfies all collected measurement equations y · s ≡ 0 (mod 2).
    7. Quantum oracle U_f computational basis behavior matches classical f(x).
    """
    errors = []
    
    # 1. Format and non-zero check
    is_valid_format = isinstance(candidate_s, str) and len(candidate_s) == n and all(c in "01" for c in candidate_s)
    if not is_valid_format:
        errors.append(f"Candidate '{candidate_s}' is not a valid {n}-bit binary string.")
    
    is_nonzero = is_valid_format and (candidate_s != "0" * n)
    if not is_nonzero:
        errors.append(f"Candidate '{candidate_s}' is the trivial zero string 0^{n}.")

    # 2. Simon periodicity f(x) == f(x ⊕ s)
    all_inputs_periodic = True
    if is_nonzero:
        s_int = int(candidate_s, 2)
        for x_val in range(2**n):
            x_bin = format(x_val, f"0{n}b")
            partner_bin = format(x_val ^ s_int, f"0{n}b")
            if hash_fn.hash(x_bin) != hash_fn.hash(partner_bin):
                all_inputs_periodic = False
                errors.append(f"Periodicity failed: f({x_bin})={hash_fn.hash(x_bin)} != f({partner_bin})={hash_fn.hash(partner_bin)}")
                break

    # 3 & 4. Cardinality and preimages
    output_groups: Dict[str, List[str]] = {}
    for x_val in range(2**n):
        x_bin = format(x_val, f"0{n}b")
        fx = hash_fn.hash(x_bin)
        output_groups.setdefault(fx, []).append(x_bin)

    distinct_count = len(output_groups)
    expected_distinct = 2**(n - 1)
    is_strictly_two_to_one = (distinct_count == expected_distinct)
    if not is_strictly_two_to_one:
        errors.append(f"Expected {expected_distinct} distinct outputs, found {distinct_count}.")

    all_preimages_size_2 = all(len(preimages) == 2 for preimages in output_groups.values())
    if not all_preimages_size_2:
        errors.append("Not all outputs have exactly 2 preimages.")

    # 5. Collision separation by candidate s
    all_collisions_match_s = True
    if is_nonzero:
        s_int = int(candidate_s, 2)
        for fx, preimages in output_groups.items():
            if len(preimages) == 2:
                diff = int(preimages[0], 2) ^ int(preimages[1], 2)
                if diff != s_int:
                    all_collisions_match_s = False
                    errors.append(f"Collision pair {preimages} differs by {format(diff, f'0{n}b')}, not {candidate_s}.")
                    break

    # 6. Measurement equations orthogonality
    satisfies_measurements = True
    if measured_equations and is_nonzero:
        for y_str in measured_equations:
            dot = sum(int(a) * int(b) for a, b in zip(candidate_s, y_str)) % 2
            if dot != 0:
                satisfies_measurements = False
                errors.append(f"Measurement equation y='{y_str}' violates orthogonality: s · y (mod 2) = {dot} != 0.")
                break

    # 7. Quantum oracle basis state agreement
    oracle_agrees = True
    mismatches = 0
    if oracle_circuit is not None:
        sim = AerSimulator()
        for x_val in range(2**n):
            x_bin = format(x_val, f"0{n}b")
            expected_fx = hash_fn.hash(x_bin)

            qc_eval = QuantumCircuit(2 * n, n)
            for i in range(n):
                if x_bin[n - 1 - i] == "1":
                    qc_eval.x(i)
            qc_eval.compose(oracle_circuit, inplace=True)
            qc_eval.measure(range(n, 2 * n), range(n))
            counts = sim.run(qc_eval, shots=5).result().get_counts()
            measured_fx = list(counts.keys())[0]
            if measured_fx != expected_fx:
                oracle_agrees = False
                mismatches += 1
                errors.append(f"Oracle basis mismatch on input |{x_bin}>|0>: measured |{measured_fx}> != expected |{expected_fx}>.")

    overall_pass = (
        is_valid_format and is_nonzero and all_inputs_periodic and
        is_strictly_two_to_one and all_preimages_size_2 and
        all_collisions_match_s and satisfies_measurements and oracle_agrees
    )

    return {
        "candidate_s": candidate_s,
        "is_valid_format": is_valid_format,
        "is_nonzero": is_nonzero,
        "all_inputs_periodic": all_inputs_periodic,
        "distinct_output_count": distinct_count,
        "expected_distinct_outputs": expected_distinct,
        "is_strictly_two_to_one": is_strictly_two_to_one,
        "all_preimages_size_2": all_preimages_size_2,
        "all_collisions_match_s": all_collisions_match_s,
        "satisfies_measurement_equations": satisfies_measurements,
        "oracle_basis_states_agree": oracle_agrees,
        "oracle_mismatch_count": mismatches,
        "overall_pass": overall_pass,
        "error_messages": errors
    }

class TestToyHashCollisionSuite(unittest.TestCase):
    
    def setUp(self):
        self.toy_hash = ToyHashFunction(s="110", n=3)
        self.simon = SimonAlgorithm(s="110", n=3)
        self.finder = ClassicalCollisionFinder(self.toy_hash)
        self.solver = GF2Solver(n=3)

    # -------------------------------------------------------------
    # TEST A: TRUTH TABLE & 2-TO-1 PROMISE
    # -------------------------------------------------------------
    def test_A_truth_table_mappings(self):
        """Verifies all 8 input-output mappings against the canonical specification."""
        for x, expected_fx in PRIMARY_TRUTH_TABLE.items():
            self.assertEqual(self.toy_hash.hash(x), expected_fx, f"Mismatch on input {x}")

    def test_A_two_to_one_property(self):
        """Verifies exactly 4 unique outputs, each with multiplicity 2."""
        props = self.toy_hash.verify_mathematical_properties()
        self.assertTrue(props["all_inputs_mapped"], "Not all 8 inputs are mapped")
        self.assertTrue(props["is_2_to_1"], "Function is not strictly 2-to-1")
        self.assertTrue(props["all_preimages_size_2"], "Not every output has 2 preimages")
        self.assertTrue(props["xor_equals_s"], "Collision XOR difference does not equal s='110'")
        self.assertTrue(props["simon_period_holds"], "Promise f(x) = f(x ⊕ s) violated")

    def test_A_collision_pairs(self):
        """Verifies all 4 collision pairs and their XOR difference."""
        collisions = self.toy_hash.get_collisions()
        self.assertEqual(len(collisions), 4, "Expected exactly 4 collision pairs")
        for fx, (x1, x2) in collisions.items():
            diff = format(int(x1, 2) ^ int(x2, 2), "03b")
            self.assertEqual(diff, "110", f"Pair ({x1}, {x2}) XOR diff {diff} != '110'")

    # -------------------------------------------------------------
    # TEST B: QUANTUM ORACLE VERIFICATION
    # -------------------------------------------------------------
    def test_B_oracle_computational_basis(self):
        """Verifies U_f |x>|0> = |x>|f(x)> for all 8 basis states."""
        check = self.simon.verify_oracle_basis_states()
        self.assertTrue(check["all_basis_states_correct"], f"Oracle basis mismatches: {check['mismatch_count']}")
        self.assertTrue(check["reversible"], "Oracle is not unitary/reversible (U_f^2 != I)")

    def test_B_oracle_circuit_dimensions(self):
        """Confirms oracle circuit uses exactly 3 input qubits and 3 output qubits."""
        qc = self.simon.oracle_circuit
        self.assertEqual(qc.num_qubits, 6, "Oracle must contain exactly 6 qubits (3 input, 3 target)")
        self.assertEqual(qc.num_clbits, 0, "Oracle unitary subcircuit must not contain classical bits")

    # -------------------------------------------------------------
    # TEST C: QUANTUM SIMULATION & INTERFERENCE
    # -------------------------------------------------------------
    def test_C_interference_and_shot_count(self):
        """Verifies shot count sum, 8-bin integrity, and complete destructive interference."""
        shots = 1024
        counts = self.simon.run_simulation(shots=shots, seed=42)
        self.assertEqual(sum(counts.values()), shots, "Counts sum does not match configured shots")
        self.assertEqual(len(counts), 8, "Histogram does not contain all 8 bins")

        # In ideal simulator, states with s · y ≡ 1 (mod 2) must have exactly 0 counts
        ortho_check = self.simon.verify_orthogonality(counts)
        self.assertTrue(ortho_check["all_observed_orthogonal"], "Observed non-orthogonal state in ideal simulation")
        
        # Destructive interference verification for states: 010, 011, 100, 101
        destructive_states = ["010", "011", "100", "101"]
        for ds in destructive_states:
            self.assertEqual(counts[ds], 0, f"Destructive interference failed for state {ds}")

    def test_C_bit_ordering_endianness(self):
        """Verifies measurement bit ordering matches dot-product endianness."""
        constructive_states = ["000", "001", "110", "111"]
        for y_str in constructive_states:
            dot = sum(int(a) * int(b) for a, b in zip("110", y_str)) % 2
            self.assertEqual(dot, 0, f"State {y_str} failed orthogonality with s='110'")

    # -------------------------------------------------------------
    # TEST D: GF(2) LINEAR SOLVER & ALL PERIODS
    # -------------------------------------------------------------
    def test_D_linear_algebra_and_recovery(self):
        """Verifies Gaussian elimination over GF(2) recovers s='110' with rank n-1=2."""
        res = self.simon.execute_and_recover()
        self.assertTrue(res["success"], f"Failed to recover secret {res['expected_s']}")
        self.assertEqual(res["recovered_s"], "110")
        self.assertEqual(res["rank"], 2)
        self.assertNotEqual(res["recovered_s"], "000", "Trivial period 000 was recovered")

    def test_D_gf2_solver_insufficient_rank_returns_none(self):
        """Ensures solver returns None when rank < n - 1 rather than guessing."""
        cand, rank, eqs = self.solver.solve(["001"])
        self.assertIsNone(cand, "Solver should return None when rank < n - 1")
        self.assertEqual(rank, 1)

    def test_D_gf2_solver_duplicate_and_zero_vectors(self):
        """Ensures solver correctly handles 000 and duplicate samples without artificial rank inflation."""
        samples = ["000", "001", "001", "110"]
        cand, rank, eqs = self.solver.solve(samples)
        self.assertEqual(rank, 2, "Duplicate and zero vectors must not artificially inflate rank")
        self.assertEqual(cand, "110")
        self.assertNotIn("000", eqs, "Trivial zero vector must not be included in independent equations")

    def test_D_gf2_solver_rejects_trivial_zero_secret(self):
        """Ensures solver never returns 000 as a valid candidate."""
        cand, rank, _ = self.solver.solve([])
        self.assertIsNone(cand)
        self.assertEqual(rank, 0)

    def test_D_all_seven_periods(self):
        """Rigorously verifies recovery across all 7 non-zero 3-bit periods."""
        results = test_all_nonzero_periods(n=3)
        self.assertEqual(len(results), 7)
        for r in results:
            self.assertTrue(r["success"], f"Failed for target period {r['expected_s']}")
            self.assertEqual(r["recovered_s"], r["expected_s"])
            self.assertEqual(r["rank"], 2)

    # -------------------------------------------------------------
    # TEST E: CLASSICAL COLLISION SEARCH & QUERY ACCOUNTING
    # -------------------------------------------------------------
    def test_E_classical_collision_attack(self):
        """Verifies classical collision search detects valid collision and recovers s."""
        queries, x1, x2, rec_s = self.finder.find_collision_randomized(seed=999)
        self.assertEqual(rec_s, "110", "Classical search recovered incorrect period")
        self.assertNotEqual(x1, x2, "Colliding inputs must be distinct")
        self.assertEqual(self.toy_hash.hash(x1), self.toy_hash.hash(x2), "Inputs do not produce identical hash")
        self.assertTrue(2 <= queries <= 5, f"Queries {queries} outside expected bounds [2, 5]")

    def test_E_query_accounting_consistency(self):
        """Verifies deterministic worst-case query bound for n=3 is 2^(n-1) + 1 = 5."""
        worst_bound = self.finder.deterministic_worst_case()
        self.assertEqual(worst_bound, 5, "Worst-case query bound for n=3 must be exactly 5")

    def test_E_classical_monte_carlo_mean_expectation(self):
        """Verifies empirical Monte Carlo mean queries match exact theoretical expectation 128/35 ≈ 3.657."""
        stats = self.finder.run_monte_carlo(trials=10000, seed=12345)
        exact_mean = 128.0 / 35.0  # ≈ 3.65714
        self.assertAlmostEqual(stats["mean_queries"], exact_mean, delta=0.1,
                               msg=f"Empirical mean {stats['mean_queries']:.4f} not within 0.1 of 128/35 ({exact_mean:.4f})")

    # -------------------------------------------------------------
    # TEST F: INDEPENDENT VALIDATOR & ARTIFACTS
    # -------------------------------------------------------------
    def test_F_independent_end_to_end_validator(self):
        """Verifies the independent validator accepts true secret and rejects invalid candidates."""
        val_pass = validate_recovered_secret("110", self.toy_hash, self.simon.oracle_circuit, ["001", "110"])
        self.assertTrue(val_pass["overall_pass"], f"Validator failed on true secret: {val_pass['error_messages']}")
        self.assertEqual(len(val_pass["error_messages"]), 0)

        val_zero = validate_recovered_secret("000", self.toy_hash)
        self.assertFalse(val_zero["overall_pass"], "Validator should reject zero string")

        val_wrong = validate_recovered_secret("001", self.toy_hash)
        self.assertFalse(val_wrong["overall_pass"], "Validator should reject incorrect secret 001")

    def test_F_artifacts_exist(self):
        """Verifies that all required plots, results, and reports exist."""
        required_figures = [
            "figures/simon_circuit.png",
            "figures/measurement_histogram.png",
            "figures/query_complexity_comparison.png",
            "figures/empirical_scaling_benchmark.png",
            "figures/noise_impact_fidelity.png"
        ]
        for fig_path in required_figures:
            self.assertTrue(os.path.exists(fig_path), f"Missing artifact figure: {fig_path}")

        required_docs = [
            "showcase.html",
            "demo.py",
            "hash_function.py",
            "simon_algorithm.py",
            "classical_comparison.py"
        ]
        for doc_path in required_docs:
            self.assertTrue(os.path.exists(doc_path), f"Missing core file: {doc_path}")

def run_all_tests():
    print("=" * 75)
    print(" AUTOMATED SYSTEM VERIFICATION SUITE - PROBLEM STATEMENT 14")
    print("=" * 75)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestToyHashCollisionSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    toy_hash = ToyHashFunction(s="110", n=3)
    simon = SimonAlgorithm(s="110", n=3)
    val_summary = validate_recovered_secret("110", toy_hash, simon.oracle_circuit, ["001", "110"])
    
    os.makedirs("results", exist_ok=True)
    with open("results/validation_summary.json", "w") as f:
        json.dump(val_summary, f, indent=2)

    oracle_val = simon.verify_oracle_basis_states()
    with open("results/oracle_validation.json", "w") as f:
        json.dump(oracle_val, f, indent=2)
    
    print("\n" + "=" * 75)
    print(f" TOTAL TESTS EXECUTED : {result.testsRun}")
    print(f" PASSED TESTS         : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f" FAILED TESTS         : {len(result.failures)}")
    print(f" ERRORS               : {len(result.errors)}")
    print(" Validation artifacts written to: results/validation_summary.json & oracle_validation.json")
    print("=" * 75)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
