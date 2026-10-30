# UI Changelog & Data Harmonization Report

**Project:** Toy Hash Collision Structure via Simon's Quantum Algorithm  
**Course:** 23CS2037 — Quantum Computing (IA-3)  
**Institution:** Karunya Institute of Technology and Sciences  
**Team 14:** Ahzam Hamza Karat (URK24CS6012) & Gautham Manoj (URK24CS1158)  
**Date:** October 2026  
**File Modified:** `showcase.html` (Rebuilt via `build_showcase.py`)  
**Backup Preserved:** `showcase_old.html`  

---

## 1. Executive Summary of Changes

The project showcase dashboard (`showcase.html`) was completely re-engineered from the ground up to create an authoritative, publication-grade, single-file interactive presentation designed specifically for faculty evaluation across Levels 1–7 (40 Marks).

The new dashboard operates **100% offline from `file://` URIs with zero external requests or CDN dependencies**. It replaces external MathJax dependencies with clean, universally supported Unicode and HTML math representations, and bundles all figures and numerical data directly into the file via `build_showcase.py`.

---

## 2. Hard Technical Architecture & Offline Guarantee

| Dimension | Previous State | New Upgraded Architecture |
|:---|:---|:---|
| **File Structure** | Separate assets / external links | **Single self-contained HTML file** (3.68 MB) |
| **External Dependencies** | MathJax CDN (`cdn.jsdelivr.net`) | **Zero external dependencies**; full offline operation via `file://` |
| **Math Formatting** | MathJax LaTeX rendering | Pure **Unicode & semantic HTML** (`⊕`, `·`, `|ψ⟩`, `√`, `<sub>`, `<sup>`) |
| **Asset Pipeline** | Relative image paths (`figures/*.png`) | **Base64 data URIs** embedded directly in HTML via `build_showcase.py` |
| **Data Ingestion** | Runtime `fetch()` calls (blocked by file:// CORS) | Inlined JSON data package (`DATASET`) in JavaScript |
| **Generator Script** | Manual edits | Re-executable Python script: `python build_showcase.py` |

---

## 3. Data Inconsistencies Identified & Harmonized

### A. Truth Table Measurement Orthogonality Column Fix
- **Issue:** The previous version of the truth table included a column titled `"Measurement Orthogonality (s·y mod 2)"` evaluated directly on the input bitstring $x$. Mathematically, $s \cdot y \equiv 0 \pmod 2$ applies exclusively to *measurement outcomes* $y \in \{0,1\}^3$ in the dual space, not input domain preimages $x$.
- **Resolution:**
  1. Removed the column from the primary 8-row hash truth table.
  2. Created a dedicated **Measurement Outcomes Orthogonality Table** over all 8 outcomes $y \in \{0,1\}^3$, displaying binary strings, $s \cdot y \pmod 2$, theoretical probabilities ($0.25$ or $0.00$), observed AerSimulator shot counts, and explicit `Allowed` vs `Forbidden` subspace status.

### B. Classical Query Accounting & Exact Expectation ($128/35$)
- **Issue:** Old notes cited a classical Monte Carlo mean of ~2.47, which stemmed from an uncalibrated zero-indexed query counter.
- **Ground-Truth Mathematics:** For a 2-to-1 function on $N=8$ inputs partitioned into 4 collision pairs of size 2, sampling without replacement yields:
  $$P(Q=2) = \frac{1}{7} = \frac{5}{35}, \quad P(Q=3) = \frac{2}{7} = \frac{10}{35}, \quad P(Q=4) = \frac{12}{35}, \quad P(Q=5) = \frac{8}{35}$$
  $$E[Q] = 2\left(\frac{5}{35}\right) + 3\left(\frac{10}{35}\right) + 4\left(\frac{12}{35}\right) + 5\left(\frac{8}{35}\right) = \frac{128}{35} \approx 3.65714$$
- **Resolution:**
  1. Defined queries formally as the number of $f$-evaluations made up to and including the colliding query.
  2. Reran 10,000 Monte Carlo trials (`seed=12345`), yielding empirical mean **$3.650 \pm 0.983$ queries** (within $0.2\%$ of exact theory).
  3. Added automated unit test `test_E_classical_monte_carlo_mean_expectation` in `validation.py`, strictly asserting the empirical mean is within $0.1$ of $128/35$.
  4. Standardized the value **3.66 queries** across all reports, calculators, and UI tables.

### C. Speedup & Crossover Region Correction
- **Issue:** Previous documentation claimed "genuine exponential speedup only emerges at $n \ge 16$".
- **Resolution:**
  1. Corrected theoretical crossover: classical queries strictly exceed expected quantum circuit runs from **$n \approx 5\text{--}6$** ($n=5$: classical 7.09 vs quantum 5.60; $n=6$: classical 10.03 vs quantum 6.60).
  2. Clarified the quantum complexity model: while $n-1 = 2$ represents the *minimum* independent equations needed, the *expected* number of circuit runs under uniform sampling is:
     $$E[\text{Runs}] = \sum_{j=1}^{n-1} \frac{1}{1 - 2^{-j}} \approx (n-1) + 1.6067 \approx n + 0.6067 \approx 3.61 \text{ for } n=3$$
  3. Both values are displayed and explained in the scaling calculator with dynamic context notes.

### D. Architectural Justification for 6 Qubits with 2 Active Target Bits
- **Issue:** The hash function output has 4 distinct values $\{000, 001, 010, 011\}$, meaning output bit $y_2 \equiv 0$ and only 2 target bits are actively flipped.
- **Resolution:** Documented the architectural rationale:
  1. *Black-Box Cryptographic Generality:* Standard oracle query model $U_f: |x\rangle|y\rangle \to |x\rangle|y \oplus f(x)\rangle$ cannot assume coordinate redundancy *a priori*.
  2. *Canonical Unitary Interface:* Preserves standard $n+n$ quantum composability without coordinate leakage.
  3. *Idle Ancilla Verification:* Simulating $q_5$ explicitly confirms that target ancillae remain unentangled and idle in $|0\rangle$, preventing parasitic phase backaction.

---

## 4. UI & Interactive Features Added

1. **Top Metric Strip (6 KPI Cards):**
   - 17/17 Unit Tests Passed (100% Green).
   - 7/7 Hidden Periods Recovered (Rank 2 over GF(2)).
   - 1,024 Shots · 0 Forbidden Outcomes.
   - Classical Mean: 3.66 Queries ($n=3$, Exact $128/35$).
   - Quantum: $\approx 3.6$ Runs ($n=3$, Minimum 2 Equations).
   - Asymptotic Scaling ($n=30$): $\sim 32,768$ vs $\sim 31$ Runs.

2. **Interactive 2-to-1 Hash Explorer:**
   - 8-pill input selector ($x = 0\dots 7$).
   - Dynamic inspector displaying selected $x$, companion partner $x \oplus 110$, shared output digest $f(x)$, and collision verification.
   - Color-coded truth table highlighting the active collision class (Classes 0, 1, 2, 3).

3. **5-Step Simon Algorithm Stepper:**
   - Interactive Prev/Next and step-dot navigation.
   - Stage 0 (Initialization) $\to$ Stage 1 (First $H^{\otimes 3}$) $\to$ Stage 2 (Reversible Oracle $U_f$) $\to$ Stage 3 (Phase Interference) $\to$ Stage 4 (Measurement & Sampling).
   - Displays both Dirac state formulas and plain-English operational descriptions.

4. **Live In-Browser Simon Quantum Circuit Simulator:**
   - Single-shot sampler sampling $y \in \{000, 001, 110, 111\}$.
   - Real-time Gaussian elimination over GF(2) with automatic handling of trivial zero vectors (`000`) and duplicate vectors (which do not artificially inflate rank).
   - Dynamic rank counter and null space resolution.
   - Success banner upon reaching rank 2: `✓ Hidden Period s = 110 Successfully Recovered in K shots!`.
   - Auto-Run mode and 1,000-experiment batch simulator with real-time canvas histogram of shots needed.

5. **Live In-Browser Classical Birthday Collision Simulator:**
   - Single-trial interactive button sampling inputs without replacement, displaying lookup table accumulation and highlighting collision detection.
   - 10,000-trial batch simulator plotting query count histogram (2, 3, 4, 5) overlaid with exact theoretical expectation lines ($5/35, 10/35, 12/35, 8/35$).

6. **Asymptotic Scaling Calculator & Interactive Log Chart:**
   - Range slider for $n \in [3, 64]$ with preset buttons ($n=3, 5, 8, 16, 30, 64$).
   - Real-time HTML5 Canvas log-scale chart plotting classical and quantum scaling curves from $n=2$ to $n=20$.
   - Annotated crossover point ($n \approx 5.4$) and animated marker tracking selected $n$.
   - Dynamic context note explaining the computational regime (Toy Parity $\to$ Crossover $\to$ Exponential Advantage).

7. **Level 6 Technology Evaluation & IBM FakeSherbrooke (127Q) Emulation:**
   - Parameterized depolarizing noise study (20 repeats $\times$ 1,024 shots with $\pm 1\sigma$ error bars).
   - Physical hardware emulation card for IBM's 127-qubit `FakeSherbrooke` backend: Depth 16, 3 native ECR gates, 98.34% allowed subspace fidelity, and 100% majority recovery.
   - Resource scaling table ($n=3$ to $n=64$).
   - Post-quantum cryptographic security implications (Even-Mansour vs AES/SHA-256).

8. **Level 7 Certification Cards:**
   - Dedicated credential cards for Ahzam Hamza Karat (`URK24CS6012`) and Gautham Manoj (`URK24CS1158`).
   - Embedded badge artwork placeholders (`figures/ibm_badge_ahzam.png`, `figures/ibm_badge_gautham.png`).
   - Explicit `[TODO: Candidate Attachment Required - Pending Student Upload]` tags to preserve academic integrity without fabricating credential links.

9. **Evaluation Rubric Coverage Matrix:**
   - Comprehensive table mapping Levels 1 through 7 (40 Marks) directly to showcase sections, source code files, and report evidence.

10. **Interactive Figure Lightbox:**
    - Full-screen modal for all publication figures with zoom, caption display, Prev/Next navigation, and keyboard accessibility (`Esc`, `ArrowLeft`, `ArrowRight`).

11. **Print & PDF Stylesheet:**
    - Clean `@media print` rules: converts background to white, hides interactive buttons and sliders, sets `page-break-inside: avoid` on cards, and generates clean printable reports.

---

## 5. Verification & Validation Status

- `python build_showcase.py`: **SUCCESS** (regenerated `showcase.html`, 4,067,600 bytes).
- `python validation.py`: **17/17 tests passing in 0.180s** (0 failures, 0 errors).
- `python -m unittest tests/test_all.py`: **17/17 tests passing in 0.172s**.
- Backup file `showcase_old.html`: Preserved in repository root.
