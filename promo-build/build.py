#!/usr/bin/env python3
"""Ten Fifty Bakers x NWTRS promo — segment renderer + assembler."""
import json, math, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_N = os.path.join(BASE, "src/nwrts")
SRC_B = os.path.join(BASE, "src/bakers")
SRC_C = os.path.join(BASE, "src/clips")
SEG = os.path.join(BASE, "segments")
AI = os.path.join(BASE, "ai")
os.makedirs(SEG, exist_ok=True)

FPS = 24
W, H = 1920, 1080
SONG_END = 184.92

with open(os.path.join(BASE, "work/beats.txt")) as f:
    BEATS = [float(l) for l in f if l.strip()]

def snap(t, tol=0.45):
    best = min(BEATS, key=lambda b: abs(b - t))
    return best if abs(best - t) <= tol else t

# ---------------------------------------------------------------- EDL
# type: vid | still | trip | ai
# kb: in | out | panlr | panrl | up | down   (stills)
# grade: phone applies mild sat/contrast lift
V, S = "vid", "still"

def N(f): return os.path.join(SRC_N, f)
def B(f): return os.path.join(SRC_B, f)
def C(f): return os.path.join(SRC_C, f)
def WP(f): return os.path.join(BASE, "src/webphotos", f)

ACTS = [
    # (act_end_time, [shots])
    (9.6, [
        dict(id=0, type=V, src=C("Web_Clip_Drone_013.mp4"), start=0.3, w=9.6),
    ]),
    (24.0, [
        dict(id=1, type=V, src=C("Web_Clip_Drone_06.mp4"), start=0.0, w=2.6),
        dict(id=2, type=V, src=C("Web_Clip_Drone_010.mp4"), start=1.0, w=4.2),
        dict(id=3, type=V, src=C("Web_Clip_Drone_09.mp4"), start=9.0, w=4.2),
        dict(id=4, type="ai", src=os.path.join(AI, "map.mp4"),
             fallback=dict(type=S, src=N("IMG_2.JPG"), kb="in"), w=4.6),
    ]),
    (48.2, [
        dict(id=5, type=V, src=N("IMG_0409.MP4"), start=1.0, w=4.0, grade="phone"),
        dict(id=6, type=V, src=N("IMG_1176.MP4"), start=2.0, w=3.4, grade="phone"),
        dict(id=7, type="trip", src=[N("IMG_6220.MP4"), N("IMG_6234.MP4"), N("IMG_7746.MP4")],
             start=[0.5, 0.5, 3.5], speed=[1.0, 1.0, 0.7], w=4.2, grade="phone"),
        dict(id=8, type=S, src=N("IMG_1187.JPEG"), kb="up", sway=True, w=3.2),
        dict(id=9, type=V, src=C("Web_Clip_Ground_00275535.mp4"), start=2.0, w=4.4),
        dict(id=10, type=V, src=C("Web_Clip_Ground_00278650.mp4"), start=1.0, w=3.0),
        dict(id=11, type=V, src=C("Web_Clip_Ground_00278171.mp4"), start=1.2, w=5.6),
    ]),
    (70.0, [
        dict(id=12, type=V, src=N("IMG_5758.MP4"), start=6.0, w=5.0, grade="phone"),
        dict(id=13, type=V, src=N("IMG_4240.MP4"), start=6.0, w=4.0, grade="phone"),
        dict(id=14, type="trip", src=[N("IMG_6221.MP4"), N("IMG_7732.MP4"), N("IMG_6203.MP4")],
             start=[0.5, 0.5, 0.5], w=3.4, grade="phone"),
        dict(id=15, type=V, src=C("Web_Clip_Ground_00274963.mp4"), start=1.0, w=3.0),
        dict(id=16, type=V, src=C("Web_Clip_Ground_00276589.mp4"), start=1.5, w=3.6),
        dict(id=17, type=V, src=C("Web_Clip_Drone_012.mp4"), start=4.0, w=4.6),
    ]),
    (78.0, [
        dict(id=18, type=V, src=C("Web_Clip_Drone_014.mp4"), start=2.0, w=5.0),
        dict(id=19, type=V, src=C("Web_Clip_Drone_03.mp4"), start=3.0, w=3.2),
    ]),
    (126.0, [
        dict(id=20, type=V, src=C("Web_Clip_Ground_00283067.mp4"), start=1.0, w=3.4),
        dict(id=21, type=V, src=C("Web_Clip_Ground_00281759.mp4"), start=1.0, w=3.0),
        dict(id=22, type=V, src=C("Web_Clip_Ground_00282208.mp4"), start=0.5, w=3.0),
        dict(id=23, type=V, src=C("Web_Clip_Ground_00282406.mp4"), start=2.0, w=4.0),
        dict(id=24, type=V, src=C("Web_Clip_Ground_00281513.mp4"), start=0.3, w=2.8),
        dict(id=26, type="ai", src=os.path.join(AI, "dining.mp4"),
             fallback=dict(type=S, src=N("IMG_25.JPEG"), kb="in"), w=3.4),
        dict(id=28, type="ai", src=os.path.join(AI, "platter.mp4"),
             fallback=dict(type=S, src=B("IMG_0778.jpg"), kb="in"), w=2.6),
        dict(id=29, type=S, src=WP("DSC01767.jpg"), kb="out", w=3.0),
        dict(id=30, type=V, src=C("Web_Clip_Ground_00280516.mp4"), start=4.0, w=3.6),
        dict(id=31, type=V, src=C("Web_Clip_Ground_00276247.mp4"), start=1.0, w=4.0),
        dict(id=32, type=S, src=N("IMG_17.JPG"), kb="out", w=3.0),
        dict(id=33, type=V, src=C("Web_Clip_Drone_011.mp4"), start=0.5, w=3.4),
        dict(id=34, type=V, src=C("Web_Clip_Drone_02.mp4"), start=0.5, w=4.0),
    ]),
    (153.5, [
        dict(id=35, type="ai", src=os.path.join(AI, "sunset.mp4"),
             fallback=dict(type=S, src=N("IMG_4994.JPEG"), kb="up"), w=4.6),
        dict(id=36, type="ai", src=os.path.join(AI, "sunset2.mp4"),
             fallback=dict(type=S, src=N("IMG_5017.JPEG"), kb="panlr"), w=3.0),
        dict(id=37, type=V, src=C("Web_Clip_Ground_00278960.mp4"), start=2.0, w=4.6),
        dict(id=38, type="ai", src=os.path.join(AI, "firepit.mp4"),
             fallback=dict(type=S, src=N("IMG_19.JPG"), kb="in"), w=3.6),
        dict(id=39, type="ai", src=os.path.join(AI, "moon.mp4"),
             fallback=dict(type=S, src=N("IMG_0503.JPEG"), kb="in"), w=4.0),
        dict(id=40, type="ai", src=os.path.join(AI, "aurora1.mp4"),
             fallback=dict(type=S, src=N("IMG_0903.JPG"), kb="in"), w=4.9),
        dict(id=41, type="ai", src=os.path.join(AI, "aurora2.mp4"),
             fallback=dict(type=S, src=N("IMG_0902.JPG"), kb="panlr"), w=4.9),
    ]),
]
# xfade overlaps consumed at junctions (see assemble): total raw = SONG_END + sum(XF)
XF = dict(j1=0.8, j2=1.0, j3=0.7, j4=0.7, j5=0.9)  # 34|35, 41|c1, c1|c2, c2|c3, c3|c4
CARDS_RAW = 153.5  # cards fill SONG_END-153.5 plus overlaps j2..j5

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAIL:", " ".join(cmd)[:400])
        print(r.stderr[-1500:])
        sys.exit(1)

