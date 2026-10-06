# 02 — Implementation-Ready Specification for Codex

## Engineering objective

Take the exact v3.1e HTML behavioral candidate as the baseline and create a repo-owned, maintainable TEST artifact that preserves all current behavior while implementing only the final ChatGPT-locked recovery corrections.

## Product form for this stage

- self-contained local-first HTML behavioral prototype;
- no backend;
- no account;
- no remote API;
- local browser storage;
- local photo processing;
- research-only sanitized evidence export.

This stage is **not** the production Android application.

## Canonical domain objects

### Garment

Committed reusable piece.

Required:
- stable local ID;
- category.

Optional:
- short recognition label;
- local photo.

Practical state:
- AVAILABLE;
- LAUNDRY;
- TEMPORARILY_UNAVAILABLE.

### DraftGarment

Uncommitted piece inside one DraftOutfit.

Must remain distinct from committed Garment until parent Outfit commit.

### DraftOutfit

Transactional state containing:
- existing committed garment IDs;
- DraftGarments;
- draft Hijab relationships where applicable.

### Outfit

Primary committed memory:
- stable ID;
- base garment IDs;
- optional practical note;
- created timestamp.

Hijab alternatives are relationship records, not ranking.

### HijabOptionRelationship

User-approved Outfit ↔ Hijab relationship.

No score, rank, match quality, or recommendation authority.

## Commit invariants

- draft piece selection/photo/name is not a commit;
- Outfit success is shown only after local persistence succeeds;
- persistence failure restores a recoverable transaction;
- committed existing garments are reused by ID, not cloned;
- Capsule/Pairing views derive from committed relationships only.

## Builder validity

An Outfit requires at least one main clothing piece:
- TOP, BOTTOM, DRESS, OUTER, or OTHER.

HIJAB/SHOES alone do not satisfy Save validity.

Disabled Save must communicate this prerequisite.

## Draft Piece edit contract

Implement an edit path from each DraftGarment chip/card.

Suggested interaction:
- visible `Edit` action or edit affordance associated with the draft piece;
- open the existing Add Piece sheet in edit mode;
- edit state starts from a snapshot of that DraftGarment;
- `Cancel` restores snapshot;
- `Done` updates the DraftGarment only;
- `Remove` remains separate from Edit.

Must support:
- category change;
- short label change/clear;
- photo replace/remove;
- stale-photo callback rejection;
- dirty Cancel/Back semantics;
- accessible labels/dialog/focus behavior equal to existing Add Piece semantics.

Instrumentation:
- `draft_piece_edit_started`
- `draft_piece_edit_saved`
- `draft_piece_edit_canceled`
- properties must exclude free-text/photo bytes.

## Duplicate Outfit decision contract

Replace the current binary `confirm()` path for an exact duplicate with an explicit decision surface.

Condition:
- exact base relation + applicable saved hijab relation already represented;
- preserve existing duplicate-detection semantics.

Actions:
- `Keep editing`
- `Open saved outfit`
- `Save another version`

Behavior:
- Keep editing: no mutation; Builder remains.
- Open saved outfit: discard only the current duplicate DraftOutfit, set current Outfit, navigate Detail.
- Save another version: continue commit.
- no branch may be inferred from closing the dialog; close/Back defaults to Keep editing.

Instrumentation:
- `duplicate_outfit_decision`
- property `choice = keep_editing | open_saved | save_another`
- existing outfit ID is allowed; no media/free text.

## Photo-size resilience

Do not invent a restrictive buyer-facing photo limit without device evidence.

Codex may implement a configurable pre-decode guard if needed for memory safety, but:
- threshold must be a named TEST configuration constant;
- rejection/warning copy must be corrective;
- user can continue without a photo;
- threshold is not marketed as a production capability limit;
- actual threshold should be finalized from target-device evidence.

## Existing v3.1e invariants to preserve

- visible Done for now;
- third Save does not force Matrix;
- native semantic relationship table;
- no `touch-action: pan-x` gesture trap;
- Matrix hit/miss cells expose text state;
- modal dialog semantics + Escape/focus containment/restoration;
- selected/current state exposed programmatically;
- availability is truthful instant-save with Saved feedback;
- Available-now representative hijab is truthful;
- practical-note false-dirty fix;
- stale Add Piece/Hijab photo completion is ignored;
- storage failure rollback;
- pairing persistence rollback;
- sanitized evidence excludes source media/free-text;
- Android Back semantics remain mapped to product exits;
- TEST tools remain research-only.

## Deferred product work

Do not implement unless a later task explicitly promotes it:
- edit committed base Outfit composition;
- delete/archive;
- backup/restore buyer UX;
- production DB/media architecture;
- cloud;
- Android native shell;
- monetization;
- mature retrieval/search/tagging;
- recommendation or AI.
