# IBM Quantum hardware run: account and job record

This file records how the hardware results in HARDWARE_RESULTS.md were produced, so the run is reproducible and auditable. The API key is intentionally not stored in this repository.

## Account

- Platform: IBM Quantum Platform (quantum.cloud.ibm.com), region us-east (Washington DC)
- Account holder: Muntaser Syed; IBMid msyed2011@my.fit.edu (Florida Institute of Technology)
- Account created 2026-11-08 for the Qiskit Fall Fest 2026 hackathon at Florida Tech
- IBM Cloud account type: trial (dashboard showed 29 days remaining on 2026-11-08, so the trial wrapper runs to about 2026-12-07; the IBM Quantum Open plan itself is free)

## Service instance

- Name: qhashrope
- Plan: Open (free), 10 minutes of QPU time per month
- Instance ID: 699aa462-4483-4d9c-aaf5-b318050df08d
- CRN: crn:v1:bluemix:public:quantum-computing:us-east:a/6d2362d566ad4491b79925a8aed1a30c:699aa462-4483-4d9c-aaf5-b318050df08d::
- Access: API key named "qhashrope", created 2026-11-08; the key value is held only in the local Qiskit configuration of the machine that submitted the jobs, never in this repository

## Accessible backends (2026-11-08)

All 156-qubit Heron r2 devices, online, region us-east:

- ibm_marrakesh (used for this run; fewest pending jobs at submission)
- ibm_fez
- ibm_kingston

## Jobs submitted 2026-11-08 (SamplerV2, 4,096 shots per circuit)

| Job ID | Content | Status |
|---|---|---|
| dbo8ukc4148s73924tfg | Pair A, identical DNA segments, 24 per-bit SWAP circuits | DONE, harvested |
| dbo8ukgou4as73b5ml6g | Pair B, benzene vs cyclohexane, 24 per-bit SWAP circuits | DONE, harvested |
| dbo8ul5t7fqc73ako2pg | Pair C, aspirin vs amide analog, 24 per-bit SWAP circuits | DONE, harvested |
| dbo8uudt7fqc73ako33g | Exploratory monolithic 49-qubit SWAP circuit, pair A (transpiled depth about 1,026, 495 CZ) | DONE, harvested 2026-11-08: P(0) = 0.4814 on the identical pair, decision differ (incorrect); see HARDWARE_RESULTS.md |

Submission script: submit_hardware.py. Submission record: hardware_jobs.json. Results: HARDWARE_RESULTS.md and hardware_results.json. The monolithic job completed later on 2026-11-08 and was harvested and analysed by retrieve_hardware_results.py; its measured result is recorded in HARDWARE_RESULTS.md and hardware_results.json.

## Jobs submitted 2026-11-10 (ibm_fez, SamplerV2, 4,096 shots per circuit)

The remaining 10 pairs of the 13-pair two-server suite, same per-bit
construction, on a second Heron r2 device. All DONE the same day:
10 of 10 decisions correct, zero bit errors in 240 bit decisions.
Results: HARDWARE_FULL_RESULTS.md and hardware_full_results.json.
Submission script: submit_hardware_full.py; harvest:
retrieve_hardware_full.py; submission record: hardware_full_jobs.json.

| Job ID | Pair |
|---|---|
| dbpk4bk4148s739uovjg | CONTROL identical (independent segment) |
| dbpk4boqtr0c738eilug | DNA identical #2 |
| dbpk4cc4148s739uovkg | DNA identical #3 |
| dbpk4cgqtr0c738eim00 | DNA 1 substitution #1 |
| dbpk4coqtr0c738eim0g | DNA 1 substitution #2 |
| dbpk4d0ou4as73ctqo7g | DNA 1 substitution #3 |
| dbpk4ddt7fqc7389j2mg | DNA 10 substitutions #1 |
| dbpk4ds4148s739uovng | DNA 10 substitutions #2 |
| dbpk4e0ou4as73ctqoag | DNA 10 substitutions #3 |
| dbpk4e8qtr0c738eim70 | aspirin vs aspirin (identical) |

The same session also ran qfourierrope's first hardware jobs on
ibm_fez (monolithic dbpk4i5t7fqc7389j2tg, decomposed
dbpk4i8ou4as73ctqohg); those are recorded in that repository.
