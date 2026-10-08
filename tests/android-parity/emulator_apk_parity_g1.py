#!/usr/bin/env python3
import argparse, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "image-fixtures"))

from emulator_photo_lifecycle import (
    PACKAGE, STATE_EXPR, sx, adb, sha256, wait_until,
    launch, CDP, capture, trigger_picker, tap_named, foreground, js_photo_signature
)

EXPECTED_HTML_SHA = "861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171"
LABEL_SENTINEL = "PRIVATE_LABEL_SENTINEL_G1"
NOTE_SENTINEL = "PRIVATE_NOTE_SENTINEL_G1"

def ensure(cond, msg):
    if not cond:
        raise RuntimeError(msg)

def list_downloads():
    p = adb("shell","find","/sdcard/Download","-maxdepth","1","-type","f","-printf","%f\\n",check=False)
    return [x.strip() for x in (p.stdout or "").splitlines() if x.strip()]

def pull_file(remote, local):
    local=Path(local)
    local.parent.mkdir(parents=True,exist_ok=True)
    adb("pull",remote,str(local))
    return local

def publish_fixture(filename):
    src="/data/local/tmp/MHCClFixtures/"+filename
    dst="/sdcard/Pictures/MHCClFixtureCurrent/"+filename
    adb("shell","cp",src,dst)
    adb("shell","touch",dst)
    adb("shell","am","broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE","-d","file://"+dst,check=False)
    time.sleep(2)

def select_fixture_photo(cdp, filename):
    publish_fixture(filename)
    trigger_picker(cdp)
    try:
        tap_named(["Dismiss"],2)
    except Exception:
        pass
    tap_named(["Photo taken"],30)
    wait_until(lambda: PACKAGE in foreground(),15,label="app foreground after Photo Picker")
    cdp.wait(sx("!!(S.addForm && !S.addForm.photoPending && S.addForm.imageData)"),25,label="photo processed")
    return js_photo_signature(cdp)

def snapshot(cdp):
    return cdp.eval("""(()=>{
      const S=JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}');
      return {
        screen:S.screen,
        outfitCount:(S.outfits||[]).length,
        garmentCount:(S.garments||[]).length,
        draft:S.draft?{existingIds:[...S.draft.existingIds],draftCount:S.draft.draftGarments.length}:null,
        duplicate:!!S.duplicateDecision,
        currentOutfitId:S.currentOutfitId||null,
        matrixSeen:!!S.matrixSeen,
        hasPhoto:(S.garments||[]).some(g=>!!g.imageData)
      };
    })()""")

