# IBM Quantum hardware results: full two-server suite on ibm_fez

Run 2026-11-10 on **ibm_fez** (156-qubit Heron r2), IBM Quantum instance
"qhashrope" (Open plan), SamplerV2, 4,096 shots per circuit. Each pair
is tested with the two-server per-bit protocol: 24 independent 3-qubit
SWAP tests, one per Golay (24,12,8) codeword bit. A bit is decided
"differ" when its measured P(0) < 0.75; the pair is decided equal when
at most 3 bits differ (the Golay radius-3 rule), exactly as in the
simulation experiment (`two_server_experiment.py`).

The 2026-11-08 run on ibm_marrakesh covered 3 of the 13 suite pairs
(first DNA identical pair, benzene vs cyclohexane, aspirin vs amide
analog; see HARDWARE_RESULTS.md). This run covers the remaining 10,
so the per-bit protocol now has complete hardware coverage of the
13-pair suite across two devices.

| Pair | Truth | Codeword Hamming | Bits decided differ | Bit errors | Verdict |
|---|---|---|---|---|---|
| CONTROL identical (independent segment) | equal | 0 | 0 | 0 | equal, correct |
| DNA identical #2 | equal | 0 | 0 | 0 | equal, correct |
| DNA identical #3 | equal | 0 | 0 | 0 | equal, correct |
| DNA 1 substitution #1 | differ | 8 | 8 | 0 | differ, correct |
| DNA 1 substitution #2 | differ | 12 | 12 | 0 | differ, correct |
| DNA 1 substitution #3 | differ | 16 | 16 | 0 | differ, correct |
| DNA 10 substitutions #1 | differ | 12 | 12 | 0 | differ, correct |
| DNA 10 substitutions #2 | differ | 12 | 12 | 0 | differ, correct |
| DNA 10 substitutions #3 | differ | 8 | 8 | 0 | differ, correct |
| aspirin vs aspirin (identical) | equal | 0 | 0 | 0 | equal, correct |

## Summary

- 10 of 10 pair decisions correct.
- **Zero bit errors in 240 bit decisions.** Every pair's decided-differ
  count equals its true codeword Hamming distance exactly.
- Combined with the 2026-11-08 ibm_marrakesh run (3 pairs, 72 bit
  decisions, zero bit errors), the per-bit two-server protocol stands
  at **13 of 13 pairs correct and zero bit errors in 312 bit decisions
  across two Heron r2 devices**.

Job record: `hardware_full_jobs.json` (submission),
`hardware_full_results.json` (harvested per-bit P(0) values).
Scripts: `submit_hardware_full.py`, `retrieve_hardware_full.py`.
Job IDs are also listed in IBM_QUANTUM_RUN.md.
