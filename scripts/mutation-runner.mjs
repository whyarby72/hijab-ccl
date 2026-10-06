import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const root = process.cwd();
const source = join(root, 'prototype/index.html');
const baseline = join(root, 'fixtures/MODEST_HIJAB_CAPSULE_CLOSET_v3.1e_UI_COPY_ACCESSIBILITY_RECONCILED_CANDIDATE.html');
const readme = join(root, 'README.md');
const tmp = mkdtempSync(join(tmpdir(), 'mhccl-real-mutations-'));
const candidateText = readFileSync(source, 'utf8');
const sha = createHash('sha256').update(candidateText).digest('hex');

const precedence = "if(S.duplicateDecision){APP.resolveDuplicate('keep_editing');log('android_back_handled',{target:'duplicate_keep_editing'});return true}";
const keep = "if(choice==='keep_editing'){S.duplicateDecision=null;save();render();return}";
const privacy = "excluded_by_default:['imageData','shortLabel','practicalNote']";
const hold = 'Physical Android, TalkBack, system Back on device, local-file/browser runtime, storage reopen, photo picker, safe-area, download retrieval, and cohort claims remain `HOLD` until executed in those environments.';
const cases = [
  ['M01','AC-007','remove duplicate-decision Back precedence','candidate',precedence,'if(false){APP.resolveDuplicate(\'keep_editing\');return true}'],
  ['M02','AC-007','route duplicate Back to builder discard path','candidate',precedence,"if(S.duplicateDecision){APP.backFromBuilder();return true}"],
  ['M03','AC-007','map duplicate close/Back to open saved','candidate',precedence,"if(S.duplicateDecision){APP.resolveDuplicate('open_saved');return true}"],
  ['M04','AC-007','make duplicate close/Back destructive','candidate',precedence,'if(S.duplicateDecision){S.draft=null;return true}'],
  ['M05','AC-007','remove non-destructive Keep editing transition','candidate',keep,"if(choice==='keep_editing'){S.draft=null;return}"],
  ['M06','AC-002/003','Cancel commits edited snapshot','candidate','Object.assign(g,f.editSnapshot)','S.garments.push(g);'],
  ['M07','AC-004','stale photo callback mutates canceled edit','candidate',"try{const data=await compressImage(file);if(!S.addOpen||!S.addForm||S.addForm.photoToken!==token){log('photo_processing_stale_discarded',{owner:S.addForm?.editDraftId?'draft_piece_edit':'add_piece'});return}",'try{const data=await compressImage(file);if(false)'],
  ['M08','AC-005','Draft edit is labeled as committed garment save','candidate',"draft_piece_edit_saved","garment_edit_saved"],
  ['M09','AC-002','Draft A edit selects Draft B','candidate','S.draft?.draftGarments.find(x=>x.id===id)','S.draft?.draftGarments.find(x=>true)'],
  ['M10','AC-003','Back bypasses dirty edit semantics','candidate','APP.closeAdd();return true','S.addOpen=false;return true'],
  ['M11','AC-012','evidence includes recognition label','candidate',privacy,"excluded_by_default:['imageData','practicalNote']"],
  ['M12','AC-012','evidence includes photo payload','candidate',privacy,"excluded_by_default:['shortLabel','practicalNote']"],
  ['M13','AC-011','Matrix row header loses semantic scope','candidate','<th scope="row">','<th scope="data">'],
  ['M14','AC-011','Matrix loses accessible Saved/Not saved state','candidate',"hit?'Saved':'Not saved'","hit?'Saved':''"],
  ['M15','AC-011','Matrix introduces grid semantics','candidate','<table class="relation-table"','<table role="grid" class="relation-table"'],
  ['M16','AC-011','Matrix relation region reintroduces pan-x trap','candidate','touch-action:auto','touch-action:pan-x'],
  ['M17','AC-011','third save forces Matrix','candidate','const next=n<3?','const next=true?'],
  ['M18','AC-011','remove Done for now','candidate','Done for now','Done later'],
  ['M19','AC-011','reintroduce old activation prerequisite','candidate','const n=S.outfits.length+1',"const gate='10 pieces';const n=S.outfits.length+1"],
  ['M20','AC-011','clone existing committed piece instead of reuse','candidate','existing_garment_reused','new_garment_created'],
  ['M21','AC-011','persistence failure displays success','candidate','This outfit was not saved','Saved successfully'],
  ['M22','AC-009','Save another creates two records','candidate','S.outfits.push(o);','S.outfits.push(o,o);'],
  ['M23','AC-008','Open saved creates another Outfit','candidate',"S.currentOutfitId=d.existingOutfitId;save();nav('detail')","S.outfits.push({id:uid('o')});nav('detail')"],
  ['M24','AC-016','mark physical Android PASS','readme',hold,'Physical Android PASS without execution.'],
  ['M25','AC-016','mark TalkBack PASS','readme',hold,hold.replace('TalkBack','TalkBack PASS')],
  ['M26','AC-016','promote failed runtime to PASS','readme','Failed browser/runtime attempts remain HOLD','Failed browser/runtime attempts are PASS'],
  ['M27','AC-016','infer BUILD authorization from deterministic PASS','readme','Production BUILD, artifact freeze, release, and publication remain unauthorized','Production BUILD is authorized']
];

