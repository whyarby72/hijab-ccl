# 02 — State / Lifecycle Model

## 1. Primary lifecycle states

```text
LAUNCH
  ↓ Start
OUTFITS_HOME_EMPTY_OR_EXISTING
  ↓ Save outfit
BUILDER_DRAFT
  ↓ successful commit
SAVE_SUCCESS
  ├─ Done for now → OUTFITS_HOME
  ├─ Save another → BUILDER_DRAFT
  └─ after third saved outfit / activation condition → ACTIVATION_MATRIX
                                                ↓ Continue
                                           OUTFITS_HOME
```

The current TEST must never force `Save another` as the only visible continuation after success.

## 2. Canonical state groups

### A. Stable destinations

- `OUTFITS_HOME`
- `CAPSULE_OVERVIEW`
- `OUTFIT_DETAIL`
- `HIJAB_PAIRING_MATRIX` (conditional)
- `ACTIVATION_MATRIX` (activation payoff, not permanent home)

### B. Transactional/transient surfaces

- `BUILDER_DRAFT_EMPTY`
- `BUILDER_DRAFT_DIRTY`
- `ADD_PIECE_CLEAN`
- `ADD_PIECE_DIRTY`
- `ADD_PIECE_PHOTO_PENDING`
- `HIJAB_EDITOR_CLEAN`
- `HIJAB_EDITOR_DIRTY`
- `HIJAB_NEW_DRAFT`
- `AVAILABILITY_SHEET`
- `NOTE_EDITOR_CLEAN`
- `NOTE_EDITOR_DIRTY`
- `TEST_TOOLS`

### C. Failure/degraded states

- `PHOTO_DECODE_FAILED`
- `PHOTO_ASYNC_CANCELED_OR_STALE`
- `STORAGE_UNAVAILABLE`
- `STORAGE_COMMIT_FAILED`
- `DRAFT_RESTORED`
- `NO_AVAILABLE_OUTFITS`
- `EVIDENCE_EXPORT_FAILED`

## 3. Draft / dirty rules

### Builder

Dirty when any of:
- existing garment selected;
- DraftGarment created/changed;
- optional hijab relationship changed inside current outfit draft.

Back/Cancel from dirty Builder:
- ask to discard;
- confirm → delete uncommitted draft objects and leave;
- refuse → remain in Builder.

Unexpected reload/interruption:
- may restore DraftOutfit;
- restoration must not convert draft to committed outfit.

### Add Piece

Dirty when any category/label/photo state has been created or changed.

Cancel/scrim/system Back:
- clean → close;
- dirty → explicit discard confirmation;
- if photo async is pending, mark operation/session canceled before closing.

### Hijab Options editor

Dirty when relationship selection or new-hijab draft differs from entry state.

Cancel/scrim/system Back:
- clean → close;
- dirty → explicit discard confirmation.

Done:
- commits relation changes atomically in current prototype scope.

### Practical Note editor

Dirty only when current text differs from entry value.

Cancel/system Back:
- clean → close;
- dirty → discard confirmation.

Save:
- trim + commit note;
- success → Outfit Detail.

### Availability

**PROPOSED_TEST_FIX:** treat availability as **instant-save** because each change is small, directly reversible, and the existing prototype already commits on selection.

Required semantics:
- selecting a state commits immediately;
- show brief truthful `Saved` feedback;
- sheet copy says **Changes save automatically**;
- `Done` only closes;
- scrim/Back closes without implying rollback;
- user can reopen and reverse any state.

This is a TEST interaction simplification, not a proven buyer preference.

## 4. Async photo lifecycle

```text
NO_PHOTO
 → PICKER_OPEN
 → FILE_SELECTED
 → PHOTO_PROCESSING(token, owner_draft)
 → PHOTO_READY
```

Alternative branches:

```text
PICKER_OPEN → cancel → NO_PHOTO
PHOTO_PROCESSING → decode fail → PHOTO_DECODE_FAILED → continue without photo / retry
PHOTO_PROCESSING → editor canceled → PHOTO_ASYNC_CANCELED_OR_STALE
PHOTO_PROCESSING → navigation/session change → PHOTO_ASYNC_CANCELED_OR_STALE
```

Hard rule:

> An async callback may mutate state only when its operation token and owning draft/editor session are still current.

## 5. Save / commit lifecycle

```text
BUILDER_DRAFT
 → SAVE_REQUESTED
 → validate minimum outfit semantics
 → COMMITTING
 → committed Garments + Outfit relations durable
 → SAVE_SUCCESS
```

Failure:

```text
COMMITTING
 → STORAGE_COMMIT_FAILED
 → buyer remains in recoverable draft
 → retry or exit with draft retained where possible
```

No success screen before durable prototype commit.

## 6. Navigation semantics

### Back

Returns to the prior safe context and respects dirty guards.

### Home / Outfits

Returns to stable `OUTFITS_HOME`; does not delete state.

### Cancel

Abandons uncommitted changes in the current transient editor after dirty confirmation when needed.

### Discard

Explicit destructive confirmation for current uncommitted draft only.

### Reset / Start new test session

Research-only destructive reset:
- hidden in TEST tools;
- clears prototype test state;
- must never be used as ordinary Home/navigation;
- requires explicit confirmation.

## 7. System Back / platform delta for current prototype

For the Android-oriented behavioral prototype:

- system Back should mirror the visible semantic exit of the active surface;
- it must not bypass dirty confirmation;
- transient editor closes before parent destination changes;
- on stable Home/Launch, browser/device exit behavior is environment-specific and not product navigation truth.

Production Android behavior remains a future platform-specialist implementation concern after BUILD authorization.

## 8. Derived availability state

`OutfitAvailable(outfit)`:

- every required base garment is `AVAILABLE`; and
- when saved hijab options exist, at least one saved hijab option is `AVAILABLE`.

Presentation rule:

If the card shows one representative hijab while another saved alternative is the actually available one, the card must not visually imply the unavailable displayed hijab is the wearable choice.

**Current disposition:** `UNRESOLVED_UI_PRESENTATION_DEBT` — requires a truthful representative-state treatment before claiming Available-now clarity.

## 9. Session / evidence lifecycle

- Each moderated participant uses a fresh `TestSession`.
- Start is blocked when prototype storage preflight fails.
- Reset cannot silently delete downloaded evidence files outside the app.
- Default evidence export is sanitized.
- Evidence-export failure does not modify buyer/product state.
