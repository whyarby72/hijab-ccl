# Hijab Capsule Closet Lite — Android TEST Shell

This directory contains the Android TEST implementation. It intentionally reuses the verified HTML candidate from `../prototype/index.html` instead of maintaining a duplicate web source.

## Toolchain

- Android Gradle Plugin: 9.2.0
- Gradle target for wrapper generation: 9.4.1
- JDK: 17
- compileSdk / targetSdk: 36
- minSdk: 24
- AndroidX Activity: 1.13.0
- AndroidX WebKit: 1.17.1

## First local build

From this directory:

```bash
gradle wrapper --gradle-version 9.4.1
./gradlew :androidApp:verifyPrototypeSha
./gradlew :androidApp:assembleDebug
```

The build is expected to fail if `prototype/index.html` does not match the canonical SHA configured in `gradle.properties`.

## Runtime architecture

The app loads:

`https://appassets.androidplatform.net/assets/index.html`

through `WebViewAssetLoader`.

No INTERNET permission is requested. External navigation is rejected.

Android-native glue currently covers:
- system Back → WebView history;
- HTML image file chooser → Android document picker;
- blob-backed sanitized exports → Android Downloads;
- WebView state save/restore.

## Governance

This is a TEST engineering implementation, not a release build. No production signing, Play publication, monetization, or BUILD promotion is authorized here.
