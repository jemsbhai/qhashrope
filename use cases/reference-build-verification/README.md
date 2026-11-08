# Reference build verification

**Problem.** Two labs comparing genomic results have to be analysing against the same reference. Version drift is a quiet, common failure mode: one group on GRCh38 with GENCODE 44, another on the same assembly with GENCODE 47, a pipeline pinned to GRCh37 years ago. The results differ, nobody's code is wrong, and the discrepancy surfaces months later as an irreproducibility argument. The release record that defines "the reference" is small (assembly, patch, annotation source and release, file manifest), but it lives in pipeline configs on both sides and is rarely checked as a record in its own right.

**qhashrope fit.** Treat the build-and-release record as the string it is. Each lab fingerprints the record its pipeline actually carries; a SWAP test decides whether the two labs are on the identical build and annotation release before any results are compared. The check is cheap enough to run at pipeline start, which is where drift has to be caught: the equality bit is a precondition for the comparison to mean anything.

**Prototype status.** Measured in this folder: `refbuild_demo.py` ran both verifiers on three release-record pairs (noiseless MPS simulator, 4096 shots per pair, global threshold 0.75; full output in `results.json`). Classical hashrope 3/3, quantum fingerprint 3/3, including the realistic failure case, same assembly with the annotation release differing. The identical pair was also run under depolarizing noise p = 0.02 in both circuit forms; see below.

**Known limitation.** The record is a claim about the files, not a check of them. A lab whose record says GENCODE 44 but whose annotation file was truncated or swapped in transit passes this test; verifying the data files themselves is the replica-equality case at full record size, and this case deliberately covers the metadata layer where drift actually starts. Both sides must also serialize the record the same way (release naming differs between Ensembl and GENCODE conventions for the same content), so a canonical record format is a precondition, as everywhere in this folder set.

## Measured results (fixed encoding, 2026-11-08)

Demo: `refbuild_demo.py`; data: `results.json`. Settings: noiseless
AerSimulator (matrix_product_state), 4096 shots per pair, global threshold
0.75, Golay-encoded fingerprint.

| Case | Quantum P(0) | Decision |
|---|---|---|
| identical build and annotation release record | 1.0000 | equal |
| annotation release differing (GENCODE 44 to 45) | 0.4888 | differ |
| a different assembly build (GRCh37 record) | 0.4841 | differ |

Classical hashrope agrees on all three pairs (3/3); quantum 3/3. The
GENCODE 44 to 45 change is the case this folder exists for: same
assembly, same everything, one version field different, and the pair
reads at the analytic floor rather than passing as "close enough".

Two-server variant, identical pair, depolarizing noise p = 0.02:
monolithic P(0) = 0.7236, called differ (wrong); per-bit P(0) values in
[0.9573, 0.9763], 0 bits decided differ, Golay radius-3 decision equal
(correct). The monolithic failure on an identical pair at this noise
level is the stage-5 result from the root RESULTS.md, reproduced here
on a release-record payload.
