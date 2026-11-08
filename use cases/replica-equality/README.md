# Replica equality over constrained links

**Problem.** Distributed systems hold copies that must agree: database replicas, ledger copies, backup archives. Verifying that two large copies are still identical usually means transferring the data or trusting one side's word.

**qhashrope fit.** Quantum fingerprinting is one of the few proven exponential separations in communication complexity. In the simultaneous-message model, two parties each send a referee an O(log n) qubit fingerprint of an n-bit string, against O(sqrt(n)) classical bits for the same task without shared randomness. The referee's SWAP test decides equality. Nothing else about the data is communicated.

**Prototype status.** Demonstrated in simulation on 96 bp segment fingerprints (18/18 pairs correct, with a measured separation gradient from identical to 10 substitutions). This folder's case is the theory anchor for the whole project: the claim to state precisely, including the model it holds in.

**Known limitation.** The separation is a communication result, not a claim that today's hardware beats a classical hash for a single direct comparison. The honest boundary: two parties, a referee, no shared randomness, and privacy of the underlying string.
