# 05 — Failure / Recovery / Reversibility Matrix

| ID | Failure / mistake | Prevention / detection | Buyer-safe recovery | Data-safety rule | TEST status |
|---|---|---|---|---|---|
| R001 | User opens Add Piece then changes mind | explicit Cancel/Back | return Builder | no committed data created | CANONICAL_TEST |
| R002 | User entered Add Piece data then closes | dirty detection | confirm discard or remain | uncommitted DraftGarment deleted only after confirm | REQUIRED FIX |
| R003 | Photo picker canceled | detect no file | remain usable without photo | no phantom photo state | CANONICAL_TEST |
| R004 | Photo decode/compress fails | error boundary | retry or continue without photo | existing draft fields preserved | CANONICAL_TEST |
| R005 | Photo processing finishes after Add Piece canceled | operation token/session check | ignore stale completion | dead editor cannot be mutated/resurrected | REQUIRED FIX |
| R006 | Photo processing finishes after Hijab editor canceled | operation token/session check | ignore stale completion | `pairEdit`/draft remains closed | REQUIRED FIX |
| R007 | Storage unavailable before test | preflight | block Start + explain | do not collect contaminated session | CANONICAL_TEST |
| R008 | Storage commit fails while saving outfit | commit error handling | retain recoverable DraftOutfit; retry | never show Save Success before durable commit | REQUIRED CONTRACT |
| R009 | User presses Back from dirty Builder | dirty guard | discard confirm or remain | committed outfits untouched | CANONICAL_TEST |
| R010 | User presses Back from dirty Note editor | compare current vs entry | discard confirm or remain | saved note unchanged until Save | CANONICAL_TEST |
| R011 | User opens Note but makes no changes | compare current vs entry | close without warning | avoid false dirty prompt | REQUIRED FIX |
| R012 | User removes all previously saved hijab options | detect destructive relation outcome | confirm outfit can remain with no saved hijab | base outfit remains intact | CANONICAL_TEST |
| R013 | New DraftHijab removal looks like selection toggle | visual/semantic contract | explicit Remove control | only draft hijab removed | REQUIRED FIX |
| R014 | Availability changes but Done looks like commit | explicit autosave copy + Saved feedback | reopen and reverse | each selector change commits atomically | REQUIRED FIX |
| R015 | Available-now says outfit available while displayed representative hijab is unavailable | derived state/presentation reconciliation | display an available saved hijab or neutral state that does not imply wrong option | relationship memory unchanged | UNRESOLVED UI DEBT |
| R016 | Duplicate exact outfit attempted | pre-commit duplicate check | explain existing saved combination / return to edit | no duplicate committed unintentionally | CANONICAL_TEST |
| R017 | Same base + different hijab detected | event only | keep memories separate; optionally test grouping offer | no automatic grouping | HYPOTHESIS |
| R018 | Save Success forces next outfit | visible Done-for-now | user can end session naturally | instrumentation records voluntary branch | REQUIRED TEST-VALIDITY FIX |
| R019 | Matrix misunderstood as recommendation | copy + moderated comprehension check | explain markers mean previously saved relation | no recommendation score generated | HYPOTHESIS / TEST |
| R020 | Garment decomposition rejected | observe friction/abandonment | branch future TEST to outfit-photo-first; do not add AI automation | current data not used to force product thesis | KILL/BRANCH CRITERION |
| R021 | Available filter has no result | explicit empty state | View all saved outfits | no state mutation | CANONICAL_TEST |
| R022 | User navigates away while async callback pending | token cancellation | ignore callback | stale result cannot mutate current session | REQUIRED FIX |
| R023 | Reload/interruption during DraftOutfit | durable draft restoration | restore draft or fail clearly | restored draft remains uncommitted | CANONICAL_TEST; real-device evidence required |
| R024 | Reload after committed outfit | persistence verification | reopen committed state | committed outfit must survive promised runtime scope | CANONICAL_TEST; real-device evidence required |
| R025 | Evidence JSON includes source photos/free text | sanitized export contract | export IDs/categories/relations/counts/has_photo/events only | media/text excluded by default | REQUIRED PRIVACY FIX |
| R026 | Research actually needs media evidence | separate explicit action + disclosure/consent | export only within approved research scope | never silently include in default export | CONDITIONAL |
| R027 | Evidence export download fails | detect export error | show failure; allow retry | product state unchanged | REQUIRED CONTRACT |
| R028 | Start new test session pressed accidentally | destructive confirmation | Cancel keeps session | clear only after explicit confirm | CANONICAL_TEST |
| R029 | System Back bypasses dirty editor | platform/back binding | same dirty guard as visible Cancel/Back | no silent draft loss | CANONICAL_TEST; device verification debt |
| R030 | Core horizontal Matrix cannot swipe on target phone | pre-test device checklist | HOLD cohort; repair local test delivery/UI | do not recruit testers with unusable artifact | REAL-DEVICE HOLD |
| R031 | Core controls clipped by Android system UI | safe-area/device check | HOLD cohort; repair layout | no workaround requiring tester coaching | REAL-DEVICE HOLD |
| R032 | Opening local HTML is unreliable | operational pre-test | HOLD/change test delivery mechanism only | do not add cloud/account merely to mask test delivery defect | REAL-DEVICE HOLD |

## Recovery principles

1. Common mistakes should be correctable without delete-and-recreate when a smaller reversal exists.
2. Draft loss must be intentional or clearly disclosed.
3. Committed user memory must not be removed by availability changes.
4. Async work is session-bound.
5. Research reset is separate from ordinary navigation.
6. Test-evidence privacy is separate from buyer backup/portability.
7. A failed device/runtime pre-test is repaired at the test-delivery or prototype layer first; it does not justify backend/cloud scope expansion.
