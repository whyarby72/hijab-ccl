# Deterministic Verification Report

Previous candidate SHA-256: `ef3ee3e1d9134884b2ab9b71b6f0ca72f011a43d4993a2dbf3448ba769558d46`

Final candidate SHA-256: `861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171`

Command:

```sh
npm run verify
```

Result: **81/81 PASS**

Mutation result:

| Measure | Result |
|---|---:|
| Deliberate mutations attempted | 27 |
| Mutations detected | 27 |
| Escaped mutations | 0 |
| Adversarial claim-ceiling controls | 6/6 PASS |

The suite includes inherited protection-family checks, explicit AC-007 Back state convergence, state/recovery fixtures, sanitization fixtures, and genuine isolated-copy mutation replay. No browser/device/manual result is inferred from this output.
