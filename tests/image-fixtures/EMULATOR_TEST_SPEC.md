# MHCCl HTML Image Fixture Emulator Verification v0.1

## Binding
- Product decision: TEST
- Canonical HTML path: `prototype/index.html`
- Canonical HTML SHA-256: `861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171`
- Candidate source MUST NOT change.

## Fixture intent
Fixtures are test-only. They must never be bundled into the customer product.

### Scenarios
1. Add top photo using `top_white_01.png`.
2. Add bottom photo using `bottom_black_01.png`.
3. Save first outfit and confirm both images remain attached.
4. Reuse one existing piece in a second outfit; ensure image ownership remains stable.
5. Replace one draft image with `replacement_test.png`; verify only intended draft changes.
6. Open picker then cancel; verify no stale callback attaches an image.
7. Select `tiny_boundary.png`; verify app remains stable.
8. Select `large_memory_smoke.png`; verify no crash/reset and normal persistence behavior.
9. Add two hijab fixtures and verify saved hijab relationships remain user-owned, not auto-ranked.
10. Close/reopen runtime and verify persisted image relationships.
11. Remove image and verify only selected garment loses image.
12. Export sanitized JSON/CSV and verify fixture bytes/data URLs/recognition labels/practical notes do not leak.

## Evidence ownership
- Fixture identity: MACHINE_OBSERVED.
- Picker interaction on emulator: MACHINE_OBSERVED when automated.
- Visual semantic correctness: MACHINE_PLUS_SCREENSHOT or HUMAN_OBSERVED.
- Any ambiguity => HOLD, not PASS.

## Stop conditions
Stop on wrong-owner image, stale callback attachment, silent reset, corrupted saved outfit, privacy leak, or crash.

## Pass gate
`HTML_IMAGE_FIXTURE_EMULATOR_VERIFICATION_PASS` requires all critical scenarios to pass while canonical HTML SHA remains exact.
