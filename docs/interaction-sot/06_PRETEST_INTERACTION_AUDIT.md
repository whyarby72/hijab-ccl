# 06 — Pre-Test Interaction Audit

## Scope

This audit evaluates whether the current TEST interaction truth is sufficiently specified to produce interpretable behavioral evidence.

It is **not** Final RED, PRR, BUILD approval, Artifact Freeze, or publication approval.

## Result

**NOT_READY — specification corrections resolved conceptually; artifact implementation/replay still required before the next moderated cohort.**

## Ready dimensions

### Product/job truth — READY

- Outfit-first primary job is clear.
- First saved outfit is first value.
- Third saved outfit + Matrix is core activation.
- Garment reuse is subordinate to outfit memory.
- Hijab relation is user-approved memory, not recommendation.
- No AI/modesty/body-scoring scope.

### Domain model — READY

- Draft vs committed objects are explicit.
- Outfit/Garment/Hijab relationship authority is explicit.
- Capsule is derived.
- Availability does not destroy saved memory.
- Test evidence is distinct from buyer data/backup.

### Master flow — READY_WITH_DEBT

Core destinations and branches are explicit.

Outstanding artifact-level corrections:
- visible `Done for now` after Save Success;
- Add Piece dirty guard;
- async photo token/session cancellation;
- truthful availability autosave semantics;
- representative-hijab availability presentation;
- sanitized default evidence JSON;
- note editor false-dirty behavior.

### Navigation semantics — READY_WITH_DEBT

- Back/Home/Cancel/Discard/Reset meanings are separated.
- System Back must mirror visible semantic exit.
- Real Android behavior remains environment evidence debt.

### Failure/recovery — READY_WITH_DEBT

Contracts exist, but implementation and replay are still required for:
- storage commit failure;
- stale async callbacks;
- sanitized export;
- representative hijab availability;
- local-file/device operational flow.

## Hypotheses that must remain unresolved for the test

Do **not** “fix” these through design assumptions:

1. whether garment decomposition is accepted;
2. whether Capsule Matrix is understood and valuable;
3. whether Hijab Options add incremental value;
4. whether availability is useful enough to retain/promote;
5. whether same-base/different-hijab grouping should exist;
6. whether `Outfits | Capsule` remains sufficient after repeat use;
7. whether photo optionality remains practical.

## Behavioral evidence protection rules

The next cohort must be able to:
- stop after one saved outfit without hidden pressure to continue;
- create later outfits using existing pieces when desired;
- recover from ordinary mistakes without moderator rescue;
- understand Matrix relation meaning from the product itself;
- use or ignore optional hijab/availability tools naturally;
- complete the test without source wardrobe media being silently exported.

## Real-device precondition

The prior Android pre-test report remains applicable:

Before an 8-tester Android cohort, verify at least all P0 operational items on a real target Android device:
- system Back;
- storage/local-file workflow;
- draft persistence/reload;
- horizontal Matrix/rail swipe;
- export retrieval;
- safe-area/system-UI layout;
- new-session reset/evidence isolation.

## Gate disposition

```yaml
interaction_pretest_readiness:
  product_truth: READY
  domain_model: READY
  state_lifecycle: READY_WITH_IMPLEMENTATION_DEBT
  master_wireflow: READY
  action_contract: READY_WITH_IMPLEMENTATION_DEBT
  recovery_contract: READY_WITH_IMPLEMENTATION_DEBT
  test_evidence_privacy: READY_WITH_IMPLEMENTATION_DEBT
  real_android_environment: UNVERIFIED
  overall: NOT_READY
```

### Why `NOT_READY`

The earlier prototype lineage was close to testable, but under the improved procedure the current artifact cannot inherit readiness merely from having screens and working buttons. The revised interaction contracts must first be reflected in the exact behavioral artifact and replayed on the target device/environment.

This does not authorize production BUILD.
