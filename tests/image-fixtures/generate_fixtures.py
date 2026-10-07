#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, struct, zlib

OUT = Path(__file__).resolve().parent / "generated"
OUT.mkdir(parents=True, exist_ok=True)

def png_bytes(width, height, rgb):
    r,g,b = rgb
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t+data) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            # deterministic mild checker/gradient so replacements are visually distinct
            delta = ((x // max(1,width//8)) + (y // max(1,height//8))) % 2
            rr = max(0,min(255,r + (12 if delta else -12)))
            gg = max(0,min(255,g + (12 if delta else -12)))
            bb = max(0,min(255,b + (12 if delta else -12)))
            row.extend((rr,gg,bb))
        rows.append(bytes(row))
    raw = b"".join(rows)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")

fixtures = [
    ("top_white_01.png", 640, 800, (232,232,228), "base_top"),
    ("bottom_black_01.png", 640, 800, (42,42,46), "base_bottom"),
    ("dress_beige_01.png", 640, 800, (190,172,145), "dress"),
    ("outer_olive_01.png", 640, 800, (113,120,82), "outer"),
    ("hijab_taupe_01.png", 640, 800, (150,132,120), "hijab_primary"),
    ("hijab_black_02.png", 640, 800, (35,35,38), "hijab_secondary"),
    ("shoes_neutral_01.png", 640, 640, (178,170,158), "shoes"),
    ("replacement_test.png", 800, 640, (128,160,184), "replace_owner"),
    ("tiny_boundary.png", 8, 8, (200,100,120), "tiny_boundary"),
    ("large_memory_smoke.png", 2048, 2048, (126,154,118), "large_memory_smoke"),
]

manifest = {"schema":"mhccl-image-fixtures-v1","fixtures":[]}
for name,w,h,rgb,role in fixtures:
    data = png_bytes(w,h,rgb)
    p = OUT / name
    p.write_bytes(data)
    manifest["fixtures"].append({
        "filename":name,
        "role":role,
        "mime":"image/png",
        "width":w,
        "height":h,
        "bytes":len(data),
        "sha256":hashlib.sha256(data).hexdigest()
    })

(OUT/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
