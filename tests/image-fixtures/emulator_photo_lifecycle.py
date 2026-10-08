#!/usr/bin/env python3
import argparse, hashlib, json, os, re, subprocess, sys, time, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
import websocket

PACKAGE="com.aiprod.hijabccl.test"
COMPONENT=PACKAGE + "/com.aiprod.hijabccl.MainActivity"
STATE_KEY="mhccl_v31e_ui_copy_accessibility_candidate_state"
STATE_EXPR="JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}')"
PORT=9222

def sx(expr):
    return "(()=>{const S=" + STATE_EXPR + "; return (" + expr + ");})()"

def run(*args, check=True, text=True, capture=True):
    cmd=list(args)
    p=subprocess.run(cmd, check=False, text=text, capture_output=capture)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed {p.returncode}: {' '.join(cmd)}\nstdout={p.stdout}\nstderr={p.stderr}")
    return p

def adb(*args, **kw):
    return run("adb", *args, **kw)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def wait_until(fn, timeout=30, interval=.35, label="condition"):
    end=time.time()+timeout
    last=None
    while time.time()<end:
        try:
            value=fn()
            if value:
                return value
            last=value
        except Exception as e:
            last=e
        time.sleep(interval)
    raise TimeoutError(f"timeout waiting for {label}; last={last!r}")

def launch():
    adb("shell","am","force-stop",PACKAGE)
    adb("shell","am","start","-W","-n",COMPONENT)
    wait_until(lambda: adb("shell","pidof",PACKAGE,check=False).stdout.strip(), 20, label="app pid")

def devtools_socket():
    def find():
        out=adb("shell","cat","/proc/net/unix").stdout
        names=[]
        for line in out.splitlines():
            if "webview_devtools_remote" in line:
                name=line.split()[-1].lstrip("@")
                names.append(name)
        pid=adb("shell","pidof",PACKAGE,check=False).stdout.strip().split()
        for p in pid:
            for n in names:
                if n.endswith("_"+p):
                    return n
        return names[0] if names else None
    return wait_until(find,25,label="WebView devtools socket")

