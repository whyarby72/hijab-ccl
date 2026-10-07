#!/usr/bin/env bash
set -euo pipefail

ANDROID_SRC="${1:?android source checkout required}"
FIXTURE_SRC="${2:?fixture source checkout required}"
PKG="com.aiprod.hijabccl.test"
ACT="com.aiprod.hijabccl.MainActivity"
OUT="$FIXTURE_SRC/evidence/html-image-fixture-emulator"
mkdir -p "$OUT/screenshots" "$OUT/logs"

log(){ printf '%s,%s,%q\n' "$(date -u +%FT%TZ)" "$1" "${2:-}" >> "$OUT/TIMELINE.csv"; }
fail(){ echo "FAIL: $*" >&2; log FAIL "$*"; exit 1; }

echo "timestamp,event,detail" > "$OUT/TIMELINE.csv"

# 1) Build exact Android TEST host which packages exact canonical HTML.
(
  cd "$ANDROID_SRC/android"
  gradle :androidApp:verifyPrototypeSha :androidApp:assembleDebug --stacktrace
)
APK="$ANDROID_SRC/android/androidApp/build/outputs/apk/debug/androidApp-debug.apk"
test -f "$APK" || fail "debug APK missing"
APK_SHA="$(sha256sum "$APK" | awk '{print $1}')"
HTML_SHA="$(sha256sum "$ANDROID_SRC/prototype/index.html" | awk '{print $1}')"
test "$HTML_SHA" = "861f38ff85f11e6c53d9b0b0f6166b5e6386accca0572a41d108680eb593c171" || fail "HTML SHA mismatch"
log BUILD "apk_sha=$APK_SHA html_sha=$HTML_SHA"