def enc_args(out, dur):
    return ["-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17",
            "-preset", "medium", "-t", f"{dur:.3f}", "-an", "-y", out]

def src_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip())

def render_vid(shot, dur, out):
    start = shot["start"]
    avail = src_dur(shot["src"]) - start
    pre = ""
    if avail < dur + 0.05:
        start = 0.0
        avail = src_dur(shot["src"])
        f = dur / max(avail - 0.05, 0.1)
        if f > 1.0:
            pre = f"setpts=PTS*{f:.5f},"
    vf = f"{pre}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
    if shot.get("grade") == "phone":
        vf += ",eq=saturation=1.06:contrast=1.03,unsharp=5:5:0.4:5:5:0.0"
    run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", shot["src"],
         "-vf", vf] + enc_args(out, dur))

HH_POST = (",scale=2020:1136,"
           "crop=1920:1080:"
           "x='50+9*sin(2*PI*t*0.5)+3*sin(2*PI*t*2.1+1.3)':"
           "y='28+11*sin(2*PI*t*0.37+0.8)+3*sin(2*PI*t*1.7)'")
SWAY_POST = (",scale=2020:1136,"
             "crop=1920:1080:"
             "x='50+16*sin(2*PI*t*0.16)':"
             "y='28+10*sin(2*PI*t*0.11+1.1)'")

