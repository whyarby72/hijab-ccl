# AGENTS.md — Modest/Hijab Capsule Closet Lite TEST Prototype

## Authority

The product is in `TEST`.
Production `BUILD` is not authorized.

The files in this handoff define product semantics. Codex owns implementation, deterministic repair, tests, and repository engineering within this scope. It must not invent material product behavior.

## Product invariants

- Outfit is the primary saved memory.
- Garment is a reusable primitive.
- Capsule is derived relationship truth.
- Hijab options are user-approved relations, never recommendations.
- Availability is practical state.
- First value is the first saved known-good outfit.
- Third Outfit does not force Matrix.
- Matrix means saved participation, not compatibility.
- No mandatory full-wardrobe entry.
- Photo/name are optional.
- No AI/cloud/account/ads/social/shopping scope.

## Engineering permissions

Allowed:
- refactor for maintainability while preserving behavior;
- extract modules/tests from the single HTML;
- add deterministic fixtures;
- implement current-task acceptance;
- add CI/reproducible verification;
- add safe mechanical fixes discovered by tests if semantics are unchanged.

Escalate instead of deciding when:
- scope changes;
- buyer-facing promise changes materially;
- a new persistent object/lifecycle is proposed;
- destructive semantics change;
- privacy/evidence fields change materially;
- a remote dependency is proposed;
- production architecture is proposed;
- a behavioral hypothesis would be pre-resolved by a feature.

## Evidence

Every PASS must bind:
- source revision;
- exact artifact/version/hash;
- environment where relevant;
- fixture/state;
- command/steps;
- expected/actual;
- evidence output.

Mock/source tests do not prove physical-device/runtime behavior.

## Human authority

Human approval remains required for:
- material product scope;
- TEST → BUILD;
- Artifact Freeze;
- release/publication;
- irreversible external actions.
