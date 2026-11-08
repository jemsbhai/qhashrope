# Model and dataset integrity attestation

**Problem.** A deployed model or a copied dataset is only trustworthy if it is bit-identical to the artifact that was evaluated and approved. The artifacts are gigabytes, so re-transferring or re-hashing them across organizations for every check is slow, and a hash alone does not bind the check to a governed approval process.

**qhashrope fit.** The holder of the deployed artifact and the holder of the certified artifact each produce a quantum fingerprint; a SWAP test attests equality with a message logarithmic in the artifact size. Combined with governed execution (budgeted, approval-gated, exactly replayable agent runs, as in the author's Pollard system), the check becomes part of an auditable chain: the artifact attested is the artifact approved is the artifact executed.

**Prototype status.** The verify primitive is demonstrated on byte-string payloads in simulation (18/18 sequence pairs classified correctly; 0.89 end-to-end accuracy under depolarizing noise p=0.02 after noise-calibrated thresholding). Applying it to real checkpoint files is an integration step, not a research step.

**Known limitation.** Near-identical artifacts (a checkpoint differing in a few weights) sit near the decision threshold with the current encoding; the error-correcting fingerprint encoding is the planned fix.
