# Bell-basis hardware run, 2026-11-08 (IBM Quantum, ibm_marrakesh)

Backend: **ibm_marrakesh** (156 qubits). SamplerV2, 4096 shots per circuit, one 48-qubit Bell-measurement (destructive SWAP test) circuit per pair, preset pass manager at optimization level 1, no readout mitigation. Submitted 2026-11-08T19:42:45.692061+00:00; job record in `bell_hardware_jobs.json`. Decision rule: a bit position is decided differ iff its Psi-sector fraction over shots exceeds 0.5; the pair is decided EQUAL iff decided-differ positions <= 3 (Golay radius-3 recombination, the same rule as the two-server per-bit protocol). Analysis by `retrieve_bell_hardware.py`; circuit and sector analysis in `bell_experiment.py`.

## Results

| Pair | Job | Truth | True Hamming | Decided differ | Bit errors | Decision | Correct |
|---|---|---|---|---|---|---|---|
| pair_01_control_identical (CONTROL identical (independent segment)) | dbod1ds4148s739ss180 | equal | 0 | 1 | 1 | equal | yes |
| pair_02_dna_identical (DNA identical) | dbod1e44148s739ss18g | equal | 0 | 1 | 1 | equal | yes |
| pair_03_dna_identical (DNA identical) | dbod1e8ou4as73cruuf0 | equal | 0 | 1 | 1 | equal | yes |
| pair_04_dna_identical (DNA identical) | dbod1ec4148s739ss19g | equal | 0 | 1 | 1 | equal | yes |
| pair_05_dna_1_substitution (DNA 1 substitutions) | dbod1egqtr0c73fljes0 | differ | 8 | 8 | 0 | differ | yes |
| pair_06_dna_1_substitution (DNA 1 substitutions) | dbod1es4148s739ss1ag | differ | 12 | 12 | 0 | differ | yes |
| pair_07_dna_1_substitution (DNA 1 substitutions) | dbod1eoou4as73cruug0 | differ | 16 | 17 | 1 | differ | yes |
| pair_08_dna_10_substitutions (DNA 10 substitutions) | dbod1f0ou4as73cruugg | differ | 12 | 13 | 1 | differ | yes |
| pair_09_dna_10_substitutions (DNA 10 substitutions) | dbod1f8qtr0c73fljeu0 | differ | 12 | 13 | 1 | differ | yes |
| pair_10_dna_10_substitutions (DNA 10 substitutions) | dbod1f8ou4as73cruuh0 | differ | 8 | 8 | 0 | differ | yes |
| pair_11_aspirin_vs_amide_analog (aspirin vs amide analog) | dbod1flt7fqc73cmtkb0 | differ | 12 | 13 | 1 | differ | yes |
| pair_12_benzene_vs_cyclohexane (benzene vs cyclohexane) | dbod1fs4148s739ss1dg | differ | 12 | 12 | 0 | differ | yes |
| pair_13_aspirin_identical (aspirin vs aspirin (identical)) | dbod1foou4as73cruuig | equal | 0 | 1 | 1 | equal | yes |

**13 of 13 pair decisions correct** under the majority rule; the per-shot vote rule also gives 13 of 13. Bit decision errors: 9 of 312 position decisions.

Per-pair detail (hardware Psi-sector fractions; simulation is the Aer depolarizing p=0.02 run in `bell_sim_results.json` on the identical circuits):

