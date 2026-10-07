#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import argparse, hashlib, json

FIXTURES = [
    ("top_white_01.jpg",(900,1200),(236,232,222),(245,245,240),"TOP-WHITE-01","top","JPEG","initial top photo / persistence"),
    ("bottom_black_01.jpg",(900,1200),(235,231,224),(45,45,45),"BOTTOM-BLACK-01","bottom","JPEG","second garment / ownership separation"),
    ("dress_beige_01.jpg",(900,1200),(232,237,231),(191,167,132),"DRESS-BEIGE-01","dress","JPEG","dress category fixture"),
    ("outer_olive_01.jpg",(900,1200),(239,235,227),(108,118,82),"OUTER-OLIVE-01","outer","JPEG","outer category fixture"),
    ("hijab_taupe_01.jpg",(900,1200),(238,234,230),(154,132,119),"HIJAB-TAUPE-01","hijab","JPEG","primary hijab fixture"),
    ("hijab_black_02.jpg",(900,1200),(235,232,228),(55,55,55),"HIJAB-BLACK-02","hijab","JPEG","alternate hijab / relation reuse"),
    ("shoes_neutral_01.jpg",(1200,900),(238,238,234),(156,145,125),"SHOES-NEUTRAL-01","shoes","JPEG","landscape orientation fixture"),
    ("replacement_test.jpg",(900,1200),(230,238,240),(99,141,155),"REPLACEMENT-TEST","top","JPEG","replace-photo scenario"),
    ("boundary_small_64.png",(64,64),(240,240,240),(120,130,160),"SMALL","scarf","PNG","minimum-size/boundary image"),
    ("transparent_hijab.png",(900,1200),(0,0,0),(147,109,126),"TRANSPARENT-HIJAB","hijab","PNG","PNG alpha/transparency handling"),
    ("large_portrait_test.jpg",(2400,3200),(242,239,231),(126,104,151),"LARGE-PORTRAIT","dress","JPEG","large-image memory/persistence smoke"),
]

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def garment_image(path, size, bg, garment, label, kind="top", fmt="JPEG", quality=90, transparent=False):
    w,h=size
    mode="RGBA" if transparent else "RGB"
    base=(0,0,0,0) if transparent else bg
    im=Image.new(mode,size,base)
    d=ImageDraw.Draw(im)
    cx=w//2; y0=int(h*0.18); y1=int(h*0.82); gw=int(w*0.42); gh=y1-y0
    outline=(30,30,30,255) if transparent else (30,30,30)
    fill=garment+(255,) if transparent else garment

    if kind=="top":
        pts=[(cx-gw//2,y0+gh//4),(cx-gw//5,y0),(cx+gw//5,y0),(cx+gw//2,y0+gh//4),
             (cx+gw//3,y0+gh//2),(cx+gw//4,y1),(cx-gw//4,y1),(cx-gw//3,y0+gh//2)]
        d.polygon(pts, fill=fill, outline=outline)
    elif kind=="bottom":
        d.polygon([(cx-gw//3,y0),(cx+gw//3,y0),(cx+gw//5,y1),(cx,y0+gh//2),(cx-gw//5,y1)], fill=fill, outline=outline)
    elif kind=="dress":
        d.polygon([(cx-gw//5,y0),(cx+gw//5,y0),(cx+gw//3,y0+gh//3),(cx+gw//2,y1),(cx-gw//2,y1),(cx-gw//3,y0+gh//3)], fill=fill, outline=outline)
    elif kind=="outer":
        d.rectangle([cx-gw//3,y0,cx+gw//3,y1], fill=fill, outline=outline, width=max(1,w//200))
        d.line([cx,y0,cx,y1], fill=outline, width=max(1,w//180))
    elif kind=="hijab":
        d.ellipse([cx-gw//3,y0,cx+gw//3,y0+gh//2], fill=fill, outline=outline)
        d.polygon([(cx-gw//3,y0+gh//4),(cx+gw//3,y0+gh//4),(cx+gw//2,y1),(cx-gw//2,y1)], fill=fill, outline=outline)
    elif kind=="shoes":
        d.rounded_rectangle([cx-gw//2,y0+gh//2,cx-5,y1], radius=max(4,w//30), fill=fill, outline=outline)
        d.rounded_rectangle([cx+5,y0+gh//2,cx+gw//2,y1], radius=max(4,w//30), fill=fill, outline=outline)
    elif kind=="scarf":
        d.rounded_rectangle([cx-gw//4,y0,cx+gw//4,y1], radius=max(4,w//30), fill=fill, outline=outline)
    else:
        d.rectangle([cx-gw//3,y0,cx+gw//3,y1], fill=fill, outline=outline)

    band_h=max(18, int(h*0.07))
    band_fill=(245,245,245,230) if transparent else (245,245,245)
    d.rectangle([0,h-band_h,w,h], fill=band_fill)
    d.text((max(4,w//50), h-band_h+max(2,band_h//6)), label, fill=(10,10,10,255) if transparent else (10,10,10))

    if fmt=="JPEG":
        if im.mode=="RGBA":
            bgim=Image.new("RGB", im.size, (255,255,255))
            bgim.paste(im, mask=im.getchannel("A"))
            im=bgim
        im.save(path, format=fmt, quality=quality, optimize=True)
    else:
        im.save(path, format=fmt)

def generate(out):
    out.mkdir(parents=True, exist_ok=True)
    records=[]
    for name,size,bg,garment,label,kind,fmt,scenario in FIXTURES:
        p=out/name
        garment_image(p,size,bg,garment,label,kind,fmt,transparent=name=="transparent_hijab.png")
        img=Image.open(p)
        records.append({
            "file":name,
            "sha256":sha256(p),
            "bytes":p.stat().st_size,
            "width":img.width,
            "height":img.height,
            "mime":"image/jpeg" if fmt=="JPEG" else "image/png",
            "scenario":scenario,
        })
    manifest={
        "schema":"mhccl_image_fixture_manifest_v1",
        "purpose":"Synthetic non-sensitive deterministic fixtures for HTML/Android photo-picker verification",
        "source":"generated test fixtures; no personal/copyrighted source photos",
        "pillow_version":__import__("PIL").__version__,
        "fixture_count":len(records),
        "fixtures":records,
    }
    (out/"GENERATED_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    ap.add_argument("--expected")
    args=ap.parse_args()
    manifest=generate(Path(args.out))
    if args.expected:
        expected=json.loads(Path(args.expected).read_text(encoding="utf-8"))
        exp={x["file"]:x["sha256"] for x in expected["fixtures"]}
        got={x["file"]:x["sha256"] for x in manifest["fixtures"]}
        if exp != got:
            missing=sorted(set(exp)^set(got))
            mismatches=sorted(k for k in exp.keys()&got.keys() if exp[k]!=got[k])
            raise SystemExit(f"fixture hash verification failed; missing={missing}; mismatches={mismatches}")
        print(f"Fixture SHA verification PASS: {len(got)}/{len(exp)}")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__":
    main()
