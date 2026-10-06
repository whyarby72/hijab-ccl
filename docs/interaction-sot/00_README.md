# Modest/Hijab Capsule Closet Lite — Interaction Source-of-Truth Pack v1.0

**Product decision:** TEST  
**BUILD authorization:** NO  
**Canonical product source:** `MODEST_HIJAB_CAPSULE_CLOSET_CANONICAL_PRODUCT_SPEC_v3.2_MATURE_STATE_v1.md`  
**Behavioral prototype lineage:** v3.1c / Android pre-test hardened artifact  
**Interaction procedure:** Universal Interaction Pre-Build Merge-Minimal Clean Patch v1.1.1 operating overlay

## Supersession note

The older handoff bundle used an onboarding/activation hypothesis of `10 pieces + 3 saved outfits`.
That is superseded for the current TEST by the later canonical v3.2 specification:

- onboarding: **Outfit-First**
- first value: **first saved known-good outfit**
- core activation: **third saved outfit + Capsule Matrix viewed**

The old 10-piece hypothesis is provenance only and must not be reintroduced as a mandatory gate without new evidence.

## Product truth preserved

- Primary buyer job: remember outfits that already work.
- Outfit is the primary saved user object/job.
- Garment is a reusable primitive captured only when needed by an outfit.
- Capsule is a derived relationship view, not an analytics dashboard.
- Hijab pairing is user-approved memory, not recommendation/compatibility scoring.
- Availability is practical state, not style recommendation.
- Photo and short recognition label are optional.
- Local-first, no mandatory account, no AI stylist, no social feed.
- Current navigation remains **Outfits | Capsule**.
- BUILD remains blocked pending behavioral evidence and explicit human approval.

## Pack contents

1. `01_DOMAIN_OBJECT_DATA_MODEL.md`
2. `02_STATE_LIFECYCLE_MODEL.md`
3. `03_MASTER_WIREFLOW.md`
4. `04_ACTION_CONTROL_REGISTER.md`
5. `05_FAILURE_RECOVERY_REVERSIBILITY_MATRIX.md`
6. `06_PRETEST_INTERACTION_AUDIT.md`
7. `07_CURRENT_INTERACTION_STATE.json`

## Status convention

- `CANONICAL_TEST` — required for current behavioral TEST.
- `PROPOSED_TEST_FIX` — correction required to protect test validity; not a proven market preference.
- `HYPOTHESIS` — intentionally unresolved pending tester evidence.
- `POST_VALIDATION` — not part of current TEST.
- `REJECTED` — outside current product thesis.

This pack is interaction/specification work only. It does not authorize Android engineering BUILD, Repo Factory invocation for production, Artifact Freeze, release, or publication.