# 2) Install app and real fixture files.
adb install -r "$APK"
adb shell pm clear "$PKG" >/dev/null
adb shell rm -rf /data/local/tmp/MHCClFixtures
adb shell mkdir -p /data/local/tmp/MHCClFixtures
adb shell rm -rf /sdcard/Pictures/MHCClFixtureCurrent
adb shell mkdir -p /sdcard/Pictures/MHCClFixtureCurrent
for f in "$FIXTURE_SRC"/tests/image-fixtures/generated/*.png; do
  adb push "$f" /data/local/tmp/MHCClFixtures/
done
log FIXTURES "staged_private=/data/local/tmp/MHCClFixtures"

dump_ui(){
  rm -f /tmp/window.xml
  adb shell rm -f /sdcard/window.xml >/dev/null 2>&1 || true
  for _ in $(seq 1 5); do
    if adb shell uiautomator dump /sdcard/window.xml >/dev/null 2>&1 &&
       adb pull /sdcard/window.xml /tmp/window.xml >/dev/null 2>&1 &&
       python3 - <<'PY' >/dev/null 2>&1
import xml.etree.ElementTree as ET
root=ET.parse('/tmp/window.xml').getroot()
assert root.tag == 'hierarchy'
assert any(n.attrib.get('class') == 'android.webkit.WebView' for n in root.iter('node'))
PY
    then
      return 0
    fi
    rm -f /tmp/window.xml
    sleep 0.5
  done
  return 1
}

node_bounds(){
  local needle="$1"
  dump_ui || return 2
  python3 - "$needle" <<'PY'
import sys, re, xml.etree.ElementTree as ET
needle=sys.argv[1]
root=ET.parse('/tmp/window.xml').getroot()
matches=[]
for n in root.iter('node'):
    text=(n.attrib.get('text') or '')+' '+(n.attrib.get('content-desc') or '')
    if needle.lower() in text.lower():
        b=n.attrib.get('bounds','')
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',b)
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            matches.append(((x1+x2)//2,(y1+y2)//2,text.strip(),b))
if not matches:
    raise SystemExit(2)
x,y,text,b=matches[0]
print(f"{x} {y}")
PY
}

wait_node(){
  local needle="$1" tries="${2:-30}"
  for _ in $(seq 1 "$tries"); do
    if node_bounds "$needle" >/tmp/xy 2>/dev/null; then return 0; fi
    sleep 1
  done
  dump_ui
  cp /tmp/window.xml "$OUT/logs/last_ui.xml" || true
  return 1
}

tap_node(){
  local needle="$1"
  wait_node "$needle" 30 || fail "UI node not found: $needle"
  read -r x y < /tmp/xy
  adb shell input tap "$x" "$y"
  log TAP "$needle @ $x,$y"
  sleep 1
}

publish_fixture(){
  local filename="$1"
  local src="/data/local/tmp/MHCClFixtures/$filename"
  local dst="/sdcard/Pictures/MHCClFixtureCurrent/$filename"
  adb shell cp "$src" "$dst"
  adb shell touch "$dst"
  adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://$dst" >/dev/null || true
  sleep 2
  log PUBLISH_FIXTURE "$filename -> $dst"
}

select_active_photo(){
  wait_node "Photos" 20 || fail "Android Photo Picker did not open"
  if wait_node "Dismiss" 2; then
    tap_node "Dismiss"
  fi
  wait_node "Photo taken" 30 || fail "active fixture not visible in Android Photo Picker"
  tap_node "Photo taken"
  sleep 2
}

shot(){
  local name="$1"
  adb exec-out screencap -p > "$OUT/screenshots/$name.png"
}

# 3) Launch exact HTML through TEST host.
adb shell am start -n "$PKG/$ACT" >/dev/null
wait_node "Save my first outfit" 40 || fail "launch screen unavailable"
shot 00_launch
tap_node "Save my first outfit"
tap_node "+ Add a piece"
tap_node "Top"
publish_fixture "top_white_01.png"
tap_node "Choose local photo"
select_active_photo
wait_node "Remove photo" 30 || fail "top photo did not attach"
shot 01_top_attached

# Replace through real picker.
publish_fixture "replacement_test.png"
tap_node "Replace local photo"
select_active_photo
wait_node "Remove photo" 30 || fail "replacement photo did not attach"
shot 02_replaced
tap_node "Add to outfit"

# Bottom: exercise picker cancel then select.
tap_node "+ Add a piece"
tap_node "Bottom"
publish_fixture "bottom_black_01.png"
tap_node "Choose local photo"
sleep 2
adb shell input keyevent 4
log PICKER_CANCEL "real Android Back in system picker"
wait_node "Choose local photo" 20 || fail "picker cancel did not return cleanly"
tap_node "Choose local photo"
select_active_photo
wait_node "Remove photo" 30 || fail "bottom photo did not attach"
tap_node "Add to outfit"
shot 03_two_pieces

tap_node "Save first outfit"
wait_node "First outfit saved" 30 || fail "first outfit save failed"
shot 04_saved

# 4) Lifecycle persistence: force-stop and relaunch.
adb shell am force-stop "$PKG"
sleep 2
adb shell am start -n "$PKG/$ACT" >/dev/null
wait_node "First outfit saved" 40 || fail "saved success state missing after force-stop/relaunch"
wait_node "Top 1" 10 || fail "persisted Top 1 missing after relaunch"
wait_node "Bottom 1" 10 || fail "persisted Bottom 1 missing after relaunch"
shot 05_reopen_success_persisted
log PERSISTENCE "success state with Top 1 + Bottom 1 restored after force-stop/relaunch"
tap_node "Done for now"
wait_node "1 saved outfit" 30 || fail "saved outfit missing after leaving restored success state"
shot 05b_home_persisted
log PERSISTENCE_HOME "1 saved outfit visible on Home after restored success state"

# Supporting machine evidence: data URL should exist in WebView storage.
if adb shell run-as "$PKG" sh -c "grep -R -a -m1 'data:image/png;base64' app_webview 2>/dev/null" >/tmp/image_storage_hit.txt 2>/dev/null; then
  log STORAGE "image_data_url_present_in_webview_storage"
else
  log STORAGE_HOLD "data URL not grep-readable; UI persistence remains primary evidence"
fi

# 5) Tiny + large memory smoke in one unsaved draft.
tap_node "Save"
tap_node "+ Add a piece"
tap_node "Outer"
publish_fixture "tiny_boundary.png"
tap_node "Choose local photo"
select_active_photo
wait_node "Remove photo" 30 || fail "tiny image did not attach"
publish_fixture "large_memory_smoke.png"
tap_node "Replace local photo"
select_active_photo
wait_node "Remove photo" 40 || fail "large image did not attach"
shot 06_large_image
tap_node "Cancel"
log BOUNDARY "tiny+large picker smoke completed"

# 6) Enable tools via query without editing canonical HTML.
# WebView host normally loads START_URL without query. Re-launch via adb is insufficient
# to alter the WebView URL, so export privacy remains covered by deterministic source suite
# unless the host is explicitly parameterized in a later bounded TEST-only harness.
log EXPORT_PRIVACY_HOLD "runtime tools query not exposed by host; do not patch canonical HTML"

# 7) Bounded logcat and environment.
adb logcat -d -t 1200 > "$OUT/logs/logcat_tail.txt" || true
adb shell getprop ro.build.version.sdk > "$OUT/android_api.txt"
adb shell getprop ro.product.model > "$OUT/device_model.txt"

python3 - "$OUT" "$APK_SHA" "$HTML_SHA" <<'PY'
import json,sys,pathlib,datetime
out=pathlib.Path(sys.argv[1])
r={
 "schema":"mhccl-html-image-fixture-emulator-v1",
 "status":"PASS_WITH_HOLDS",
 "candidate_sha256":sys.argv[3],
 "apk_sha256":sys.argv[2],
 "tests":{
   "real_picker_attach":"PASS",
   "real_picker_replace":"PASS",
   "real_picker_cancel":"PASS",
   "save_and_reopen_persistence":"PASS",
   "tiny_boundary":"PASS",
   "large_memory_smoke":"PASS",
   "export_privacy_runtime":"HOLD_HARNESS_LIMITATION"
 },
 "source_changed":False,
 "build_authorized":False,
 "release_authorized":False,
 "publication_authorized":False
}
(out/"RESULT.json").write_text(json.dumps(r,indent=2)+"\n")
(out/"REPORT.md").write_text("""# HTML Image Fixture Emulator Report

Status: **PASS_WITH_HOLDS**

PASS: real system picker attach, replace, cancel, first-outfit save, force-stop/relaunch persistence, tiny image boundary, large image memory smoke.

HOLD: runtime export privacy in this host because the canonical HTML exposes research tools only through `?tools=1` and the TEST shell currently loads the canonical URL without query parameters. The deterministic verifier already covers export sanitization; this workflow deliberately does not patch the canonical HTML merely to clear this hold.

No BUILD/release/publication authority is granted.
""")
PY

echo "HTML image fixture emulator flow completed"
