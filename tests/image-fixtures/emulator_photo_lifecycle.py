#!/usr/bin/env python3
import argparse, hashlib, json, os, re, subprocess, sys, time, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
import websocket

PACKAGE="com.aiprod.hijabccl.test"
COMPONENT=PACKAGE + "/com.aiprod.hijabccl.MainActivity"
PORT=9222

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
                return pages[0] if pages else None
            except Exception:
                return None
        t=wait_until(target,20,label="CDP page")
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

def pick_document(filename):
    # DocumentsUI normally exposes freshly pushed images in Recents.
    stem=Path(filename).stem
    try:
        return tap_named([filename,stem],10)
    except Exception:
        pass

    root=dump_ui()
    center,_=find_node(root,["show roots","open navigation drawer"])
    if center:
        adb("shell","input","tap",str(center[0]),str(center[1]))
        time.sleep(.7)
        try: tap_named(["Downloads","Download"],6)
        except Exception: pass
    else:
        try: tap_named(["Downloads","Download"],4)
        except Exception: pass
    time.sleep(.8)
    try:
        return tap_named([filename,stem],10)
    except Exception:
        pass

    # Last deterministic fallback: use DocumentsUI search.
    adb("shell","input","keyevent","84",check=False)
    time.sleep(.5)
    adb("shell","input","text",stem.replace("_","%s"),check=False)
    time.sleep(1.2)
    return tap_named([filename,stem],10)

def capture(outdir,name):
    p=run("adb","exec-out","screencap","-p",check=True,text=False,capture=True)
    (outdir/(name+".png")).write_bytes(p.stdout)

