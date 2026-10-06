# 04 — Complete Action / Control Register

Status legend:
- `CANONICAL_TEST`
- `PROPOSED_TEST_FIX`
- `HYPOTHESIS`
- `N_A_CURRENT_TEST`

| ID | Surface | Control | Preconditions | Effect / transition | Commit / persistence | Back/Cancel/Failure | Status |
|---|---|---|---|---|---|---|---|
| A001 | Launch/Home empty | Start / Save one outfit | storage preflight usable | create/open DraftOutfit → Builder | draft persistence only | storage unavailable blocks start with explanation | CANONICAL_TEST |
| A002 | Builder | Existing garment card | committed garment exists | toggle relation in DraftOutfit | uncommitted until outfit Save | reversible in draft | CANONICAL_TEST |
| A003 | Builder | Add new piece | draft active | open Add Piece | none | Back/Cancel closes with dirty guard | CANONICAL_TEST |
| A004 | Add Piece | Category | sheet open | set DraftGarment category | draft only | invalid/missing category blocks Add with corrective feedback | CANONICAL_TEST |
| A005 | Add Piece | Short label | sheet open | set optional recognition text | draft only | discard with parent draft if canceled | CANONICAL_TEST |
| A006 | Add Piece | Choose local photo | picker supported; sheet current | open picker; start async processing token | no garment commit | cancel picker → unchanged; decode fail → retry/continue; stale callback ignored | CANONICAL_TEST |
| A007 | Add Piece | Add to outfit | category valid; async photo not in unresolved state | attach DraftGarment to DraftOutfit; close sheet | draft only; commit waits for outfit Save | failure keeps sheet/draft recoverable | CANONICAL_TEST |
| A008 | Add Piece | Cancel / scrim / system Back | sheet open | return Builder | none | dirty → discard confirmation; pending async invalidated | PROPOSED_TEST_FIX |
| A009 | Builder | Remove draft piece | draft piece exists | remove relation/draft piece | draft only | reversible by re-adding | CANONICAL_TEST |
| A010 | Builder | Back | builder active | prior safe Home/Launch | none | dirty → discard confirmation | CANONICAL_TEST |
| A011 | Builder | Save outfit | valid draft combination | COMMITTING → Save Success | authoritative prototype commit of Outfit + attached new Garments | storage failure → retain recoverable draft; no success claim | CANONICAL_TEST |
| A012 | Save Success | Done for now | saved outfit committed | Outfits Home | none | always visible | PROPOSED_TEST_FIX |
| A013 | Save Success | Save another outfit | saved outfit committed | create next DraftOutfit → Builder | new draft only | voluntary continuation event | CANONICAL_TEST, but must coexist with A012 |
| A014 | Save Success after 3rd | View Capsule Matrix | core activation condition met | Activation Matrix | read-only | Continue returns Home | CANONICAL_TEST |
| A015 | Activation Matrix | Continue to my outfits | matrix visible | Outfits Home | none | system Back equivalent allowed | CANONICAL_TEST |
| A016 | Outfits Home | All | any saved outfits | show all | none | switchable | CANONICAL_TEST |
| A017 | Outfits Home | Available now | saved outfits exist | apply derived availability filter | none | empty state offers View all | CANONICAL_TEST |
| A018 | Outfits Home | Outfit card | outfit exists | Outfit Detail | none | Detail Back → Home | CANONICAL_TEST |
| A019 | Outfits Home | + Save | stable Home | create DraftOutfit → Builder | draft only | Builder Back semantics | CANONICAL_TEST |
| A020 | Bottom nav | Outfits | not already transient-dirty | Outfits Home | none | transient editor must resolve first | CANONICAL_TEST |
| A021 | Bottom nav | Capsule | not already transient-dirty | Capsule Overview | none | transient editor must resolve first | CANONICAL_TEST |
| A022 | Capsule | Hijab pairing | any outfit has >1 saved option | Pairing Matrix | none | Back → Capsule | CANONICAL_TEST conditional |
| A023 | Detail | Back | detail open | Outfits Home | none | no data loss | CANONICAL_TEST |
| A024 | Detail | Edit/Add hijab options | outfit exists | Hijab Options Editor | edit transaction | Cancel/Back dirty guard | CANONICAL_TEST |
| A025 | Hijab editor | Toggle existing hijab | eligible hijab exists | change draft relationship selection | commit only on Done | reversible before Done | CANONICAL_TEST |
| A026 | Hijab editor | Add new hijab | editor open | reveal DraftHijab form | draft only | whole-editor cancel discards | CANONICAL_TEST |
| A027 | New hijab | Choose local photo | current DraftHijab | async photo token | no commit | stale/canceled callback ignored; decode fallback | PROPOSED_TEST_FIX |
| A028 | New hijab | Add new hijab | category HIJAB / valid draft | append DraftHijab and select | draft only | may remove before Done | CANONICAL_TEST |
| A029 | New hijab draft | Remove draft | DraftHijab exists | remove draft entity | draft only | control must look like Remove, not selection ✓ | PROPOSED_TEST_FIX |
| A030 | Hijab editor | Done | edit state valid | commit relation changes/new hijabs → Detail | authoritative transaction commit | if removing all prior options → explicit confirmation | CANONICAL_TEST |
| A031 | Hijab editor | Cancel/scrim/Back | editor open | Detail | none | dirty → discard confirm | CANONICAL_TEST |
| A032 | Detail | Manage availability | outfit exists | Availability sheet | none on open | close returns Detail | CANONICAL_TEST |
| A033 | Availability | State selector | garment selected | set AVAILABLE/LAUNDRY/TEMP_UNAVAILABLE | **immediate commit** | save feedback; reopen can reverse | PROPOSED_TEST_FIX |
| A034 | Availability | Done/scrim/Back | sheet open | Detail | no new commit on Done | sheet says Changes save automatically | PROPOSED_TEST_FIX |
| A035 | Detail | Add/Edit practical note | outfit exists | Note Editor | transaction draft | Cancel/Back dirty guard | CANONICAL_TEST |
| A036 | Note editor | Save note | valid text | trim + commit → Detail | authoritative note commit | failure retains edit text | CANONICAL_TEST |
| A037 | Note editor | Cancel/Back | editor open | Detail | none | prompt only if text changed | PROPOSED_TEST_FIX |
| A038 | Available empty | View all saved outfits | zero available results | filter All | none | — | CANONICAL_TEST |
| A039 | Pairing Matrix | Back | matrix open | Capsule Overview | none | — | CANONICAL_TEST |
| A040 | TEST tools | Export evidence JSON | tools enabled | download sanitized evidence | external file only | export failure leaves product state unchanged | PROPOSED_TEST_FIX |
| A041 | TEST tools | Export events CSV | tools enabled | download event rows | external file only | failure leaves product state unchanged | CANONICAL_TEST |
| A042 | TEST tools | Start new test session | tools enabled | confirmation → clear prototype state → fresh session | destructive research reset | cancel = no change | CANONICAL_TEST |
| A043 | TEST tools | Close | tools open | underlying surface | none | — | CANONICAL_TEST |

## Cross-cutting control laws

### Enabled / disabled truth

- A disabled control must explain the missing prerequisite where buyer confusion is plausible.
- Save cannot appear successful before commit succeeds.
- Photo remains optional; photo-processing failure cannot disable the whole outfit job.

### Async/session truth

Any async callback must verify:
- owning surface/editor session still active;
- operation token still current;
- target draft object still exists.

Otherwise result is discarded as stale.

### Accessibility projection

Every material control requires:
- meaningful accessible label/semantics;
- non-pointer activation where the platform supports it;
- predictable focus transition for modal/sheet open/close;
- focus return to invoking control when feasible;
- state announcements for Saving/Saved/Error where material.

Section 30 / platform owner remains canonical.

### Instrumentation truth

Behavioral events should distinguish at least:
- first outfit completed;
- new garment count;
- existing garment reuse;
- voluntary Save-another vs Done-for-now;
- draft abandonment;
- Matrix viewed/comprehension observation;
- hijab option use;
- availability use;
- grouping-offer response when explicitly tested.

Instrumentation must not force continuation or change the task being measured.