def add_piece(cdp, category, label=""):
    expr="window.APP.openAdd(%s); window.APP.setAddLabel(%s); window.APP.addDraftGarment(); true" % (json.dumps(category),json.dumps(label))
    cdp.eval(expr)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apk",required=True)
    ap.add_argument("--prototype",required=True)
    ap.add_argument("--fixtures",required=True)
    ap.add_argument("--evidence",required=True)
    args=ap.parse_args()

    ev=Path(args.evidence)
    (ev/"screenshots").mkdir(parents=True,exist_ok=True)
    (ev/"exports").mkdir(parents=True,exist_ok=True)

    results={
      "schema":"mhccl_android_apk_emulator_parity_g1_v1",
      "status":"RUNNING",
      "gate":"ANDROID_APK_EMULATOR_PARITY_G1",
      "tests":[],
      "environment":{},
      "candidate":{"expected_sha256":EXPECTED_HTML_SHA},
      "source_changed":False,
      "build_authorized":False,
      "artifact_freeze_authorized":False,
      "release_authorized":False,
      "publication_authorized":False
    }

    def record(tid,status,details=None):
        results["tests"].append({"id":tid,"status":status,"details":details or {}})
        (ev/"RESULTS.json").write_text(json.dumps(results,indent=2)+"\\n",encoding="utf-8")

    cdp=None
    try:
        html_sha=sha256(args.prototype)
        apk_sha=sha256(args.apk)
        ensure(html_sha==EXPECTED_HTML_SHA,"canonical HTML SHA mismatch: "+html_sha)
        results["candidate"]["actual_sha256"]=html_sha
        results["environment"]={
          "apk_sha256":apk_sha,
          "android_release":adb("shell","getprop","ro.build.version.release").stdout.strip(),
          "api":adb("shell","getprop","ro.build.version.sdk").stdout.strip(),
          "model":adb("shell","getprop","ro.product.model").stdout.strip()
        }
        record("G1_00_ARTIFACT_BINDING","PASS",{"html_sha256":html_sha,"apk_sha256":apk_sha})

        adb("install","-r",args.apk)
        adb("shell","pm","clear",PACKAGE)
        record("G1_01_INSTALL_CLEAN","PASS",{"package":PACKAGE})

        fixture_dir=Path(args.fixtures)
        adb("shell","rm","-rf","/data/local/tmp/MHCClFixtures",check=False)
        adb("shell","mkdir","-p","/data/local/tmp/MHCClFixtures")
        adb("shell","rm","-rf","/sdcard/Pictures/MHCClFixtureCurrent",check=False)
        adb("shell","mkdir","-p","/sdcard/Pictures/MHCClFixtureCurrent")
        for p in sorted(fixture_dir.iterdir()):
            if p.suffix.lower() not in {".jpg",".jpeg",".png"}:
                continue
            adb("push",str(p),"/data/local/tmp/MHCClFixtures/"+p.name)

        launch()
        cdp=CDP()
        cdp.wait("typeof window.APP==='object' && document.body.innerText.includes('Save my first outfit')",20,label="clean APK launch")
        url=cdp.eval("location.href")
        ensure(url.startswith("https://appassets.androidplatform.net/assets/index.html"),"unexpected app URL "+str(url))
        capture(ev/"screenshots","00_clean_launch")
        record("G1_02_LAUNCH","PASS",{"url":url})

        pkgdump=adb("shell","dumpsys","package",PACKAGE).stdout
        ensure("android.permission.INTERNET" not in pkgdump,"debug package unexpectedly declares INTERNET permission")
        record("G1_03_NETWORK_ISOLATION","PASS",{"internet_permission":False,"runtime_origin":"appassets.androidplatform.net"})

        cdp.eval("window.APP.startFirst(); window.APP.openAdd('TOP'); window.APP.setAddLabel("+json.dumps(LABEL_SENTINEL)+"); true")
        cdp.wait(sx("S.screen==='builder' && S.addOpen && S.addForm.category==='TOP'"),10,label="first TOP form")
        photo=select_fixture_photo(cdp,"transparent_hijab.png")
        cdp.eval("window.APP.addDraftGarment(); window.APP.saveDraftOutfit(); true")
        cdp.wait(sx("S.screen==='success' && S.outfits.length===1 && S.garments.length===1"),15,label="first outfit saved")
        first=snapshot(cdp)
        ensure(first["hasPhoto"],"first committed garment lost picker photo")
        outfit_id=first["currentOutfitId"]
        garment_id=cdp.eval("("+STATE_EXPR+").garments[0].id")
        cdp.eval("window.APP.editNote("+json.dumps(outfit_id)+"); window.APP.setNoteDraft("+json.dumps(NOTE_SENTINEL)+"); window.APP.saveNote(); true")
        cdp.wait(sx("S.outfits[0] && S.outfits[0].practicalNote==="+json.dumps(NOTE_SENTINEL)),10,label="private note sentinel")
        capture(ev/"screenshots","01_first_saved_with_photo")
        record("G1_04_REAL_PICKER_AND_FIRST_SAVE","PASS",{"photo_signature":photo,"outfit_id":outfit_id})

        cdp.close(); cdp=None
        launch()
        cdp=CDP()
        cdp.wait(sx("S.outfits.length===1 && S.garments.length===1 && !!S.garments[0].imageData"),20,label="process restart persistence")
        persisted=snapshot(cdp)
        ensure(cdp.eval("("+STATE_EXPR+").outfits[0].practicalNote")==NOTE_SENTINEL,"practical note missing after restart")
        record("G1_05_PROCESS_PERSISTENCE","PASS",persisted)

        cdp.eval("window.APP.doneForNow(); window.APP.newOutfit(); window.APP.toggleExisting("+json.dumps(garment_id)+"); window.APP.saveDraftOutfit(); true")
        cdp.wait(sx("S.screen==='builder' && !!S.duplicateDecision"),12,label="duplicate decision")
        before_back=snapshot(cdp)
        capture(ev/"screenshots","02_duplicate_before_system_back")
        adb("shell","input","keyevent","4")
        cdp.wait(sx("S.screen==='builder' && !S.duplicateDecision && S.draft && S.draft.existingIds.length===1"),15,label="native Back keeps draft")
        after_back=snapshot(cdp)
        ensure(after_back["outfitCount"]==1,"system Back altered saved outfit count")
        ensure(after_back["draft"] and after_back["draft"]["existingIds"]==[garment_id],"system Back lost duplicate draft")
        back_event=cdp.eval("""(()=>{
          const S=JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}');
          return [...(S.events||[])].reverse().find(e=>e.event==='android_back_handled')||null;
        })()""")
        ensure(back_event and back_event.get("target")=="duplicate_keep_editing","missing duplicate Back event: "+repr(back_event))
        capture(ev/"screenshots","03_duplicate_after_system_back")
        record("G1_06_NATIVE_SYSTEM_BACK_DUPLICATE","PASS",{"before":before_back,"after":after_back,"event":back_event})

        cdp.eval("window.APP.toggleExisting("+json.dumps(garment_id)+"); window.APP.backFromBuilder(); true")
        cdp.wait(sx("S.screen==='home' && S.outfits.length===1"),10,label="home after duplicate draft exit")

        cdp.eval("window.APP.newOutfit(); window.APP.toggleExisting("+json.dumps(garment_id)+"); true")
        add_piece(cdp,"BOTTOM")
        cdp.eval("window.APP.saveDraftOutfit(); true")
        cdp.wait(sx("S.screen==='success' && S.outfits.length===2"),12,label="second outfit")

        cdp.eval("window.APP.afterSuccess(); window.APP.toggleExisting("+json.dumps(garment_id)+"); true")
        add_piece(cdp,"OUTER")
        cdp.eval("window.APP.saveDraftOutfit(); true")
        cdp.wait(sx("S.screen==='success' && S.outfits.length===3"),12,label="third outfit")
        cdp.eval("window.APP.viewMatrixFromSuccess(); true")
        cdp.wait(sx("S.screen==='matrix' && S.outfits.length===3"),10,label="Capsule Matrix")

        matrix=cdp.eval("""(()=>{
          const table=document.querySelector('table.relation-table');
          const caption=table&&table.querySelector('caption');
          const cols=table?[...table.querySelectorAll('thead th[scope="col"]')].map(x=>x.textContent.trim()):[];
          const rows=table?[...table.querySelectorAll('tbody th[scope="row"]')].map(x=>x.textContent.trim()):[];
          const semantics=table?[...table.querySelectorAll('tbody td .sr-only')].map(x=>x.textContent.trim()):[];
          const wrap=document.querySelector('[data-scroll-region]');
          return {exists:!!table,caption:caption?caption.textContent.trim():'',cols,rows,semantics,
            overflow:wrap?wrap.scrollWidth>wrap.clientWidth:false,
            scrollWidth:wrap?wrap.scrollWidth:0,clientWidth:wrap?wrap.clientWidth:0};
        })()""")
        ensure(matrix["exists"],"Matrix table missing")
        ensure(matrix["cols"]==["Piece","Outfit 1","Outfit 2","Outfit 3"],"Matrix columns mismatch: "+repr(matrix["cols"]))
        ensure(len(matrix["rows"])>=3,"Matrix rows incomplete")
        ensure("Saved" in matrix["semantics"] and "Not saved" in matrix["semantics"],"Matrix accessible relation semantics incomplete")
        capture(ev/"screenshots","04_matrix")
        record("G1_07_MATRIX_PARITY","PASS",matrix)

        cdp.eval("location.href='https://appassets.androidplatform.net/assets/index.html?tools=1'; true")
        time.sleep(1.2)
        cdp.close(); cdp=None
        cdp=CDP()
        cdp.wait("typeof window.APP==='object' && location.search.includes('tools=1')",20,label="tools query runtime")
        cdp.eval("window.APP.finishMatrix(); window.APP.openResearch(); true")
        cdp.wait("document.body.innerText.includes('TEST tools')",10,label="research tools visible")

        session_id=cdp.eval("("+STATE_EXPR+").sessionId")
        before=set(list_downloads())
        cdp.eval("window.APP.exportJSON(); window.APP.exportCSV(); true")
        json_name="mhccl_"+session_id+"_evidence_sanitized.json"
        csv_name="mhccl_"+session_id+"_events.csv"
        wait_until(lambda: json_name in list_downloads() and csv_name in list_downloads(),25,label="native export files in Downloads")
        after=set(list_downloads())

        json_local=pull_file("/sdcard/Download/"+json_name,ev/"exports"/json_name)
        csv_local=pull_file("/sdcard/Download/"+csv_name,ev/"exports"/csv_name)
        json_text=json_local.read_text(encoding="utf-8")
        csv_text=csv_local.read_text(encoding="utf-8")
        payload=json.loads(json_text)
        ensure(payload.get("sanitized") is True,"export JSON not marked sanitized")
        excluded=payload.get("excluded_by_default",[])
        ensure(all(x in excluded for x in ["imageData","shortLabel","practicalNote"]),"privacy exclusion declaration incomplete")
        for forbidden in ["data:image/",LABEL_SENTINEL,NOTE_SENTINEL]:
            ensure(forbidden not in json_text,"JSON privacy leak: "+forbidden)
            ensure(forbidden not in csv_text,"CSV privacy leak: "+forbidden)
        record("G1_08_NATIVE_EXPORT_PRIVACY","PASS",{
          "json":json_name,"csv":csv_name,
          "new_download_files":sorted(after-before),
          "json_sha256":sha256(json_local),"csv_sha256":sha256(csv_local)
        })
        capture(ev/"screenshots","05_test_tools_after_exports")

        cdp.close(); cdp=None
        launch()
        cdp=CDP()
        cdp.wait(sx("S.outfits.length===3 && S.garments.length===3"),20,label="final restart state")
        final_state=snapshot(cdp)
        record("G1_09_FINAL_RESTART","PASS",final_state)

        results["status"]="PASS"
        results["p0"]=0
        results["p1"]=0
    except Exception as e:
        results["status"]="FAIL"
        results["error"]=repr(e)
        try:
            if cdp: capture(ev/"screenshots","FAIL_screen")
        except Exception:
            pass
        raise
    finally:
        try:
            if cdp: cdp.close()
        except Exception:
            pass
        (ev/"RESULTS.json").write_text(json.dumps(results,indent=2)+"\\n",encoding="utf-8")
        (ev/"REPORT.md").write_text(
          "# Android APK Emulator Parity G1\\n\\nStatus: **"+results["status"]+"**\\n\\n"
          +"Candidate SHA-256: "+results["candidate"].get("actual_sha256","")+"\\n\\n"
          +"APK SHA-256: "+results.get("environment",{}).get("apk_sha256","")+"\\n\\n"
          +"Tests recorded: "+str(len(results["tests"]))+"\\n\\n"
          +"TEST engineering evidence only; no BUILD, Artifact Freeze, release, or publication authority.\\n",
          encoding="utf-8"
        )

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL:",repr(exc),file=sys.stderr)
        sys.exit(1)
