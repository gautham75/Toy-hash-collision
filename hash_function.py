"""
Toy Hash Function Implementation & Mathematical Verification.
Implements the 3-bit hash function f: {0,1}^3 -> {0,1}^3 with hidden period s = '110'.

Promise (Simon's Problem):
    f(x) = f(y) <=> y = x OR y = x ⊕ s
"""

from typing import Dict, List, Tuple

# Canonical primary truth table as mandated by Problem Statement 14
PRIMARY_TRUTH_TABLE: Dict[str, str] = {
    "000": "000",
    "001": "001",
    "010": "010",
    "011": "011",
    "100": "010",
    "101": "011",
    "110": "000",
    "111": "001",
}

class ToyHashFunction:
    """
    3-bit Toy Hash Function with hidden linear collision structure s.
    """
    def __init__(self, s: str = "110", n: int = 3):
        if len(s) != n:
            raise ValueError(f"Secret period length {len(s)} does not match n={n}")
        if s == "0" * n:
            raise ValueError("Secret period s cannot be the trivial zero string 0^n")
        self.n = n
        self.s = s
        self.s_int = int(s, 2)
        self.truth_table = self._build_truth_table()

    def _build_truth_table(self) -> Dict[str, str]:
        """
        Constructs truth table for the 2-to-1 function f(x).
        For the primary test case s = '110', returns the exact canonical table.
        For general s, uses a consistent linear projection: f(x) = x ⊕ x_j * s,
        where j is the first bit position (from LSB) where s_j == 1.
        """
        if self.s == "110" and self.n == 3:
            return PRIMARY_TRUTH_TABLE.copy()

        # General construction for arbitrary s
        j = None
        for bit_idx in range(self.n):
            if self.s[self.n - 1 - bit_idx] == "1":
                j = bit_idx
                break

        table = {}
        for x_val in range(2**self.n):
            x_bin = format(x_val, f"0{self.n}b")
            # bit j of x (0 is LSB)
            xj = int(x_bin[self.n - 1 - j])
            fx_val = x_val ^ (xj * self.s_int)
            table[x_bin] = format(fx_val, f"0{self.n}b")
        return table

    def hash(self, x: str) -> str:
        """Evaluates the hash function f(x) on an n-bit string."""
        if len(x) != self.n:
            raise ValueError(f"Input string '{x}' has length {len(x)}, expected {self.n}")
        return self.truth_table[x]

    def verify_mathematical_properties(self) -> Dict[str, bool]:
        """
        Rigorously tests all mathematical properties of the hash function:
        1. All 8 inputs map to valid n-bit outputs.
        2. Exactly 2^(n-1) unique outputs (2-to-1 mapping).
        3. Every output has exactly 2 preimages.
        4. For every pair (x, y) with f(x) == f(y) and x != y: x ⊕ y == s.
        5. No unintended collisions exist.
        """
        # Group by output
        collisions: Dict[str, List[str]] = {}
        for x_bin, out_bin in self.truth_table.items():
            collisions.setdefault(out_bin, []).append(x_bin)

        is_2_to_1 = len(collisions) == 2**(self.n - 1)
        all_pairs_size_two = all(len(preimages) == 2 for preimages in collisions.values())

        # Check XOR difference for every colliding pair
        xor_correct = True
        for fx, preimages in collisions.items():
            if len(preimages) == 2:
                diff = int(preimages[0], 2) ^ int(preimages[1], 2)
                if diff != self.s_int:
                    xor_correct = False
                    break

        # Check promise f(x) == f(x ⊕ s) for every single x
        period_holds = True
        for x_bin in self.truth_table:
            x_partner = format(int(x_bin, 2) ^ self.s_int, f"0{self.n}b")
            if self.truth_table[x_bin] != self.truth_table[x_partner]:
                period_holds = False
                break

        return {
            "all_inputs_mapped": len(self.truth_table) == 2**self.n,
            "is_2_to_1": is_2_to_1,
            "all_preimages_size_2": all_pairs_size_two,
            "xor_equals_s": xor_correct,
            "simon_period_holds": period_holds,
            "overall_valid": is_2_to_1 and all_pairs_size_two and xor_correct and period_holds
        }

    def get_collisions(self) -> Dict[str, Tuple[str, str]]:
        """Returns the dictionary of collision pairs keyed by hash output."""
        grouped: Dict[str, List[str]] = {}
        for x, fx in self.truth_table.items():
            grouped.setdefault(fx, []).append(x)
        return {fx: (pair[0], pair[1]) for fx, pair in grouped.items() if len(pair) == 2}

if __name__ == "__main__":
    toy_hash = ToyHashFunction(s="110", n=3)
    results = toy_hash.verify_mathematical_properties()
    print("Truth Table:")
    for x, fx in sorted(toy_hash.truth_table.items()):
        print(f"  f({x}) = {fx}")
    print("\nCollision Pairs:")
    for fx, (x1, x2) in toy_hash.get_collisions().items():
        diff = format(int(x1, 2) ^ int(x2, 2), "03b")
        print(f"  f({x1}) == f({x2}) == {fx} | XOR Difference: {diff}")
    print(f"\nMathematical Verification Status: {results['overall_valid']}")