- **pair_01_control_identical** (CONTROL identical (independent segment)): agreeing positions Psi fraction 0.0059-0.6375; shots within radius 0.9021. Simulation p=0.02 for the same pair: decided differ 0, bit errors 0; noiseless decided differ 0.
- **pair_02_dna_identical** (DNA identical): agreeing positions Psi fraction 0.0073-0.7434; shots within radius 0.9045. Simulation p=0.02 for the same pair: decided differ 0, bit errors 0; noiseless decided differ 0.
- **pair_03_dna_identical** (DNA identical): agreeing positions Psi fraction 0.0085-0.7524; shots within radius 0.9067. Simulation p=0.02 for the same pair: decided differ 0, bit errors 0; noiseless decided differ 0.
- **pair_04_dna_identical** (DNA identical): agreeing positions Psi fraction 0.0088-0.7488; shots within radius 0.8936. Simulation p=0.02 for the same pair: decided differ 0, bit errors 0; noiseless decided differ 0.
- **pair_05_dna_1_substitution** (DNA 1 substitutions): agreeing positions Psi fraction 0.0112-0.3254; differing positions 0.8579-0.9905; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 8, bit errors 0; noiseless decided differ 8.
- **pair_06_dna_1_substitution** (DNA 1 substitutions): agreeing positions Psi fraction 0.0107-0.0591; differing positions 0.8787-0.9873; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 12, bit errors 0; noiseless decided differ 12.
- **pair_07_dna_1_substitution** (DNA 1 substitutions): agreeing positions Psi fraction 0.0115-0.7571; differing positions 0.8713-0.9907; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 16, bit errors 0; noiseless decided differ 16.
- **pair_08_dna_10_substitutions** (DNA 10 substitutions): agreeing positions Psi fraction 0.0095-0.7454; differing positions 0.8770-0.9785; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 12, bit errors 0; noiseless decided differ 12.
- **pair_09_dna_10_substitutions** (DNA 10 substitutions): agreeing positions Psi fraction 0.0127-0.7715; differing positions 0.8679-0.9890; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 12, bit errors 0; noiseless decided differ 12.
- **pair_10_dna_10_substitutions** (DNA 10 substitutions): agreeing positions Psi fraction 0.0059-0.3020; differing positions 0.8796-0.9885; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 8, bit errors 0; noiseless decided differ 8.
- **pair_11_aspirin_vs_amide_analog** (aspirin vs amide analog): agreeing positions Psi fraction 0.0071-0.7830; differing positions 0.8823-0.9836; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 12, bit errors 0; noiseless decided differ 12.
- **pair_12_benzene_vs_cyclohexane** (benzene vs cyclohexane): agreeing positions Psi fraction 0.0063-0.3240; differing positions 0.8838-0.9849; shots within radius 0.0. Simulation p=0.02 for the same pair: decided differ 12, bit errors 0; noiseless decided differ 12.
- **pair_13_aspirin_identical** (aspirin vs aspirin (identical)): agreeing positions Psi fraction 0.0098-0.7322; shots within radius 0.9165. Simulation p=0.02 for the same pair: decided differ 0, bit errors 0; noiseless decided differ 0.

## Resource counts: the optimization claim

Abstract Bell circuit: 48 qubits, 24 CX, depth 4 in the abstract gate set (fingerprint preparation, one parallel CNOT layer, one parallel Hadamard layer, measurement). Transpiled onto ibm_marrakesh with the preset pass manager (optimization level 1), every one of the 13 circuits came out at **24 CZ and depth 8**: the layout placed the 24 position pairs on disjoint adjacent qubit pairs, so no SWAP routing was inserted and the abstract cost survived transpilation exactly.

Reference points on the same backend and pass manager: the monolithic 49-qubit SWAP test transpiled to 495 CZ at depth 1026 (recorded in `hardware_jobs.json` for the exploratory job of the per-bit hardware run), and the two-server per-bit protocol needs 24 separate 3-qubit circuits per pair. The Bell circuit replaces the monolithic network's 495 two-qubit gates with 24, a factor of about 21x fewer, at about 128x shallower depth, and replaces the per-bit protocol's 24 circuit executions with 1.

## What the hardware did and did not show

The destructive SWAP test was executed end-to-end on a real device for all 13 comparisons of the simulation suite: 13 of 13 decisions correct, 9 individual position errors in 312 position decisions, with no readout mitigation and no per-pair calibration. Unlike the Aer depolarizing model, the real device also has readout error, T1/T2 decoherence and crosstalk; the numbers above include all of those effects and are reported as measured. Caveats: one device, one calibration cycle, 4096 shots per circuit; the fingerprints are basis states, so this validates the verification circuit and its resource counts on hardware, not a communication-complexity advantage (that requires the phase fingerprint). Simulation validation before submission (bell_experiment.py): noiseless decided-differ exactly equal to the true Hamming distance on all 13 pairs; depolarizing p=0.02 gave 13/13 under the majority rule and 13/13 under the vote rule, 0 bit errors.
