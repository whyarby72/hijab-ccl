# Image fixture verification

Synthetic TEST-only garment fixtures for replayable photo-picker verification.

- No personal photos.
- No copyrighted source imagery.
- Binary fixtures are generated in CI from `generate_fixtures.py`.
- `FIXTURE_MANIFEST.json` binds the expected SHA-256 of each generated image.
- The generated fixture directory is uploaded as a workflow artifact for replay/audit.
- These assets are verification inputs, not product/buyer assets.

Primary scenarios:
1. initial photo selection;
2. replace;
3. remove;
4. picker cancel;
5. multiple-draft ownership separation;
6. transparent PNG conversion;
7. 64×64 boundary image;
8. large 2400×3200 compression;
9. save + process restart persistence.