const results = [];
for (const [id, invariant, description, target, needle, replacement] of cases) {
  const mutatedCandidate = join(tmp, `${id}.html`); const mutatedReadme = join(tmp, `${id}.md`);
  cpSync(source, mutatedCandidate); cpSync(readme, mutatedReadme);
  const targetPath = target === 'candidate' ? mutatedCandidate : mutatedReadme;
  const original = readFileSync(targetPath, 'utf8');
  if (!original.includes(needle)) throw new Error(`${id}: mutation needle missing`);
  writeFileSync(targetPath, original.replace(needle, replacement));
  let exitCode = 0; let output = '';
  try { output = execFileSync(process.execPath, [join(root, 'scripts/verify.mjs')], { cwd: root, env: { ...process.env, MHCCL_CANDIDATE_PATH: mutatedCandidate, MHCCL_BASELINE_PATH: baseline, MHCCL_README_PATH: mutatedReadme }, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }); }
  catch (error) { exitCode = error.status ?? 1; output = `${error.stdout || ''}${error.stderr || ''}`; }
  const detected = exitCode !== 0;
  results.push({ id, invariant, description, detected, exit_code: exitCode, evidence: output.split('\n').filter(line => line.includes('FAIL')).slice(0, 2) });
}
rmSync(tmp, { recursive: true, force: true });
const escaped = results.filter(result => !result.detected);
const report = [`# Mutation and Adversarial Verification Report`, ``, `Candidate SHA-256: \`${sha}\``, ``, `Genuine isolated-copy verifier replay: **YES**`, ``, `| ID | Invariant | Result | Exit | Target |`, `|---|---|---|---:|---|`, ...results.map(result => `| ${result.id} | ${result.invariant} — ${result.description} | ${result.detected ? 'DETECTED' : 'ESCAPED_MUTATION'} | ${result.exit_code} | isolated copy |`), ``, `Total mutations attempted: **${results.length}**`, `Mutations detected: **${results.length - escaped.length}**`, `Escaped mutations: **${escaped.length}**`, ``, `Each mutation started from the exact good candidate, changed one isolated copy, executed the verifier, and required a non-zero result. The canonical candidate was not modified.`];
mkdirSync(join(root, 'evidence'), { recursive: true }); writeFileSync(join(root, 'evidence/MUTATION_ADVERSARIAL_REPORT.md'), report.join('\n') + '\n');
console.log(`genuine_mutation_replay: attempted=${results.length} detected=${results.length - escaped.length} escaped=${escaped.length}`);
if (escaped.length) process.exitCode = 1;
