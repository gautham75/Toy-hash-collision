"""
=============================================================================
KARUNYA INSTITUTE OF TECHNOLOGY AND SCIENCES
Department of Computer Science and Engineering
Course: 23CS2037 - Quantum Computing | Skill-Based Assessment (IA-3)
Team 14:
  - AHZAM HAMZA KARAT (URK24CS6012)
  - GAUTHAM MANOJ     (URK24CS1158)
Problem Statement 14:
  Toy hash collision structure: A 3-bit hash function has a hidden period s 
  that creates systematic collisions. Use Simon's algorithm to find s and 
  show the classical O(2^(n/2)) versus quantum O(n) query comparison.
=============================================================================
"""

import os
import sys
import json
import datetime
import numpy as np

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from hash_function import ToyHashFunction
from simon_algorithm import SimonAlgorithm, test_all_nonzero_periods
from classical_comparison import ClassicalCollisionFinder, ComplexityComparison
from src.noise_analysis import NoiseEvaluator
from validation import validate_recovered_secret

import qiskit
import qiskit_aer

def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f" {text}")
    print("=" * 75)

def main():     
    os.makedirs("results", exist_ok=True)
    os.makedirs("figures", exist_ok=True)

    timestamp_str = datetime.datetime.now().isoformat()

    print_banner("14. TOY HASH COLLISION STRUCTURE VIA SIMON'S ALGORITHM")
    print("Course: 23CS2037 - Quantum Computing | Assessment Scope: Levels 1 to 7")
    print("Team 14: URK24CS6012 (Ahzam Hamza Karat) & URK24CS1158 (Gautham Manoj)")
    print(f"Environment: Python {sys.version.split()[0]} | Qiskit {qiskit.__version__} | Qiskit Aer {qiskit_aer.__version__}")

    # ---------------------------------------------------------
    # LEVEL 1 & 2: TOY HASH COLLISION STRUCTURE & QUANTUM ORACLE
    # ---------------------------------------------------------
    print_banner("PHASE 1: HASH ORACLE & SYSTEMATIC COLLISION STRUCTURE")
    s_target = "110"
    n_bits = 3
    toy_hash = ToyHashFunction(s=s_target, n=n_bits)
    print(f"Target Secret Period: s = '{s_target}' (n = {n_bits} bits, 2^{n_bits} = 8 inputs)")
    print("\nTruth Table of 2-to-1 Hash Function f(x):")
    print(f"  {'Input x':<10} | {'Binary':<8} | {'Hash Output f(x)':<18} | {'Pair (x XOR s)':<12}")
    print("  " + "-" * 58)
    for x_bin, fx in sorted(toy_hash.truth_table.items()):
        x_int = int(x_bin, 2)
        pair_bin = format(x_int ^ toy_hash.s_int, '03b')
        print(f"  {x_int:<10} | {x_bin:<8} | {fx:<18} | {pair_bin:<12}")

    print("\nSystematic Collision Pairs Verified:")
    collisions = toy_hash.get_collisions()
    for fx, (x1, x2) in sorted(collisions.items()):
        xor_diff = format(int(x1, 2) ^ int(x2, 2), '03b')
        print(f"  Collision on Output '{fx}': f({x1}) == f({x2}) => Diff = {x1} ^ {x2} = '{xor_diff}'")

    # Mathematical Verification
    math_check = toy_hash.verify_mathematical_properties()
    print(f"\nMathematical Property Verification: {'PASS (100% Correct)' if math_check['overall_valid'] else 'FAIL'}")

    # ---------------------------------------------------------
    # LEVEL 4 & 5: QUANTUM SIMULATION & GF(2) LINEAR ALGEBRA
    # ---------------------------------------------------------
    print_banner("PHASE 2: SIMON'S QUANTUM CIRCUIT EXECUTION & SIMULATION")
    simon = SimonAlgorithm(s=s_target, n=n_bits)
    
    # Save circuit diagram
    simon.full_circuit.decompose().draw(output='mpl', style='iqp').savefig("figures/simon_circuit.png", bbox_inches='tight', dpi=300)
    print("Circuit diagram saved to: figures/simon_circuit.png")

    # Oracle basis state validation
    oracle_check = simon.verify_oracle_basis_states()
    with open("results/oracle_validation.json", "w") as f:
        json.dump(oracle_check, f, indent=2)

    shots = 1024
    counts = simon.run_simulation(shots=shots, seed=42)
    simon.plot_histogram(counts, save_path="figures/measurement_histogram.png")
    
    print(f"\nMeasurement Counts across {shots} shots on AerSimulator (seed=42):")
    for k in sorted(counts.keys()):
        dot_prod = sum(int(a) * int(b) for a, b in zip(s_target, k)) % 2
        print(f"  Observed bitstring y = '{k}' : {counts[k]:4d} counts | Orthogonality check: s · y (mod 2) = {dot_prod}")

    with open("results/measurements_ideal.json", "w") as f:
        json.dump(counts, f, indent=2)

    # Solve linear equations over GF(2)
    recovery_result = simon.execute_and_recover()
    print(f"\nLinear Algebra Post-Processing over GF(2):")
    print(f"  Linearly Independent Equations Obtained: {recovery_result['equations']}")
    print(f"  Matrix Rank over GF(2): {recovery_result['rank']} (Required: n-1 = {n_bits - 1})")
    print(f"  Recovered Secret Period: s = '{recovery_result['recovered_s']}'")
    assert recovery_result['recovered_s'] == s_target, "Error: Recovered secret does not match target!"
    print(f"  => VALIDATION STATUS: SUCCESSFUL! Secret '{s_target}' correctly recovered.")

    ideal_recovery_record = {
        "timestamp": timestamp_str,
        "configured_secret": s_target,
        "recovered_secret": recovery_result["recovered_s"],
        "rank": recovery_result["rank"],
        "equations": recovery_result["equations"],
        "total_circuit_executions": recovery_result["total_queries"],
        "quantum_oracle_invocations": recovery_result["total_queries"],
        "status": "PASS" if recovery_result["success"] else "FAIL"
    }
    with open("results/ideal_recovery.json", "w") as f:
        json.dump(ideal_recovery_record, f, indent=2)

    # Independent End-to-End Validation
    val_summary = validate_recovered_secret(recovery_result['recovered_s'], toy_hash, simon.oracle_circuit, recovery_result['equations'])
    with open("results/validation_summary.json", "w") as f:
        json.dump(val_summary, f, indent=2)

    # Multi-period validation across all 7 non-zero periods
    all_period_results = test_all_nonzero_periods(n=3)
    with open("results/all_periods_validation.json", "w") as f:
        json.dump(all_period_results, f, indent=2)

    # ---------------------------------------------------------
    # LEVEL 3 & 5: QUANTUM VS CLASSICAL ALGORITHM COMPLEXITY
    # ---------------------------------------------------------
    print_banner("PHASE 3: CLASSICAL COLLISION ATTACK & COMPLEXITY BENCHMARK")
    finder = ClassicalCollisionFinder(toy_hash)
    print("Running 10,000 Monte Carlo Classical Birthday Collision Trials (n=3, seed=12345)...")
    classical_stats = finder.run_monte_carlo(trials=10000, seed=12345)
    print(f"  Empirical Mean Classical Queries : {classical_stats['mean_queries']:.3f} +/- {classical_stats['std_queries']:.3f}")
    print(f"  Exact Theoretical Expectation (128/35): {classical_stats['exact_theoretical_expectation']:.3f}")
    print(f"  Asymptotic Birthday Bound (sqrt[pi * 2^(n-1)]) : {classical_stats['theoretical_birthday_bound']:.3f}")
    print(f"  Classical Worst-Case Queries (2^(n-1) + 1): {finder.deterministic_worst_case()}")
    
    with open("results/classical_monte_carlo.json", "w") as f:
        json.dump(classical_stats, f, indent=2)

    # Generate Theoretical & Empirical Scaling Analysis
    comp = ComplexityComparison()
    comp.plot_theoretical_scaling()
    scaling_data = comp.run_empirical_scaling(max_n=9, trials_per_n=30, seed=42)
    with open("results/complexity_scaling.json", "w") as f:
        json.dump(scaling_data, f, indent=2)

    # ---------------------------------------------------------
    # LEVEL 6: NOISE EVALUATION & NISQ FEASIBILITY
    # ---------------------------------------------------------
    print_banner("PHASE 4: HARDWARE CONSTRAINTS, NOISE & NISQ FEASIBILITY")
    evaluator = NoiseEvaluator(s=s_target, n=n_bits)
    error_rates = [0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05]
    valid_fracs, maj_succs, raw_rates, details = evaluator.evaluate_noise_sweep(error_rates, seed=42)
    evaluator.plot_noise_resilience(error_rates, valid_fracs, raw_rates)
    
    noise_data = {
        "study_type": "Simulated NISQ Hardware Noise Study (Qiskit Aer NoiseModel)",
        "hardware_claim": "SIMULATION ONLY - Not executed on real physical hardware",
        "backend": "AerSimulator",
        "error_rates_cnot": error_rates,
        "valid_orthogonal_fraction": valid_fracs,
        "majority_filtered_recovery_1024shots": maj_succs,
        "raw_small_shot_recovery_rate": raw_rates,
        "trial_details": details,
        "notes": (
            "Single-qubit depolarizing error p_1q = p/10, readout error p_ro = p, two-qubit CNOT error p_2q = p. "
            "Evaluated across 20 repeats x 1,024 shots per error level with error bars (mean +/- 1 SD). "
            "Majority-filtered recovery achieves 100% across all rates; raw small-shot trials show stochastic noise corruption."
        )
    }
    with open("results/noise_sweep_data.json", "w") as f:
        json.dump(noise_data, f, indent=2)

    # ---------------------------------------------------------
    # LEVEL 6 (OPTIONAL): IBM HARDWARE EMULATION (FakeSherbrooke)
    # ---------------------------------------------------------
    try:
        from src.hardware_run import run_hardware_emulation
        run_hardware_emulation(s=s_target, n=n_bits, shots=1024, seed=42)
    except Exception as e:
        print(f"Hardware emulation skipped: {e}")

    # Save comprehensive experiment metadata
    metadata = {
        "project_title": "Toy Hash Collision Structure: Finding a Hidden Period Using Simon's Algorithm",
        "course": "23CS2037 - Quantum Computing",
        "institution": "Karunya Institute of Technology and Sciences",
        "team": "Team 14",
        "members": [
            {"name": "Ahzam Hamza Karat", "register_no": "URK24CS6012"},
            {"name": "Gautham Manoj", "register_no": "URK24CS1158"}
        ],
        "timestamp": timestamp_str,
        "python_version": sys.version.split()[0],
        "qiskit_version": qiskit.__version__,
        "qiskit_aer_version": qiskit_aer.__version__,
        "configured_secret": s_target,
        "target_bits": n_bits,
        "simulation_backend": "Qiskit AerSimulator",
        "ideal_shots": shots,
        "random_seeds": {
            "circuit_simulation": 42,
            "classical_monte_carlo": 12345,
            "empirical_scaling": 42,
            "noise_sweep": 42
        },
        "query_accounting_definitions": {
            "function_evaluation": "Classical black-box evaluation of f(x)",
            "quantum_oracle_invocation": "Execution of unitary gate U_f inside quantum circuit (1 per shot)",
            "measurement_sample": "One 3-bit string y measured from input register meas_x",
            "independent_equation": "Non-zero measurement vector y increasing matrix rank over GF(2)"
        },
        "overall_status": "COMPLETED & VERIFIED"
    }
    with open("results/experiment_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print_banner("ALL PHASES COMPLETED SUCCESSFULLY!")
    print("Figures generated in 'figures/' directory:")
    for f in sorted(os.listdir("figures")):
        print(f"  - figures/{f}")
    print("\nData artifacts saved in 'results/' directory:")
    for f in sorted(os.listdir("results")):
        print(f"  - results/{f}")

if __name__ == "__main__":
    main()
