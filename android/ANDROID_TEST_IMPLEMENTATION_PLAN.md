# Android TEST Implementation Plan v0.1

## Status

- Product: **Modest/Hijab Capsule Closet Lite**
- Decision: **TEST**
- Production BUILD authorized: **NO**
- Android implementation class: **engineering prototype / parity implementation**
- Canonical HTML candidate SHA-256:
  `861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171`

The physical P01-P07 campaign has not been honestly completed. It remains evidence debt even if the operator elects to proceed with Android engineering.

## Strategy

Use a thin Android shell around the already verified local-first HTML behavior instead of rewriting the UI before demand/behavior evidence exists.

The Android build packages the repository's existing `prototype/index.html` directly as an app asset. There is no second HTML copy.

The Gradle `verifyPrototypeSha` task fails the build if the canonical prototype bytes drift from the expected tested SHA.

## Android responsibilities

Native Android owns only platform-bound behavior:

1. installable application shell;
2. stable in-app HTTPS asset origin via `WebViewAssetLoader`;
3. physical Android Back delivery into WebView history;
4. system photo/file picker integration;
5. sanitized JSON/CSV export into Android Downloads;
6. lifecycle/reopen handling;
7. security boundary around navigation and local content.

Product behavior and UI remain owned by the canonical HTML candidate during this TEST phase.

## Explicit non-goals

- no account;
- no cloud sync;
- no server/backend;
- no ads;
- no billing;
- no recommendations;
- no shopping;
- no analytics expansion;
- no Compose rewrite;
- no feature redesign;
- no Play publication;
- no production signing.

## First engineering gate

Codex must prove:

1. `verifyPrototypeSha` PASS;
2. debug APK builds;
3. APK installs on API 36 emulator;
4. launch/render PASS;
5. first save + reload persistence PASS;
6. duplicate decision + real emulator system Back PASS inside native shell;
7. third save + Matrix PASS;
8. photo picker PASS;
9. exports appear in Downloads and remain sanitized;
10. no external navigation/network dependency;
11. accessibility/TalkBack smoke where environment permits.

Only after those pass should a physical APK be installed on the Samsung test device.

## Evidence rule

Do not call the Android app production-ready from build success alone.

Any PASS must identify:
- source commit;
- prototype SHA;
- APK SHA;
- emulator/device environment;
- replay command or human-observation boundary.
