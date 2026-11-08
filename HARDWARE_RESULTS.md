# Hardware run, 2026-11-08 (IBM Quantum, ibm_marrakesh)

Backend: **ibm_marrakesh** (156 qubits). SamplerV2, 4096 shots per circuit. Submitted 2026-11-08T15:03:43.946118+00:00; job record in `hardware_jobs.json`. Decision rule identical to the simulation: per-bit P(0) decided differ below 0.75; Golay radius-3 recombination (equal iff decided-differ <= 3). Analysis by `retrieve_hardware_results.py`.

## Per-bit two-server verification on hardware

| Pair | Job | Truth | True Hamming | Decided differ | Bit errors | R3 decision | Correct |
|---|---|---|---|---|---|---|---|
| A_dna_identical | dbo8ukc4148s73924tfg | equal | 0 | 0 | 0 | equal | yes |
| B_benzene_vs_cyclohexane | dbo8ukgou4as73b5ml6g | differ | 12 | 12 | 0 | differ | yes |
| C_aspirin_vs_amide_analog | dbo8ul5t7fqc73ako2pg | differ | 12 | 12 | 0 | differ | yes |

Per-bit P(0) detail (hardware | simulated depolarizing p=0.02 from `two_server_results.json`; noiseless analytic values are 1.0 for agreeing bits and 0.5 for differing bits):

- **A_dna_identical** (DNA identical (prototype suite, seeded segment vs itself)): hardware per-bit P(0) range 0.9456-0.9636; decided differ 0 of 24 (true Hamming 0); bit decision errors 0.
  Simulation p=0.02 for the same pair: per-bit P(0) range 0.9526-0.9741, decided differ 0, bit decision errors 0.
  Hardware per-bit P(0): [0.9521, 0.9561, 0.9541, 0.9517, 0.9592, 0.9614, 0.9514, 0.9614, 0.9565, 0.9519, 0.9463, 0.9636, 0.9575, 0.9573, 0.9568, 0.9492, 0.9456, 0.9558, 0.9548, 0.9478, 0.9553, 0.9629, 0.9521, 0.9558]
- **B_benzene_vs_cyclohexane** (benzene c1ccccc1 vs cyclohexane C1CCCCC1): hardware per-bit P(0) range 0.4922-0.9670; decided differ 12 of 24 (true Hamming 12); bit decision errors 0.
  Simulation p=0.02 for the same pair: per-bit P(0) range 0.4961-0.9734, decided differ 12, bit decision errors 0.
  Hardware per-bit P(0): [0.9614, 0.5056, 0.9541, 0.9604, 0.4939, 0.5264, 0.9561, 0.9592, 0.967, 0.532, 0.9541, 0.9636, 0.9631, 0.5046, 0.5151, 0.5059, 0.5051, 0.4922, 0.5315, 0.5125, 0.5049, 0.9648, 0.9573, 0.96]
- **C_aspirin_vs_amide_analog** (aspirin vs amide analog (one-character O to N)): hardware per-bit P(0) range 0.4880-0.9624; decided differ 12 of 24 (true Hamming 12); bit decision errors 0.
  Simulation p=0.02 for the same pair: per-bit P(0) range 0.4941-0.9753, decided differ 12, bit decision errors 0.
  Hardware per-bit P(0): [0.5017, 0.9585, 0.9529, 0.9536, 0.5105, 0.4998, 0.5098, 0.9563, 0.957, 0.9624, 0.9536, 0.5325, 0.9592, 0.488, 0.49, 0.9548, 0.5334, 0.9539, 0.5051, 0.9473, 0.9619, 0.5085, 0.5283, 0.5249]

## Exploratory monolithic 49-qubit SWAP test (pair A)

Not harvested in this run (dbo8uudt7fqc73ako33g=QUEUED). No result is claimed.

## What the hardware did and did not show

The per-bit two-server protocol was executed end-to-end on a real device: 3 of 3 pair decisions were correct under the same Golay radius-3 rule that classified 13/13 in the p=0.02 simulation. Across all harvested pairs there were 0 individual bit decision errors (a bit whose hardware P(0) fell on the wrong side of 0.75 relative to the true codeword bits). Unlike the Aer depolarizing model used in simulation, the real device also has readout error, T1/T2 decoherence and crosstalk; the numbers above include all of those effects and are reported as measured, bit errors included. The hardware run does not by itself establish a scaling claim: circuits were 3-qubit tests transpiled by the standard preset pass manager, one device, one calibration cycle.
