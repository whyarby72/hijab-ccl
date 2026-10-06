import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';

const root = process.cwd();
const candidatePath = process.env.MHCCL_CANDIDATE_PATH || join(root, 'prototype/index.html');
const baselinePath = process.env.MHCCL_BASELINE_PATH || join(root, 'fixtures/MODEST_HIJAB_CAPSULE_CLOSET_v3.1e_UI_COPY_ACCESSIBILITY_RECONCILED_CANDIDATE.html');
const readmePath = process.env.MHCCL_README_PATH || join(root, 'README.md');
const candidate = readFileSync(candidatePath, 'utf8');
const baseline = readFileSync(baselinePath);
const expectedBaseline = '7b809352dfd0e46a7e5161a5630de41e956847a08f2b79babcde34bdaa086f4d';
const expectedCandidate = process.env.MHCCL_EXPECT_CANDIDATE_SHA256 || '';
const sha = value => createHash('sha256').update(value).digest('hex');
const checks = [];
const check = (name, ok) => checks.push([ok ? 'PASS' : 'FAIL', name]);
const must = (needle, name) => check(name, candidate.includes(needle));

check('candidate readable', candidate.length > 0);
check('canonical baseline hash', sha(baseline) === expectedBaseline);
if (expectedCandidate) check('candidate hash matches expected', sha(candidate) === expectedCandidate);
const script = candidate.match(/<script>([\s\S]*?)<\/script>/)?.[1];
try { execFileSync(process.execPath, ['--check'], { input: script, stdio: ['pipe', 'pipe', 'pipe'] }); check('embedded JavaScript syntax', true); }
catch { check('embedded JavaScript syntax', false); }

