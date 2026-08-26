#!/usr/bin/env python3
"""Stylized Australia -> NW Tasmania zoom, brand-styled, pure PIL."""
import json, math, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
SS = 2  # supersample
FPS = 24
DUR = 3.2
N = int(DUR * FPS)  # 77 frames

BG = (10, 12, 15)
LAND = (28, 33, 40)
LAND_TAS = (44, 50, 58)
COAST = (120, 112, 90)
COAST_TAS = (204, 178, 104)
GOLD = (204, 178, 104)
WHITE = (240, 238, 232)

PIN = (146.585, -41.16)  # Bakers Beach, NW Tasmania

feats = json.load(open(os.path.join(BASE, "work/admin1_au.json")))["features"]

def polys_of(f):
    g = f["geometry"]
    if g["type"] == "Polygon":
        return [g["coordinates"][0]]
    return [p[0] for p in g["coordinates"]]

STATES = [(f["properties"]["STATE_NAME"], polys_of(f)) for f in feats]

def ease(t):  # smootherstep
    return t*t*t*(t*(t*6-15)+10)

# viewport keyframes: (cx, cy, half_height_deg)
KA = (133.5, -27.0, 21.0)   # Australia
KB = (146.55, -41.35, 1.05)  # NW Tasmania

F6 = ImageFont.truetype(os.path.join(BASE, "fonts/Montserrat-600.ttf"), 46)
F7 = ImageFont.truetype(os.path.join(BASE, "fonts/Montserrat-700.ttf"), 78)
F5 = ImageFont.truetype(os.path.join(BASE, "fonts/Montserrat-500.ttf"), 38)

os.makedirs(os.path.join(BASE, "map_frames"), exist_ok=True)

ZOOM_END = 0.72  # fraction of timeline when zoom completes

for fi in range(N):
    t = fi / (N - 1)
    zt = ease(min(1.0, t / ZOOM_END))
    # interpolate in log space for zoom feel
    hh = math.exp(math.log(KA[2]) + (math.log(KB[2]) - math.log(KA[2])) * zt)
    cx = KA[0] + (KB[0] - KA[0]) * zt
    cy = KA[1] + (KB[1] - KA[1]) * zt
    latsc = math.cos(math.radians(cy))
    hw = hh * (W / H) / latsc

    img = Image.new("RGB", (W*SS, H*SS), BG)
    dr = ImageDraw.Draw(img)

    def prj(lon, lat):
        x = (lon - cx) / hw * (W*SS/2) * latsc / math.cos(math.radians(lat)) if False else (lon - cx) / hw * (W*SS/2)
        y = -(lat - cy) / hh * (H*SS/2)
        return (W*SS/2 + x, H*SS/2 + y)

    MARG = 400
    def clip_poly(pts):
        # Sutherland-Hodgman against expanded viewport box
        def clip_edge(pts, inside, inter):
            out = []
            for i in range(len(pts)):
                a, b = pts[i-1], pts[i]
                ia, ib = inside(a), inside(b)
                if ib:
                    if not ia:
                        out.append(inter(a, b))
                    out.append(b)
                elif ia:
                    out.append(inter(a, b))
            return out
        x0, y0, x1, y1 = -MARG, -MARG, W*SS+MARG, H*SS+MARG
        for inside, inter in (
            (lambda p: p[0] >= x0, lambda a, b: (x0, a[1]+(b[1]-a[1])*(x0-a[0])/(b[0]-a[0]))),
            (lambda p: p[0] <= x1, lambda a, b: (x1, a[1]+(b[1]-a[1])*(x1-a[0])/(b[0]-a[0]))),
            (lambda p: p[1] >= y0, lambda a, b: (a[0]+(b[0]-a[0])*(y0-a[1])/(b[1]-a[1]), y0)),
            (lambda p: p[1] <= y1, lambda a, b: (a[0]+(b[0]-a[0])*(y1-a[1])/(b[1]-a[1]), y1)),
        ):
            pts = clip_edge(pts, inside, inter)
            if len(pts) < 3:
                return []
        return pts

    for name, polys in STATES:
        tas = name == "Tasmania"
        fill = LAND_TAS if tas else LAND
        line = COAST_TAS if tas else COAST
        lw = (6 if tas else 3)
        for poly in polys:
            pts = [prj(lo, la) for lo, la in poly]
            if len(pts) < 3:
                continue
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if max(xs) < -MARG or min(xs) > W*SS+MARG or max(ys) < -MARG or min(ys) > H*SS+MARG:
                continue
            cp = clip_poly(pts)
            if len(cp) < 3:
                continue
            dr.polygon(cp, fill=fill, outline=line, width=lw)

    # pin + pulse after zoom completes
    if t > 0.60:
        a = min(1.0, (t - 0.60) / 0.18)
        px, py = prj(*PIN)
        # pulse rings
        ph = (t * 2.2) % 1.0
        for ring, base in ((ph, 1.0), ((ph + 0.5) % 1.0, 0.6)):
            rr = (30 + 150 * ring) * SS / 2
            alpha = int(140 * base * (1 - ring) * a)
            if alpha > 4:
                ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                od.ellipse([px-rr, py-rr, px+rr, py+rr], outline=(*GOLD, alpha), width=4*SS)
                img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        dr = ImageDraw.Draw(img)
        r = 14 * SS * a
        dr.ellipse([px-r, py-r, px+r, py+r], fill=GOLD)
        dr.ellipse([px-r*0.45, py-r*0.45, px+r*0.45, py+r*0.45], fill=BG)

    img = img.resize((W, H), Image.LANCZOS)

    # labels fade in
    if t > 0.70:
        a = min(1.0, (t - 0.70) / 0.15)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        px, py = prj(*PIN); px /= SS; py /= SS
        tx = px + 70; ty = py - 120
        od.text((tx+2, ty+3), "BAKERS BEACH", font=F7, fill=(0, 0, 0, int(160*a)))
        od.text((tx, ty), "BAKERS BEACH", font=F7, fill=(*WHITE, int(255*a)))
        od.text((tx+2, ty+95+2), "NORTH WEST TASMANIA", font=F6, fill=(0, 0, 0, int(160*a)))
        od.text((tx, ty+95), "NORTH WEST TASMANIA", font=F6, fill=(*GOLD, int(255*a)))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    # vignette
    img.save(os.path.join(BASE, f"map_frames/f{fi:03d}.png"))

subprocess.run(["ffmpeg", "-v", "error", "-framerate", str(FPS),
                "-i", os.path.join(BASE, "map_frames/f%03d.png"),
                "-vf", "vignette=PI/5",
                "-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264",
                "-crf", "17", "-preset", "medium", "-t", f"{DUR:.3f}",
                "-an", "-y", os.path.join(BASE, "ai/map.mp4")], check=True)
print("map done")
