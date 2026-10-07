# Codex Task — MHCCl HTML Image Fixture Emulator Verification

TASK: MHCCl-HTML-IMAGE-FIXTURE-EMU-001
BRANCH: html-image-fixture-emulator-v0.1
DECISION: TEST

Use the existing working Android emulator if available, preferably:
- AVD: task-s3-api36
- API: 36

Do not modify prototype/index.html.

1. Checkout the branch and verify:
   sha256 prototype/index.html
   Expected:
   861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171

2. Generate fixtures:
   python3 tests/image-fixtures/generate_fixtures.py

3. Validate every generated file against:
   tests/image-fixtures/generated/manifest.json

4. Push generated PNG fixtures to emulator Downloads, e.g.
   adb push tests/image-fixtures/generated/*.png /sdcard/Download/

5. Use the exact standalone HTML candidate, not the Android APK shell.
   Prefer the same Chrome/local-file runtime previously proven on emulator.
   If direct local file is blocked by emulator/browser policy, record HOLD_ENVIRONMENT and use localhost only as supplemental evidence, not as a replacement for local-file behavior.

6. Execute the scenarios in tests/image-fixtures/EMULATOR_TEST_SPEC.md.
   Use real Android file picker interactions on the emulator.
   Automation is allowed because this is emulator evidence, but record exact commands/tooling.
   Do not inject image data directly into JS and do not bypass the picker.

7. Capture bounded screenshots/logs for:
   - first image attached
   - replace image
   - picker cancel
   - reopen persistence
   - sanitized export

8. Verify exports contain no image bytes/data URLs and no excluded private text fields.

9. Produce:
   evidence/html-image-fixture-emulator/RESULT.json
   evidence/html-image-fixture-emulator/REPORT.md
   evidence/html-image-fixture-emulator/TIMELINE.csv
   evidence/html-image-fixture-emulator/ENVIRONMENT.json

10. Status:
   PASS / PASS_WITH_HOLDS / HOLD / FAIL

Do not push raw screenshots or personal/environment-sensitive paths publicly.
Do not merge to main.
Do not authorize BUILD, release, Artifact Freeze, or publication.