def render_still(shot, dur, out):
    frames = max(2, round(dur * FPS))
    kb = shot.get("kb", "in")
    hh = HH_POST if shot.get("hh") else (SWAY_POST if shot.get("sway") else "")
    src = shot["src"]
    if kb in ("up", "down"):
        # vertical pan across middle band via animated crop
        rng = 0.55
        expr_t = f"(t/{dur:.3f})"
        pos = expr_t if kb == "up" else f"(1-{expr_t})"
        vf = (f"scale={W}:-2,"
              f"crop={W}:{H}:0:'(ih-{H})*(0.5-{rng}/2+{rng}*{pos})',"
              f"fps={FPS}{hh}")
        run(["ffmpeg", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", src,
             "-vf", vf] + enc_args(out, dur))
        return
    # zoom / horizontal pan on oversized canvas
    IW, IH = 3840, 2160
    d = frames
    if kb == "in":
        z = f"1.001+0.11*on/{d-1}"; x = "(iw-iw/zoom)/2"; y = "(ih-ih/zoom)/2"
    elif kb == "out":
        z = f"1.111-0.11*on/{d-1}"; x = "(iw-iw/zoom)/2"; y = "(ih-ih/zoom)/2"
    elif kb == "panlr":
        z = "1.09"; x = f"(iw-iw/zoom)*on/{d-1}"; y = "(ih-ih/zoom)/2"
    else:  # panrl
        z = "1.09"; x = f"(iw-iw/zoom)*(1-on/{d-1})"; y = "(ih-ih/zoom)/2"
    vf = (f"scale={IW}:{IH}:force_original_aspect_ratio=increase,crop={IW}:{IH},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={d}:s={W}x{H}:fps={FPS}{hh}")
    run(["ffmpeg", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", src,
         "-vf", vf] + enc_args(out, dur))

def render_trip(shot, dur, out):
    ins, filts = [], []
    speeds = shot.get("speed", [1.0] * len(shot["src"]))
    for i, (s, st, sp) in enumerate(zip(shot["src"], shot["start"], speeds)):
        ins += ["-ss", str(st), "-i", s]
        pre = f"setpts=PTS/{sp:.4f}," if sp != 1.0 else ""
        filts.append(f"[{i}:v]{pre}scale=642:-2,crop=640:{H},fps={FPS},"
                     f"eq=saturation=1.06:contrast=1.03[v{i}]")
    fc = ";".join(filts) + f";[v0][v1][v2]hstack=3,scale={W}:{H}[v]"
    run(["ffmpeg", "-v", "error"] + ins + ["-filter_complex", fc, "-map", "[v]"]
        + enc_args(out, dur))

AI_YBIAS = {"sunset": 0.62, "aurora1": 0.60, "aurora2": 0.50, "moon": 0.55,
            "sunset2": 0.50, "platter": 0.50, "map": 0.50, "firepit": 0.50, "dining": 0.50}

def render_ai(shot, dur, out):
    src = shot["src"]
    base = os.path.basename(src).replace(".mp4", "")
    up = src.replace(".mp4", "_2k.mp4")
    if os.path.exists(up):
        src = up
    if os.path.exists(src):
        yb = AI_YBIAS.get(base, 0.5)
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:'(iw-ow)/2':'(ih-oh)*{yb}',fps={FPS}")
        if base == "platter":
            # extend the clip's pull-back: start punched in 12%, settle to full frame
            vf += (f",crop=w='iw/(1.12-0.12*min(t/{dur:.3f},1))'"
                   f":h='ih/(1.12-0.12*min(t/{dur:.3f},1))'"
                   f":x='(iw-ow)/2':y='(ih-oh)/2',scale={W}:{H}")
        run(["ffmpeg", "-v", "error", "-i", src, "-vf", vf] + enc_args(out, dur))
    else:
        fb = dict(shot["fallback"]); fb["id"] = shot["id"]
        render_still(fb, dur, out)

def main():
    only = set(int(a) for a in sys.argv[1:]) if len(sys.argv) > 1 else None
    t = 0.0
    timeline = []  # (id, final_start, dur)
    prev_end = 0.0
    for act_end, shots in ACTS:
        total_w = sum(s["w"] for s in shots)
        span = act_end - prev_end
        cum = prev_end
        bounds = []
        for s in shots[:-1]:
            cum += s["w"] / total_w * span
            bounds.append(snap(cum))
        starts = [prev_end] + bounds
        ends = bounds + [snap(act_end) if act_end != ACTS[-1][0] else act_end]
        for s, st, en in zip(shots, starts, ends):
            dur = max(1.2, en - st)
            timeline.append((s["id"], st, dur, s))
        prev_end = ends[-1]
    with open(os.path.join(BASE, "work/timeline.json"), "w") as f:
        json.dump([(i, round(st, 3), round(d, 3)) for i, st, d, _ in timeline], f, indent=0)
    for i, st, dur, s in timeline:
        if only and i not in only:
            continue
        out = os.path.join(SEG, f"{i:03d}.mp4")
        print(f"[{i:03d}] {s['type']} start@{st:.2f} dur={dur:.2f}")
        if s["type"] == V: render_vid(s, dur, out)
        elif s["type"] == S: render_still(s, dur, out)
        elif s["type"] == "trip": render_trip(s, dur, out)
        elif s["type"] == "ai": render_ai(s, dur, out)
    print("segments done; last shot ends", prev_end)

if __name__ == "__main__":
    main()
