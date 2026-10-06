# 01 — Domain / Object / Data Model

## 1. Scope

This object model is the current **TEST interaction model**, not the mature production database schema.

Core invariant:

> **The user saves a known-good Outfit. Garments exist because they participate in real saved Outfit memory. Capsule views are derived from those saved relationships.**

## 2. Current TEST objects

### 2.1 `Garment`

A reusable physical-clothing primitive referenced by outfits.

```yaml
Garment:
  id: stable_local_id
  category: TOP | BOTTOM | DRESS | OUTER | HIJAB | OTHER_SUPPORTED
  recognition_label: optional_short_text
  photo_ref: optional_local_test_media
  availability: AVAILABLE | LAUNDRY | TEMPORARILY_UNAVAILABLE
  committed: true
```

Rules:

- `category` is required.
- photo is optional;
- recognition label is optional;
- absence of photo/label must not block first value;
- the same committed garment may be reused in later outfits;
- current TEST has no destructive merge/archive contract;
- `availability` describes practical use state, not style suitability.

### 2.2 `DraftGarment`

Uncommitted garment being created inside a real outfit task.

```yaml
DraftGarment:
  draft_id: stable_draft_id
  parent_draft_outfit_id: required
  category: required_before_add
  recognition_label: optional
  photo_ref: optional_pending_or_ready
  photo_operation_token: optional
  local_status: DRAFT | PHOTO_PENDING | READY_TO_ATTACH
```

Rules:

- must never become a committed `Garment` merely because a photo/category was selected;
- becomes committed only through the parent outfit commit;
- Cancel/Discard removes it after applicable dirty confirmation;
- async photo completion after the draft/editor has been canceled must be ignored and must not resurrect state.

### 2.3 `DraftOutfit`

Temporary transaction for creating a saved outfit.

```yaml
DraftOutfit:
  draft_id: stable_local_id
  existing_garment_ids: []
  draft_garment_ids: []
  selected_hijab_relation_draft: []
  created_at: local_timestamp
  dirty: boolean
  restoration_state: ACTIVE | RESTORED_AFTER_INTERRUPTION
```

Rules:

- it is not a saved outfit;
- explicit discard removes uncommitted DraftGarment state;
- unexpected interruption may restore the draft;
- save commits the outfit plus any attached DraftGarments atomically at the interaction-contract level;
- there must be no hidden mandatory “10 pieces” prerequisite.

### 2.4 `Outfit`

The primary committed memory object.

```yaml
Outfit:
  id: stable_local_id
  base_garment_ids: [Garment.id]
  saved_hijab_option_ids: [Garment.id]
  practical_note: optional_free_text
  created_at: local_timestamp
  updated_at: local_timestamp
```

Rules:

- represents a combination the user already knows works;
- no generated or recommended outfit may enter committed state;
- one saved outfit may have zero, one, or multiple **user-approved hijab options**;
- base garment relationships remain distinct from alternative hijab-option relationships;
- current TEST does not require an outfit name;
- current TEST does not require wear history, favorite, archive, duplicate merge, or tagging.

### 2.5 `HijabOptionRelationship`

A user-approved relation between an Outfit and a committed hijab garment.

This is relationship memory only.

```yaml
HijabOptionRelationship:
  outfit_id: Outfit.id
  hijab_garment_id: Garment.id
  source: USER_SAVED
```

Hard rules:

- no ranking;
- no “best match”;
- no compatibility score;
- empty relation means **not saved yet**, not “does not match”;
- removing all hijab options from an outfit is allowed only through an explicit user-confirmed outcome when prior saved relations exist.

### 2.6 `AvailabilityState`

Current state of a committed garment.

```yaml
AvailabilityState:
  garment_id: Garment.id
  state: AVAILABLE | LAUNDRY | TEMPORARILY_UNAVAILABLE
```

Derived outfit rule:

- required base garments must be available;
- if saved hijab options exist, at least one saved hijab option must be available;
- saved outfit memory itself is never deleted merely because a garment is unavailable.

### 2.7 `PracticalNote`

Optional user-authored free text attached to a saved outfit.

Rules:

- no scoring;
- no parsing into style recommendations;
- treated as user content;
- excluded by default from sanitized behavioral-test evidence export.

### 2.8 `CapsuleRelationshipView`

Derived, read-only projection.

```yaml
CapsuleRelationshipView:
  row_object: committed_garment
  column_object: selected_or_saved_outfit
  marker_meaning: GARMENT_PARTICIPATES_IN_USER_SAVED_OUTFIT
```

Rules:

- not separately authoritative;
- must derive from committed Outfit/Garment relations;
- activation view at three outfits may show the whole small set;
- a mature giant all-outfit matrix is not implied by the TEST.

### 2.9 `TestSession` / `TestEvent`

Research-only data.

```yaml
TestSession:
  session_id: random_or_unique
  started_at: timestamp

TestEvent:
  session_id: TestSession.id
  event_name: controlled_enum_or_string
  event_properties: derived_minimized_fields
```

Hard boundary:

- TestEvent/Test evidence is not buyer backup.
- Default test evidence excludes source photo bytes and free-text notes/labels unless a separate explicit research need and consent exists.

## 3. Identity / commit rules

1. Existing committed garment identity is reused rather than cloned when the user selects an existing piece.
2. Draft IDs remain distinct from committed IDs unless the implementation has a deterministic atomic promotion rule.
3. Outfit visible success occurs only after the outfit and attached new garments are durably committed in the prototype storage scope.
4. Capsule/Pairing views read committed state only.
5. No UI control may claim saved/committed state merely because a preview exists.

## 4. Current TEST non-objects / non-authorities

The following are **not** current canonical objects:

- AI recommendation;
- style score;
- modesty score;
- body profile;
- social profile/follow graph;
- shopping item;
- mandatory calendar plan;
- wardrobe-completion score;
- mature `WearLog` as required object;
- automatic duplicate cluster;
- automatic same-base grouping.

## 5. Post-validation / mature objects

May exist later only if promoted by evidence:

- WearLog;
- archive metadata;
- backup manifest;
- focused compare set;
- presentation grouping metadata;
- duplicate-merge transaction.

They must not leak into current TEST interaction requirements.
