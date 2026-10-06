# 04 — Engineering Test Matrix

## Strategy

Testing is intentionally split:

### Early / continuous — cheap deterministic build guards

Run during Codex engineering:
- JS syntax;
- HTML structural parse;
- protected source/semantic assertions;
- pure/state-machine scenarios;
- persistence-failure rollback simulations;
- async stale-callback simulations;
- evidence sanitization;
- native-table semantics;
- accessibility source semantics;
- duplicate-decision state tests;
- DraftGarment edit transaction tests;
- mutation/negative controls.

### Late / consolidated — environment/manual verification

Defer until engineering candidate is stable:
- direct runtime/browser execution;
- physical Android;
- TalkBack;
- enlarged text;
- system Back gesture/button;
- real photo picker;
- real Downloads;
- close/reopen persistence;
- Matrix swipe + vertical scroll;
- virtual keyboard;
- safe area;
- 8-tester cohort.

## New deterministic cases for Codex

### DraftGarment edit

- edit category then Save → draft updated;
- edit label then Save → draft updated;
- clear label → accepted;
- replace photo → old draft photo replaced;
- remove photo → draft photo empty;
- Cancel after edit → original snapshot preserved;
- Back after dirty edit → same discard semantics as Cancel;
- async completion after Cancel → ignored;
- edit one draft → no other draft changed;
- edit draft → committed Garment count unchanged;
- parent Outfit save after edit → final committed values equal edited draft.

### Duplicate Outfit decision

- duplicate detection opens explicit decision surface;
- Keep editing → draft byte/semantic state unchanged;
- dialog close/Back → Keep editing;
- Open saved outfit → current draft removed and existing Outfit opened;
- Save another version → exactly one new Outfit committed;
- each branch logs one controlled event;
- no branch exports free text/media;
- storage failure on Save another version → rollback/recoverable draft.

## Regression floor

Existing v3.1e floors must not decrease:
- syntax PASS;
- source invariants equivalent to prior 86/86;
- semantic/state-truth equivalent to prior 41/41;
- state-flow scenarios equivalent to prior 13/13;
- mutation guard equivalent to 57/57 detected, 0 escapes, 18/18 adversarial PASS.

Counts may increase as new guards are added. Never preserve a number by weakening coverage.
