# Mutation and Adversarial Verification Report

Candidate SHA-256: `861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171`

Genuine isolated-copy verifier replay: **YES**

| ID | Invariant | Result | Exit | Target |
|---|---|---|---:|---|
| M01 | AC-007 — remove duplicate-decision Back precedence | DETECTED | 1 | isolated copy |
| M02 | AC-007 — route duplicate Back to builder discard path | DETECTED | 1 | isolated copy |
| M03 | AC-007 — map duplicate close/Back to open saved | DETECTED | 1 | isolated copy |
| M04 | AC-007 — make duplicate close/Back destructive | DETECTED | 1 | isolated copy |
| M05 | AC-007 — remove non-destructive Keep editing transition | DETECTED | 1 | isolated copy |
| M06 | AC-002/003 — Cancel commits edited snapshot | DETECTED | 1 | isolated copy |
| M07 | AC-004 — stale photo callback mutates canceled edit | DETECTED | 1 | isolated copy |
| M08 | AC-005 — Draft edit is labeled as committed garment save | DETECTED | 1 | isolated copy |
| M09 | AC-002 — Draft A edit selects Draft B | DETECTED | 1 | isolated copy |
| M10 | AC-003 — Back bypasses dirty edit semantics | DETECTED | 1 | isolated copy |
| M11 | AC-012 — evidence includes recognition label | DETECTED | 1 | isolated copy |
| M12 | AC-012 — evidence includes photo payload | DETECTED | 1 | isolated copy |
| M13 | AC-011 — Matrix row header loses semantic scope | DETECTED | 1 | isolated copy |
| M14 | AC-011 — Matrix loses accessible Saved/Not saved state | DETECTED | 1 | isolated copy |
| M15 | AC-011 — Matrix introduces grid semantics | DETECTED | 1 | isolated copy |
| M16 | AC-011 — Matrix relation region reintroduces pan-x trap | DETECTED | 1 | isolated copy |
| M17 | AC-011 — third save forces Matrix | DETECTED | 1 | isolated copy |
| M18 | AC-011 — remove Done for now | DETECTED | 1 | isolated copy |
| M19 | AC-011 — reintroduce old activation prerequisite | DETECTED | 1 | isolated copy |
| M20 | AC-011 — clone existing committed piece instead of reuse | DETECTED | 1 | isolated copy |
| M21 | AC-011 — persistence failure displays success | DETECTED | 1 | isolated copy |
| M22 | AC-009 — Save another creates two records | DETECTED | 1 | isolated copy |
| M23 | AC-008 — Open saved creates another Outfit | DETECTED | 1 | isolated copy |
| M24 | AC-016 — mark physical Android PASS | DETECTED | 1 | isolated copy |
| M25 | AC-016 — mark TalkBack PASS | DETECTED | 1 | isolated copy |
| M26 | AC-016 — promote failed runtime to PASS | DETECTED | 1 | isolated copy |
| M27 | AC-016 — infer BUILD authorization from deterministic PASS | DETECTED | 1 | isolated copy |

Total mutations attempted: **27**
Mutations detected: **27**
Escaped mutations: **0**

Each mutation started from the exact good candidate, changed one isolated copy, executed the verifier, and required a non-zero result. The canonical candidate was not modified.
