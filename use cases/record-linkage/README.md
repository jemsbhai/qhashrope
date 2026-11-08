# Record linkage without disclosure

**Problem.** Two institutions, for example two hospitals, need to deduplicate or link records: is this the same patient on both sides? Privacy law and policy forbid pooling the records to find out, and most linkage questions are really equality questions about one record at a time.

**qhashrope fit.** Each institution fingerprints its copy of the record locally. The SWAP test outputs one bit, same or different, and the fingerprints reveal almost nothing else about the record. Equality is the only disclosure, which is exactly the constraint health and administrative data impose.

**Prototype status.** The equality primitive is demonstrated in simulation (18/18 pairs; separation gradient measured from identical down to 10 substitutions). A realistic record schema and field-level encoding are the next steps.

**Known limitation.** Exact equality is brittle for records with formatting differences (name spellings, date formats). A production version needs a canonicalization step before fingerprinting, and near-duplicate detection is a different, harder problem than the equality case demonstrated here.