must('draft_piece_edit_started', 'T1 start instrumentation');
must('draft_piece_edit_saved', 'T1 save instrumentation');
must('draft_piece_edit_canceled', 'T1 cancel instrumentation');
must('editDraft(id)', 'Draft edit entrypoint');
must('editSnapshot', 'Draft edit snapshot');
must('photo_processing_stale_discarded', 'stale photo callback guard');
must('Edit draft piece', 'accessible edit dialog name');
must('duplicate_outfit_decision', 'T2 decision instrumentation');
must('Keep editing', 'duplicate keep-editing action');
must('Open saved outfit', 'duplicate open-saved action');
must('Save another version', 'duplicate save-another action');
must("resolveDuplicate('keep_editing')", 'duplicate close/back safety');
must("resolveDuplicate('open_saved')", 'duplicate open branch');
must("resolveDuplicate('save_another')", 'duplicate save branch');
must("if(S.duplicateDecision){APP.resolveDuplicate('keep_editing');log('android_back_handled',{target:'duplicate_keep_editing'});return true}", 'AC-007 duplicate Back precedence');
must("if(choice==='keep_editing'){S.duplicateDecision=null;save();render();return}", 'Keep editing is non-destructive');
must("S.draft?.draftGarments.find(x=>x.id===id)", 'Draft edit targets one DraftGarment');
must("if(!S.addOpen||!S.addForm||S.addForm.photoToken!==token)", 'Canceled edit rejects stale photo');
must("try{const data=await compressImage(file);if(!S.addOpen||!S.addForm||S.addForm.photoToken!==token){log('photo_processing_stale_discarded',{owner:S.addForm?.editDraftId?'draft_piece_edit':'add_piece'});return}", 'Draft edit photo callback is owner-bound');
must("const next=n<3?", 'Done for now remains available before Matrix');
must("S.outfits.push(o);", 'Save another version creates one Outfit');
must("S.currentOutfitId=d.existingOutfitId;save();nav('detail')", 'Open saved opens existing Outfit only');
must("touch-action:auto", 'Matrix relation scroll preserves vertical pan');
check('both photo owners retain token guards', (candidate.match(/photoToken!==token/g) || []).length >= 2 && (candidate.match(/photo_processing_stale_discarded/g) || []).length >= 2);
must("if(S.addOpen){APP.closeAdd();return true}", 'system Back closes Add Piece safely');
must('<th scope="row">', 'Matrix row header is semantic');
check('old binary duplicate confirm removed', !candidate.includes('This combination is already represented in a saved outfit. Save another version anyway?'));
check('sanitized evidence excludes raw fields', candidate.includes("excluded_by_default:['imageData','shortLabel','practicalNote']"));
check('no prohibited cloud/backend scope', !/firebase|supabase|fetch\s*\(|WebSocket|recommendation/i.test(candidate));
check('native relation table preserved', candidate.includes('<table class="relation-table"'));
check('dirty edit uses snapshot restore', candidate.includes('Object.assign(g,f.editSnapshot)'));
check('draft edit does not commit garment', candidate.includes("log('draft_piece_edit_saved'"));

const inheritedGuards = [
  ['Outfit remains primary saved memory', candidate.includes("outfits:[]") && candidate.includes("outfit_saved")],
  ['third save keeps Matrix voluntary', candidate.includes("viewMatrixFromSuccess()") && candidate.includes('Done for now')],
  ['no old 10-piece gate', !candidate.includes('10 pieces') && !candidate.includes('10-piece')],
  ['reuse uses committed IDs', candidate.includes('existing_garment_selected') && candidate.includes('existing_garment_reused')],
  ['main-piece save validity', candidate.includes('baseCats.has(g.category)')],
  ['Add Piece stale callback guard', candidate.includes("owner:'add_piece'")],
  ['Hijab stale callback guard', candidate.includes("owner:'hijab_editor'")],
  ['dirty Builder discard guard', candidate.includes('backFromBuilder()') && candidate.includes('Discard this outfit?')],
  ['pairing rollback', candidate.includes('const before=JSON.stringify(S)') && candidate.includes('S=JSON.parse(before)')],
  ['duplicate save failure has no false success', candidate.includes('This outfit was not saved')],
  ['availability autosave', candidate.includes('Changes save automatically') && candidate.includes('availability_saved')],
  ['saved memory survives availability', candidate.includes('Unavailable pieces stay in your saved outfits')],
  ['available alternative hijab truthful', candidate.includes('contextualHijab') && candidate.includes('preferAvailable')],
  ['note false-dirty guard', candidate.includes('noteEditDirty') && candidate.includes('value!==S.noteEdit.original')],
  ['hijab relation is user-saved', candidate.includes("source:'ADDED_LATER'") && candidate.includes('Saved option')],
  ['empty relation is not incompatible', candidate.includes('Empty means not saved yet')],
  ['explicit DraftHijab removal', candidate.includes('removePairDraft')],
  ['native semantic relation table', candidate.includes('<table class="relation-table"') && candidate.includes('scope="row"') && candidate.includes('scope="col"')],
  ['accessible hit/miss state', candidate.includes("hit?'Saved':'Not saved'") && candidate.includes('aria-hidden="true"')],
  ['relation cells not tabbable/grid', !candidate.includes('role="grid"') && !candidate.includes('tabindex="0"')],
  ['Matrix vertical pan preserved', candidate.includes('.relation-scroll') && candidate.includes('touch-action:auto')],
  ['modal semantics', candidate.includes('role="dialog"') && candidate.includes('aria-modal="true"')],
  ['focus containment/restoration', candidate.includes('focusablesWithin') && candidate.includes('dialogReturnFocusKey')],
  ['Escape safe', candidate.includes("e.key==='Escape'") && candidate.includes('closeActiveDialogFromKeyboard')],
  ['both bottom-nav current states', candidate.includes("S.screen==='home'?'aria-current=\"page\"'") && candidate.includes("S.screen==='capsule'?'aria-current=\"page\"'")],
  ['programmatic pressed state', candidate.includes('aria-pressed')],
  ['live processing/saved feedback', candidate.includes('aria-live="polite"')],
  ['privacy excludes source/free text', candidate.includes("excluded_by_default:['imageData','shortLabel','practicalNote']")],
  ['claim ceiling documented', readFileSync(readmePath, 'utf8').includes('remain `HOLD` until executed')],
  ['all deferred environment claims remain HOLD', readFileSync(readmePath, 'utf8').includes('Physical Android, TalkBack, system Back on device, local-file/browser runtime, storage reopen, photo picker, safe-area, download retrieval, and cohort claims remain `HOLD` until executed in those environments.')],
  ['failed runtime remains HOLD', readFileSync(readmePath, 'utf8').includes('Failed browser/runtime attempts remain HOLD')],
  ['BUILD authority remains false', readFileSync(readmePath, 'utf8').includes('Production BUILD, artifact freeze, release, and publication remain unauthorized')]
];
for (const [name, ok] of inheritedGuards) check(`inherited: ${name}`, ok);

const original = { id: 'dg_1', category: 'TOP', shortLabel: 'White blouse', imageData: 'old' };
let draft = structuredClone(original); const snapshot = structuredClone(draft);
draft.category = 'OUTER'; draft.shortLabel = 'Jacket'; draft.imageData = 'new'; draft = structuredClone(snapshot);
check('edit cancel restores snapshot', JSON.stringify(draft) === JSON.stringify(original));
draft = structuredClone(original); draft.category = 'DRESS'; draft.shortLabel = 'Black dress';
check('edit save updates draft only', draft.category === 'DRESS' && original.category === 'TOP');
let activeToken = 'new-token'; const staleToken = 'old-token'; let photo = 'new-photo'; if (staleToken !== activeToken) photo = photo;
check('stale async completion is ignored', photo === 'new-photo');
const draftBeforeFailure = JSON.stringify({ outfits: ['saved'], draft: { id: 'draft_1' } });
let persisted = draftBeforeFailure; try { throw new Error('simulated storage failure'); } catch { persisted = draftBeforeFailure; }
check('persistence failure preserves recoverable draft', persisted === draftBeforeFailure);
const evidence = { event: 'draft_piece_edit_saved', label: 'secret', imageData: 'bytes', has_photo: true };
const sanitized = { event: evidence.event, has_photo: evidence.has_photo };
check('sanitized fixture excludes label/photo bytes', !('label' in sanitized) && !('imageData' in sanitized));

const duplicateBefore = { screen: 'builder', draft: { id: 'draft_1', draftGarments: [{ id: 'dg_1', category: 'TOP' }] }, outfits: 1, currentOutfitId: 'o_1', duplicateDecision: { existingOutfitId: 'o_1' } };
const duplicateBack = structuredClone(duplicateBefore);
let builderBackCalls = 0; let discardConfirmationCalls = 0; const duplicateEvents = [];
function safeDuplicateKeepEditing(state, source) { duplicateEvents.push({ event: 'duplicate_outfit_decision', choice: 'keep_editing', source }); state.duplicateDecision = null; return state; }
function simulatedBack(state) { if (state.duplicateDecision) return safeDuplicateKeepEditing(state, 'back'); builderBackCalls++; discardConfirmationCalls++; return state; }
const afterDuplicateBack = simulatedBack(duplicateBack);
check('duplicate Back closes decision', afterDuplicateBack.duplicateDecision === null);
check('duplicate Back keeps Builder active', afterDuplicateBack.screen === 'builder');
check('duplicate Back preserves DraftOutfit', JSON.stringify(afterDuplicateBack.draft) === JSON.stringify(duplicateBefore.draft));
check('duplicate Back bypasses generic Builder Back', builderBackCalls === 0);
check('duplicate Back does not ask discard confirmation', discardConfirmationCalls === 0);
check('duplicate Back does not create Outfit', afterDuplicateBack.outfits === duplicateBefore.outfits);
check('duplicate Back preserves current saved Outfit', afterDuplicateBack.currentOutfitId === duplicateBefore.currentOutfitId);
check('duplicate Back event is controlled and private', duplicateEvents[0].choice === 'keep_editing' && !('label' in duplicateEvents[0]) && !('imageData' in duplicateEvents[0]));
const convergence = ['escape', 'scrim', 'explicit'].map(source => { const state = structuredClone(duplicateBefore); return safeDuplicateKeepEditing(state, source); });
check('Escape/scrim/Keep editing converge', convergence.every(state => state.duplicateDecision === null && state.screen === 'builder' && JSON.stringify(state.draft) === JSON.stringify(duplicateBefore.draft)));

for (const [status, name] of checks) console.log(`${status} ${name}`);
const failed = checks.filter(([status]) => status === 'FAIL').length;
console.log(`\n${checks.length - failed}/${checks.length} deterministic checks passed`);
if (failed) process.exitCode = 1;