def js_photo_signature(cdp, ref="S.addForm&&S.addForm.imageData||''"):
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
      const s=S.addForm&&S.addForm.imageData||'';
      if(!s)return {w:0,h:0,prefix:''};
      const img=new Image(); img.src=s; await img.decode();
      return {w:img.naturalWidth,h:img.naturalHeight,prefix:s.slice(0,32)};
    })()""")

def trigger_picker(cdp):
    ok=cdp.eval("""(()=>{const x=document.querySelector('[data-focus-key="piece-photo"]'); if(!x)return false; x.click(); return true})()""")
    if not ok: raise RuntimeError("piece-photo input missing")
    wait_until(lambda: PACKAGE not in foreground(),10,label="system picker foreground")

def select_photo(cdp,filename):
    trigger_picker(cdp)
    pick_document(filename)
    wait_until(lambda: PACKAGE in foreground(),15,label="app foreground after picker")
    cdp.wait("!!(S.addForm && !S.addForm.photoPending && S.addForm.imageData)",25,label="photo processed")
    return js_photo_signature(cdp)

def state(cdp):
    return cdp.eval("""(()=>({
      screen:S.screen,
      addOpen:S.addOpen,
      draftCount:S.draft?S.draft.draftGarments.length:0,
      draft:S.draft?S.draft.draftGarments.map(g=>({category:g.category,hasPhoto:!!g.imageData,imageLen:(g.imageData||'').length})):[],
      garmentCount:S.garments.length,
      outfitCount:S.outfits.length,
      committed:S.garments.map(g=>({category:g.category,hasPhoto:!!g.imageData,imageLen:(g.imageData||'').length}))
    }))()""")

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

    for p in sorted(fixture_dir.iterdir()):
        if p.suffix.lower() not in {".jpg",".jpeg",".png"}: continue
        remote="/sdcard/Download/"+p.name
        adb("push",str(p),remote)
        adb("shell","am","broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE","-d","file://"+remote,check=False)
    time.sleep(1)

    launch()
    cdp=CDP()
    try:
        cdp.wait("typeof S!=='undefined' && typeof APP!=='undefined'",20,label="candidate globals")
        candidate=cdp.eval("document.documentElement.innerHTML.includes('Capsule Matrix')")
        if not candidate: raise RuntimeError("canonical candidate did not render")

        # Clean test session only; source bytes remain unchanged.
        cdp.eval("localStorage.clear(); location.reload(); true")
        time.sleep(1.0)
        cdp.close(); cdp=CDP()
        cdp.wait("typeof S!=='undefined' && S.screen==='launch'",20,label="clean launch")
        capture(evidence,"00_clean_launch")

        cdp.eval("APP.startFirst(); APP.openAdd(); APP.pickCat('TOP'); true")
        cdp.wait("S.screen==='builder' && S.addOpen && S.addForm.category==='TOP'",10,label="TOP add form")

        first=select_photo(cdp,"top_white_01.jpg")
        record("IMG01_INITIAL_PICK","PASS",first)
        capture(evidence,"01_initial_top")

        replacement=select_photo(cdp,"replacement_test.jpg")
        if replacement["sha256"]==first["sha256"]: raise RuntimeError("replacement did not change processed photo")
        record("IMG02_REPLACE","PASS",{"before":first,"after":replacement})

        cdp.eval("APP.removeAddPhoto(); true")
        cdp.wait("S.addForm && !S.addForm.imageData && !S.addForm.photoPending",10,label="remove photo")
        record("IMG03_REMOVE","PASS",{"imageDataEmpty":True})

        # Re-add then cancel a second picker invocation; existing selected photo must survive.
        restored=select_photo(cdp,"top_white_01.jpg")
        trigger_picker(cdp)
        adb("shell","input","keyevent","4")
        wait_until(lambda: PACKAGE in foreground(),12,label="return after picker cancel")
        time.sleep(.7)
        after_cancel=js_photo_signature(cdp)
        if after_cancel["sha256"]!=restored["sha256"]: raise RuntimeError("picker cancel changed existing photo")
        record("IMG04_PICKER_CANCEL","PASS",{"before":restored,"after":after_cancel})

        cdp.eval("APP.addDraftGarment(); true")
        cdp.wait("S.draft && S.draft.draftGarments.length===1 && !!S.draft.draftGarments[0].imageData",10,label="first draft photo commit")

        cdp.eval("APP.openAdd(); APP.pickCat('BOTTOM'); true")
        bottom=select_photo(cdp,"bottom_black_01.jpg")
        cdp.eval("APP.addDraftGarment(); true")
        cdp.wait("S.draft.draftGarments.length===2 && S.draft.draftGarments.every(g=>!!g.imageData)",10,label="two photo drafts")
        ownership=cdp.eval("""(()=>({
          categories:S.draft.draftGarments.map(g=>g.category),
          distinct:S.draft.draftGarments[0].imageData!==S.draft.draftGarments[1].imageData
        }))()""")
        if ownership["categories"]!=["TOP","BOTTOM"] or not ownership["distinct"]:
            raise RuntimeError("draft image ownership separation failed")
        record("IMG05_MULTI_DRAFT_OWNERSHIP","PASS",{"top":restored,"bottom":bottom,"ownership":ownership})

        # Transparent PNG -> product compressor must yield JPEG.
        cdp.eval("APP.openAdd(); APP.pickCat('HIJAB'); true")
        transparent=select_photo(cdp,"transparent_hijab.png")
        if not transparent["prefix"].startswith("data:image/jpeg"):
            raise RuntimeError("transparent PNG was not normalized to JPEG")
        dims_png=js_image_dims(cdp)
        record("IMG06_TRANSPARENT_PNG","PASS",{"signature":transparent,"dims":dims_png})

        # Small boundary image.
        cdp.eval("APP.removeAddPhoto(); true")
        small=select_photo(cdp,"boundary_small_64.png")
        dims_small=js_image_dims(cdp)
        if (dims_small["w"],dims_small["h"]) != (64,64):
            raise RuntimeError(f"64x64 boundary changed unexpectedly: {dims_small}")
        record("IMG07_SMALL_BOUNDARY","PASS",{"signature":small,"dims":dims_small})

        # Large portrait compression => 420x560.
        cdp.eval("APP.removeAddPhoto(); APP.pickCat('DRESS'); true")
        large=select_photo(cdp,"large_portrait_test.jpg")
        dims_large=js_image_dims(cdp)
        if max(dims_large["w"],dims_large["h"])>560 or (dims_large["w"],dims_large["h"])!=(420,560):
            raise RuntimeError(f"large image compression mismatch: {dims_large}")
        record("IMG08_LARGE_COMPRESSION","PASS",{"signature":large,"dims":dims_large})
        cdp.eval("APP.addDraftGarment(); true")
        cdp.wait("S.draft.draftGarments.length===3",10,label="three drafts")

        before_save=state(cdp)
        cdp.eval("APP.saveDraftOutfit(); true")
        cdp.wait("S.screen==='success' && S.outfits.length===1 && S.garments.length===3",15,label="save outfit with photos")
        saved=state(cdp)
        if not all(x["hasPhoto"] for x in saved["committed"]):
            raise RuntimeError("committed garment missing photo")
        record("IMG09_SAVE_COMMIT","PASS",{"before":before_save,"after":saved})
        capture(evidence,"09_saved_outfit")

        # Process kill/restart, then reconnect to the new WebView.
        cdp.close()
        launch()
        cdp=CDP()
        cdp.wait("typeof S!=='undefined' && S.outfits.length===1 && S.garments.length===3",20,label="restart persistence")
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
