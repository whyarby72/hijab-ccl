# 03 — Master Wireflow

## 1. First-use / activation flow

```text
LAUNCH
  └─ Start
      ↓
OUTFITS_HOME (empty)
  └─ Save one outfit
      ↓
OUTFIT BUILDER
  ├─ choose existing garment(s)
  ├─ Add new piece
  │    ├─ choose category [required]
  │    ├─ optional short label
  │    ├─ optional local photo
  │    ├─ Add to draft
  │    └─ Cancel / Back → dirty guard when needed
  ├─ review current draft
  ├─ Back → discard guard
  └─ Save outfit
       ↓
     SAVE SUCCESS
       ├─ Done for now → OUTFITS HOME
       └─ Save another outfit → next OUTFIT BUILDER
```

### After second outfit

Same flow, but existing committed garments are surfaced before `Add new`.

Goal: reveal whether reuse reduces effort.

### After third saved outfit

```text
SAVE SUCCESS
  ├─ Done for now → OUTFITS HOME
  └─ View Capsule Matrix / activation payoff
       ↓
    ACTIVATION MATRIX
       └─ Continue to my outfits → OUTFITS HOME
```

The prototype must not force continuation to outfit 2 or 3 as the only visible path.

## 2. Existing-garment reuse branch

```text
BUILDER
  → existing pieces shown
  → user selects one or more
  → selected piece enters DraftOutfit relation
  → no new Garment object created
  → save commits only Outfit + any truly new garments
```

Duplicate prevention happens before cleanup:
- show existing same-category garments;
- preserve recognition label/photo;
- do not silently clone an existing garment.

## 3. Add Piece flow

```text
BUILDER
  → Add new
  → ADD PIECE SHEET
      ├─ category
      ├─ optional label
      ├─ optional photo
      │    → picker
      │    → process
      │    ├─ ready
      │    ├─ decode fail → continue without photo / retry
      │    └─ stale/canceled → ignore result
      ├─ Add to outfit draft
      └─ Cancel / scrim / Back
            ├─ clean → close
            └─ dirty → discard confirmation
```

No DraftGarment commits before parent Outfit save.

## 4. Stable navigation flow

```text
OUTFITS HOME
  ├─ outfit card → OUTFIT DETAIL
  ├─ availability filter: All | Available now
  ├─ Save outfit → BUILDER
  └─ bottom nav Capsule → CAPSULE OVERVIEW

CAPSULE OVERVIEW
  ├─ relationship view
  ├─ conditional Hijab Pairing → HIJAB PAIRING MATRIX
  └─ bottom nav Outfits → OUTFITS HOME

HIJAB PAIRING MATRIX
  └─ Back → CAPSULE OVERVIEW
```

No separate top-level Availability destination in current TEST.

## 5. Outfit Detail flow

```text
OUTFIT DETAIL
  ├─ Back → OUTFITS HOME
  ├─ Edit/Add Hijab Options → HIJAB OPTIONS EDITOR
  ├─ Manage Availability → AVAILABILITY SHEET
  └─ Add/Edit Practical Note → NOTE EDITOR
```

Base outfit-member editing, rename, delete/archive are not current TEST requirements.

## 6. Hijab Options flow

```text
OUTFIT DETAIL
  → Edit hijab options
  → HIJAB OPTIONS EDITOR
      ├─ toggle existing hijab relations
      ├─ Add new hijab
      │    ├─ category fixed as HIJAB
      │    ├─ optional label
      │    ├─ optional photo
      │    ├─ add DraftHijab
      │    └─ remove DraftHijab before commit
      ├─ Done
      │    ├─ if all prior hijab relations removed → confirm outfit may remain without saved hijab
      │    └─ commit atomically → OUTFIT DETAIL
      └─ Cancel / scrim / Back
           ├─ clean → OUTFIT DETAIL
           └─ dirty → discard confirmation
```

Control semantics must distinguish:
- selection checkbox/toggle;
- remove-new-draft control.

Do not use the same ambiguous ✓ symbol for both selection and destructive draft removal.

## 7. Availability flow

```text
OUTFIT DETAIL
  → Manage availability
  → AVAILABILITY SHEET
      ├─ select garment
      ├─ choose AVAILABLE / LAUNDRY / TEMPORARILY_UNAVAILABLE
      │    → commit immediately
      │    → show Saved
      ├─ change another garment
      └─ Done / scrim / Back → OUTFIT DETAIL
```

Sheet must state: **Changes save automatically.**

## 8. Practical Note flow

```text
OUTFIT DETAIL
  → Add/Edit practical note
  → NOTE EDITOR
      ├─ edit text
      ├─ Save note → commit → OUTFIT DETAIL
      └─ Cancel / Back
           ├─ unchanged → OUTFIT DETAIL
           └─ changed → discard confirmation
```

## 9. Available-now flow

```text
OUTFITS HOME
  → Available now
  → derived filter
      ├─ results → open outfit detail
      └─ no results → View all saved outfits → All
```

Filter changes visibility only; it does not mutate saved outfit relations.

## 10. TEST tools / moderator flow

Hidden unless research tools explicitly enabled.

```text
TEST TOOLS
  ├─ Record device preflight
  ├─ Export sanitized evidence JSON
  ├─ Export events CSV
  ├─ Start new test session
  │    → confirm destructive research reset
  │    → fresh TestSession + empty prototype state
  └─ Close → underlying screen
```

Default sanitized JSON:
- IDs;
- categories;
- relationship IDs;
- counts;
- availability;
- boolean `has_photo`;
- event data.

Exclude by default:
- image bytes/base64;
- practical-note text;
- free-text recognition labels.

## 11. Explicit dead-end prohibitions

- Save success cannot expose only “Save another”.
- Add Piece cannot trap a user after photo failure.
- Dirty transient editors cannot close silently.
- Availability `Done` cannot imply a commit that already happened invisibly without explanatory copy.
- System Back cannot bypass dirty/discard semantics.
- Empty Available-now must provide path back to All.
- Pairing Matrix must provide path back to Capsule.
- TEST reset must never masquerade as ordinary Home.