class CDP:
    def __init__(self):
        socket_name=devtools_socket()
        adb("forward","--remove",f"tcp:{PORT}",check=False)
        adb("forward",f"tcp:{PORT}",f"localabstract:{socket_name}")
        def target():
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json",timeout=2) as r:
                    arr=json.load(r)
                pages=[x for x in arr if x.get("type")=="page" and x.get("webSocketDebuggerUrl")]
                exact=[x for x in pages if "appassets.androidplatform.net/assets/index.html" in (x.get("url") or "")]
                return exact[0] if exact else None
            except Exception:
                return None
        t=wait_until(target,25,label="canonical CDP page")
        self.ws=websocket.create_connection(t["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
        self.i=0
        self.call("Runtime.enable",{})

    def close(self):
        try:self.ws.close()
        except Exception:pass
        adb("forward","--remove",f"tcp:{PORT}",check=False)

    def call(self,method,params):
        self.i+=1
        ident=self.i
        self.ws.send(json.dumps({"id":ident,"method":method,"params":params}))
        while True:
            msg=json.loads(self.ws.recv())
            if msg.get("id")==ident:
                if "error" in msg: raise RuntimeError(msg["error"])
                return msg.get("result",{})

    def eval(self,expr, await_promise=True):
        res=self.call("Runtime.evaluate",{
            "expression":expr,
            "returnByValue":True,
            "awaitPromise":await_promise,
            "userGesture":True,
        })
        if res.get("exceptionDetails"):
            raise RuntimeError("JS exception: "+json.dumps(res["exceptionDetails"]))
        return res.get("result",{}).get("value")

    def wait(self,expr,timeout=25,label="JS condition"):
        return wait_until(lambda:self.eval(expr),timeout,label=label)

def dump_ui():
    for _ in range(4):
        p=adb("shell","uiautomator","dump","/sdcard/mhccl_ui.xml",check=False)
        if p.returncode==0:
            xml=adb("shell","cat","/sdcard/mhccl_ui.xml",check=False).stdout
            if xml.strip().startswith("<?xml"):
                return ET.fromstring(xml)
        time.sleep(.6)
    raise RuntimeError("uiautomator dump failed")

def bounds_center(bounds):
    m=re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",bounds or "")
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups())
    return ((x1+x2)//2,(y1+y2)//2)

def find_node(root, candidates):
    cs=[c.lower() for c in candidates]
    for node in root.iter("node"):
        vals=[node.attrib.get("text",""),node.attrib.get("content-desc","")]
        merged=" ".join(vals).lower()
        if any(c and c in merged for c in cs):
            center=bounds_center(node.attrib.get("bounds",""))
            if center:return center,node.attrib
    return None,None

def tap_named(candidates,timeout=12):
    end=time.time()+timeout
    while time.time()<end:
        root=dump_ui()
        center,attrs=find_node(root,candidates)
        if center:
            adb("shell","input","tap",str(center[0]),str(center[1]))
            return attrs
        time.sleep(.5)
    raise RuntimeError(f"UI node not found: {candidates}")

def foreground():
    out=adb("shell","dumpsys","window","windows",check=False).stdout
    for line in out.splitlines():
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            return line.strip()
    return ""

def media_index_probe(filename):
    # Test-only adb observation. Device MediaStore is the provider of the gallery.
    # Avoid adb-shell quote stripping in --where (API 36 invalid-token error).
    # Query only metadata rows, then match an exact filename value in Python.
    query=adb("shell","content","query",
        "--uri","content://media/external/images/media",
        "--projection","_id:_display_name:mime_type:relative_path:is_pending:is_trashed:date_added",check=False)
    rows=query.stdout.strip()
    expected="_display_name="+filename
    matches=[line for line in rows.splitlines() if line.startswith("Row:")
             and expected in [piece.strip() for piece in line.split(",")]]
    return {"returncode":query.returncode,
            "found":query.returncode==0 and bool(matches) and not query.stderr.strip(),
            "matching_rows":matches[:4],
            "stdout":rows[-1400:],"stderr":query.stderr.strip()[-700:]}

def publish_fixture(filename,fixture_dir,evidence):
    source=fixture_dir/filename
    if not source.is_file(): raise RuntimeError("FIXTURE_MISSING: "+str(source))
    target="/sdcard/Pictures/MHCClFixtureCurrent/"+filename
    adb("shell","mkdir","-p","/sdcard/Pictures/MHCClFixtureCurrent")
    adb("push",str(source),target)
    device_hash=adb("shell","sha256sum",target).stdout.split()[0]
    local_hash=sha256(source)
    if device_hash!=local_hash:
        raise RuntimeError("FIXTURE_DEVICE_HASH_MISMATCH: "+filename)
    adb("shell","touch",target)
    scan=adb("shell","am","broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE",
             "-d","file://"+target,check=False)
    # This legacy broadcast is a test-environment trigger, not proof of indexing.
    # Do not infer visibility from the command's returncode or a fixed sleep.
    probe=None
    try:
        probe=wait_until(lambda: (p if (p:=media_index_probe(filename))["found"] else None),
                         35,interval=1.0,label="MediaStore indexed "+filename)
    except Exception:
        bad=media_index_probe(filename)
        (evidence/("MEDIA_INDEX_FAIL_"+filename+".json")).write_text(
            json.dumps({"filename":filename,"device_sha256":device_hash,
                        "broadcast_exit":scan.returncode,"probe":bad},indent=2)+"\\n")
        raise RuntimeError("MEDIA_INDEX_NOT_READY: "+filename+"; "+repr(bad))
    (evidence/("MEDIA_INDEX_"+filename+".json")).write_text(
        json.dumps({"filename":filename,"source_sha256":local_hash,
                    "device_sha256":device_hash,"broadcast_exit":scan.returncode,
                    "probe":probe},indent=2)+"\\n")
    return probe

def pick_photo_thumbnail(filename,evidence):
    # Real Android Photo Picker may lag behind MediaStore insertion. Wait for
    # the gallery *UI* to render a selectable thumbnail, not for an arbitrary
    # fixed delay, and never fall back to DocumentsUI while claiming picker PASS.
    deadline=time.time()+45
    attempt=0
    root=None
    center=None
    attrs=None
    while time.time()<deadline:
        attempt+=1
        root=dump_ui()
        center,attrs=find_node(root,["Photo taken"])
        if center: break
        if attempt==12:
            # Refresh the provider-backed page once through the actual UI tabs.
            album,_=find_node(root,["Albums"])
            if album:
                adb("shell","input","tap",str(album[0]),str(album[1]))
                time.sleep(1.0)
                root=dump_ui()
                photos,_=find_node(root,["Photos"])
                if photos:
                    adb("shell","input","tap",str(photos[0]),str(photos[1]))
        time.sleep(1)
    (evidence/("PICKER_UI_"+filename+".xml")).write_bytes(ET.tostring(root,encoding="utf-8"))
    if not center:
        capture(evidence,"PICKER_NO_THUMBNAIL_"+filename)
        # The index row and actual Photo Picker rendering are separate gates.
        empty,_=find_node(root,["No photos or videos"])
        diagnostic={"filename":filename,"attempts":attempt,
                    "picker_empty":bool(empty),
                    "media_index":media_index_probe(filename),
                    "picker_provider":"com.google.android.providers.media.module",
                    "provider_package_info":adb("shell","dumpsys","package",
                        "com.google.android.providers.media.module",check=False).stdout[-4500:]}
        (evidence/("PICKER_NOT_READY_"+filename+".json")).write_text(
            json.dumps(diagnostic,indent=2)+"\\n")
        raise RuntimeError("PHOTO_PICKER_THUMBNAIL_NOT_READY: "+filename+
                           "; media_index_found="+str(diagnostic["media_index"]["found"]))
    capture(evidence,"PICKER_READY_"+filename)
    adb("shell","input","tap",str(center[0]),str(center[1]))
    return {"picker_node_text":attrs.get("text",""),
            "picker_node_description":attrs.get("content-desc",""),
            "picker_node_package":attrs.get("package",""),
            "readiness_probes":attempt}

def capture(outdir,name):
    p=run("adb","exec-out","screencap","-p",check=True,text=False,capture=True)
    (outdir/(name+".png")).write_bytes(p.stdout)

def js_photo_signature(cdp, ref=None):
    if ref is None:
        ref="((JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}').addForm||{}).imageData||'')"
    expr=f"""(async()=>{{
      const s={ref};
      if(!s)return {{len:0,sha256:'',prefix:''}};
      const b=new TextEncoder().encode(s);
      const d=await crypto.subtle.digest('SHA-256',b);
      const h=Array.from(new Uint8Array(d)).map(x=>x.toString(16).padStart(2,'0')).join('');
      return {{len:s.length,sha256:h,prefix:s.slice(0,32)}};
    }})()"""
    return cdp.eval(expr)

def js_image_dims(cdp):
    return cdp.eval("""(async()=>{
      const S=JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}');
      const s=S.addForm&&S.addForm.imageData||'';
      if(!s)return {w:0,h:0,prefix:''};
      const img=new Image(); img.src=s; await img.decode();
      return {w:img.naturalWidth,h:img.naturalHeight,prefix:s.slice(0,32)};
    })()""")

def trigger_picker(cdp):
    ok=cdp.eval("""(()=>{const x=document.querySelector('[data-focus-key="piece-photo"]'); if(!x)return false; x.click(); return true})()""")
    if not ok: raise RuntimeError("piece-photo input missing")
    wait_until(lambda: PACKAGE not in foreground(),10,label="system picker foreground")

def select_photo(cdp,filename,fixture_dir,evidence):
    publish_fixture(filename,fixture_dir,evidence)
    trigger_picker(cdp)
    picker=pick_photo_thumbnail(filename,evidence)
    cdp.wait(sx("!!(S.addForm && !S.addForm.photoPending && S.addForm.imageData)"),35,
             label="photo processed for "+filename)
    signature=js_photo_signature(cdp)
    if signature["len"]<100 or not signature["prefix"].startswith("data:image/"):
        raise RuntimeError("PHOTO_CALLBACK_EMPTY: "+filename)
    (evidence/("PICKED_"+filename+".json")).write_text(
        json.dumps({"fixture":filename,"picker":picker,"signature":signature},indent=2)+"\\n")
    return signature

def state(cdp):
    return cdp.eval("""(()=>{
      const S=JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}');
      return {
        screen:S.screen,
        addOpen:S.addOpen,
        draftCount:S.draft?S.draft.draftGarments.length:0,
        draft:S.draft?S.draft.draftGarments.map(g=>({category:g.category,hasPhoto:!!g.imageData,imageLen:(g.imageData||'').length})):[],
        garmentCount:(S.garments||[]).length,
        outfitCount:(S.outfits||[]).length,
        committed:(S.garments||[]).map(g=>({category:g.category,hasPhoto:!!g.imageData,imageLen:(g.imageData||'').length}))
      };
    })()""")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apk",required=True)
    ap.add_argument("--fixtures",required=True)
    ap.add_argument("--evidence",required=True)
    args=ap.parse_args()
    fixture_dir=Path(args.fixtures)
    evidence=Path(args.evidence); evidence.mkdir(parents=True,exist_ok=True)
    results={"schema":"mhccl_html_image_emulator_v1","status":"RUNNING","tests":[],"environment":{}}

    def record(tid,status,details):
        results["tests"].append({"id":tid,"status":status,"details":details})
        (evidence/"RESULTS.json").write_text(json.dumps(results,indent=2)+"\n")

    adb("wait-for-device")
    results["environment"]["android_release"]=adb("shell","getprop","ro.build.version.release").stdout.strip()
    results["environment"]["api"]=adb("shell","getprop","ro.build.version.sdk").stdout.strip()
    results["environment"]["model"]=adb("shell","getprop","ro.product.model").stdout.strip()

    # Install exact debug APK created by this workflow.
    adb("install","-r",args.apk)
    results["environment"]["apk_sha256"]=sha256(args.apk)

    # Deliberately do not bulk-publish all images into Downloads.
    # Historical PASS used one active gallery image per picker operation.
    adb("shell","rm","-rf","/sdcard/Pictures/MHCClFixtureCurrent")
    adb("shell","mkdir","-p","/sdcard/Pictures/MHCClFixtureCurrent")
    manifest_path=fixture_dir/"GENERATED_MANIFEST.json"
    if not manifest_path.is_file(): raise RuntimeError("GENERATED_MANIFEST_MISSING")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    files={x["file"]:x["sha256"] for x in manifest["fixtures"]}
    for name,expected in files.items():
        if sha256(fixture_dir/name)!=expected:
            raise RuntimeError("FIXTURE_MANIFEST_HASH_MISMATCH: "+name)
    record("IMG00_FIXTURE_HASH_PREFLIGHT","PASS",
           {"count":len(files),"fixture_manifest_sha256":sha256(manifest_path)})
    launch()
    cdp=None
    # Cold emulator startup may expose a WebView socket before its canonical
    # DevTools target is ready. Bounded retry with environment evidence; never PASS
    # a photo assertion through a startup retry.
    for attempt in (1,2):
        try:
            cdp=CDP()
            break
        except Exception as startup_error:
            diagnostic={"attempt":attempt,"error":repr(startup_error),
                        "pid":adb("shell","pidof",PACKAGE,check=False).stdout.strip(),
                        "focus":foreground(),
                        "devtools_sockets":[line.strip() for line in adb("shell","cat","/proc/net/unix",check=False).stdout.splitlines() if "webview_devtools_remote" in line][-12:]}
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json",timeout=3) as target_resp:
                    diagnostic["devtools_targets"]=json.load(target_resp)
            except Exception as target_error:
                diagnostic["targets_error"]=repr(target_error)
            (evidence/("CDP_STARTUP_ATTEMPT_"+str(attempt)+".json")).write_text(
                json.dumps(diagnostic,indent=2)+"\\n")
            capture(evidence,"CDP_STARTUP_ATTEMPT_"+str(attempt))
            if attempt==2: raise
            launch()
            time.sleep(2)
    try:
        cdp.wait("typeof window.APP==='object' && !!document.querySelector('#app')",20,label="candidate app contract")
        candidate=cdp.eval("document.documentElement.innerHTML.includes('Capsule Matrix')")
        if not candidate: raise RuntimeError("canonical candidate did not render")

        # Clean test session only; source bytes remain unchanged.
        cdp.eval("localStorage.clear(); location.reload(); true")
        time.sleep(1.0)
        cdp.close(); cdp=CDP()
        cdp.wait("typeof window.APP==='object' && document.body.innerText.includes('Save my first outfit')",20,label="clean launch")
        capture(evidence,"00_clean_launch")

        cdp.eval("window.APP.startFirst(); window.APP.openAdd(); window.APP.pickCat('TOP'); true")
        cdp.wait(sx("S.screen==='builder' && S.addOpen && S.addForm.category==='TOP'"),10,label="TOP add form")

        first=select_photo(cdp,"top_white_01.jpg",fixture_dir,evidence)
        record("IMG01_INITIAL_PICK","PASS",first)
        capture(evidence,"01_initial_top")

        replacement=select_photo(cdp,"replacement_test.jpg",fixture_dir,evidence)
        if replacement["sha256"]==first["sha256"]: raise RuntimeError("replacement did not change processed photo")
        record("IMG02_REPLACE","PASS",{"before":first,"after":replacement})

        cdp.eval("window.APP.removeAddPhoto(); true")
        cdp.wait(sx("S.addForm && !S.addForm.imageData && !S.addForm.photoPending"),10,label="remove photo")
        record("IMG03_REMOVE","PASS",{"imageDataEmpty":True})

        # Re-add then cancel a second picker invocation; existing selected photo must survive.
        restored=select_photo(cdp,"top_white_01.jpg",fixture_dir,evidence)
        trigger_picker(cdp)
        adb("shell","input","keyevent","4")
        wait_until(lambda: PACKAGE in foreground(),12,label="return after picker cancel")
        time.sleep(.7)
        after_cancel=js_photo_signature(cdp)
        if after_cancel["sha256"]!=restored["sha256"]: raise RuntimeError("picker cancel changed existing photo")
        record("IMG04_PICKER_CANCEL","PASS",{"before":restored,"after":after_cancel})

        cdp.eval("window.APP.addDraftGarment(); true")
        cdp.wait(sx("S.draft && S.draft.draftGarments.length===1 && !!S.draft.draftGarments[0].imageData"),10,label="first draft photo commit")

        cdp.eval("window.APP.openAdd(); window.APP.pickCat('BOTTOM'); true")
        bottom=select_photo(cdp,"bottom_black_01.jpg",fixture_dir,evidence)
        cdp.eval("window.APP.addDraftGarment(); true")
        cdp.wait(sx("S.draft.draftGarments.length===2 && S.draft.draftGarments.every(g=>!!g.imageData)"),10,label="two photo drafts")
        ownership=cdp.eval("""(()=>{
          const S=JSON.parse(localStorage.getItem('mhccl_v31e_ui_copy_accessibility_candidate_state')||'{}');
          return {
            categories:S.draft.draftGarments.map(g=>g.category),
            distinct:S.draft.draftGarments[0].imageData!==S.draft.draftGarments[1].imageData
          };
        })()""")
        if ownership["categories"]!=["TOP","BOTTOM"] or not ownership["distinct"]:
            raise RuntimeError("draft image ownership separation failed")
        record("IMG05_MULTI_DRAFT_OWNERSHIP","PASS",{"top":restored,"bottom":bottom,"ownership":ownership})

        # Transparent PNG -> product compressor must yield JPEG.
        cdp.eval("window.APP.openAdd(); window.APP.pickCat('HIJAB'); true")
        transparent=select_photo(cdp,"transparent_hijab.png",fixture_dir,evidence)
        if not transparent["prefix"].startswith("data:image/jpeg"):
            raise RuntimeError("transparent PNG was not normalized to JPEG")
        dims_png=js_image_dims(cdp)
        record("IMG06_TRANSPARENT_PNG","PASS",{"signature":transparent,"dims":dims_png})

        # Small boundary image.
        cdp.eval("window.APP.removeAddPhoto(); true")
        small=select_photo(cdp,"boundary_small_64.png",fixture_dir,evidence)
        dims_small=js_image_dims(cdp)
        if (dims_small["w"],dims_small["h"]) != (64,64):
            raise RuntimeError(f"64x64 boundary changed unexpectedly: {dims_small}")
        record("IMG07_SMALL_BOUNDARY","PASS",{"signature":small,"dims":dims_small})

        # Large portrait compression => 420x560.
        cdp.eval("window.APP.removeAddPhoto(); window.APP.pickCat('DRESS'); true")
        large=select_photo(cdp,"large_portrait_test.jpg",fixture_dir,evidence)
        dims_large=js_image_dims(cdp)
        if max(dims_large["w"],dims_large["h"])>560 or (dims_large["w"],dims_large["h"])!=(420,560):
            raise RuntimeError(f"large image compression mismatch: {dims_large}")
        record("IMG08_LARGE_COMPRESSION","PASS",{"signature":large,"dims":dims_large})
        cdp.eval("window.APP.addDraftGarment(); true")
        cdp.wait(sx("S.draft.draftGarments.length===3"),10,label="three drafts")

        before_save=state(cdp)
        cdp.eval("window.APP.saveDraftOutfit(); true")
        cdp.wait(sx("S.screen==='success' && S.outfits.length===1 && S.garments.length===3"),15,label="save outfit with photos")
        saved=state(cdp)
        if not all(x["hasPhoto"] for x in saved["committed"]):
            raise RuntimeError("committed garment missing photo")
        record("IMG09_SAVE_COMMIT","PASS",{"before":before_save,"after":saved})
        capture(evidence,"09_saved_outfit")

        # Process kill/restart, then reconnect to the new WebView.
        cdp.close()
        launch()
        cdp=CDP()
        cdp.wait(sx("S.outfits.length===1 && S.garments.length===3"),20,label="restart persistence")
        persisted=state(cdp)
        if not all(x["hasPhoto"] for x in persisted["committed"]):
            raise RuntimeError("photo persistence failed after process restart")
        record("IMG10_PROCESS_RESTART_PERSISTENCE","PASS",persisted)
        capture(evidence,"10_restart_persisted")

        results["status"]="PASS"
    except Exception as e:
        results["status"]="FAIL"
        results["error"]=repr(e)
        try:capture(evidence,"FAIL_screen")
        except Exception:pass
        raise
    finally:
        try:cdp.close()
        except Exception:pass
        (evidence/"RESULTS.json").write_text(json.dumps(results,indent=2)+"\n")
        (evidence/"ENVIRONMENT.txt").write_text(
            json.dumps(results.get("environment",{}),indent=2)+"\n",encoding="utf-8"
        )

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}",file=sys.stderr)
        sys.exit(1)
