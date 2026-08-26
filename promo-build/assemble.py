#!/usr/bin/env python3
"""Assemble: concat runs -> xfade joins -> title overlays -> audio mux."""
import json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(BASE, "segments")
OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)
GOLD = "#CCB268"
F5 = os.path.join(BASE, "fonts/Montserrat-500.ttf")
F6 = os.path.join(BASE, "fonts/Montserrat-600.ttf")
F7 = os.path.join(BASE, "fonts/Montserrat-700.ttf")

XF = [0.8, 1.0, 0.7, 0.7, 0.9]  # R1|R2, R2|c1, c1|c2, c2|c3, c3|c4
CARD_DUR = [8.4, 9.9, 9.3, 7.92]

def run(cmd, tag=""):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL", tag, r.stderr[-2000:])
        sys.exit(1)

def dur_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip())

def concat(ids, out):
    lst = os.path.join(BASE, f"work/cc_{os.path.basename(out)}.txt")
    with open(lst, "w") as f:
        for i in ids:
            f.write(f"file '{SEG}/{i:03d}.mp4'\n")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", "-y", out], "concat")

def main():
    tl = json.load(open(os.path.join(BASE, "work/timeline.json")))
    starts = {i: st for i, st, d in tl}
    r1 = os.path.join(BASE, "work/r1.mp4"); r2 = os.path.join(BASE, "work/r2.mp4")
    joined = os.path.join(BASE, "work/joined.mp4")
    if not (os.path.exists(joined) and os.environ.get("SKIP_JOIN")):
        concat(list(range(0, 35)), r1)
        concat(list(range(35, 42)), r2)
        parts = [r1, r2] + [f"{SEG}/{i:03d}.mp4" for i in range(42, 46)]
        durs = [dur_of(p) for p in parts]
        print("part durations:", [round(d, 2) for d in durs])
        # xfade chain
        fc, off, cur = [], 0.0, "[0:v]"
        for k in range(1, len(parts)):
            off = off + durs[k-1] - XF[k-1]
            outl = f"[x{k}]"
            fc.append(f"{cur}[{k}:v]xfade=transition=fade:duration={XF[k-1]}:offset={off:.3f}{outl}")
            cur = outl
        fcs = ";".join(fc)
        run(["ffmpeg", "-v", "error"] + sum([["-i", p] for p in parts], []) +
            ["-filter_complex", fcs, "-map", cur.strip("[]").join(["[", "]"]),
             "-r", "24", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17",
             "-preset", "medium", "-an", "-y", joined], "xfade")
    print("joined dur:", dur_of(joined))

    # ---------------- titles ----------------
    # (shot_id, offset, dur, style, lines)
    T = [
        (0, 2.2, 5.2, "open", ["TEN FIFTY BAKERS PRESENTS", "BAKERS BEACH · TASMANIA"]),
        (1, 0.10, 3.2, "lt", ["1,100 PRIVATE ACRES"]),
        (3, 0.20, 3.6, "lt", ["23 KM OF WILD TRAILS"]),
        (9, 0.30, 3.6, "lt", ["FOREST · MOORLAND · COAST"]),
        (11, 0.60, 4.0, "lt", ["YOU WON'T RUN ALONE"]),
        (12, 0.40, 4.0, "lt", ["TRAIL RUNNING COUNTRY"]),
        (18, 0.50, 6.4, "big", ["THEN COME HOME", "TO TEN FIFTY"]),
        (20, 0.20, 3.6, "lt", ["OFF-GRID LUXURY · SLEEPS 10"]),
        (29, 0.20, 3.4, "lt", ["WOOD-FIRED SAUNA"]),
        (31, 0.20, 3.4, "lt", ["OUTDOOR BATHS"]),
        (37, 0.30, 3.6, "lt", ["EVENINGS BY THE FIRE"]),
        (40, 0.70, 6.0, "lt", ["SOME NIGHTS, THE SKY JOINS IN"]),
    ]
    R2_START = starts[35]
    def ftime(shot, offset):
        t = starts[shot] + offset
        if shot >= 35:
            t -= XF[0]
        return t

    # render title PNGs
    tdir = os.path.join(BASE, "titles"); os.makedirs(tdir, exist_ok=True)
    for n, (sid, offs, tdur, style, lines) in enumerate(T):
        png = os.path.join(tdir, f"t{n:02d}.png")
        if style == "open":
            cmd = ["convert", "-size", "1920x1080", "xc:none",
                   "-font", F6, "-pointsize", "34", "-kerning", "16",
                   "-fill", GOLD, "-gravity", "center",
                   "-annotate", "+0-90", lines[0],
                   "-font", F7, "-pointsize", "88", "-kerning", "10", "-fill", "white",
                   "-annotate", "+0+10", lines[1],
                   png]
        elif style == "big":
            cmd = ["convert", "-size", "1920x1080", "xc:none",
                   "-font", F7, "-pointsize", "84", "-kerning", "8",
                   "-fill", "white", "-gravity", "center",
                   "-annotate", "+0-285", lines[0],
                   "-font", F6, "-pointsize", "54", "-kerning", "14", "-fill", GOLD,
                   "-annotate", "+0-170", lines[1],
                   png]
        else:  # lower third
            cmd = ["convert", "-size", "1920x1080", "xc:none",
                   "-fill", GOLD, "-draw", "rectangle 120,868 240,873",
                   "-font", F6, "-pointsize", "52", "-kerning", "10",
                   "-fill", "white", "-gravity", "northwest",
                   "-annotate", "+120+900", lines[0],
                   png]
        # soft shadow for legibility
        run(cmd, "title-png")
        shadow = "85x7+0+4" if style == "big" else "70x5+0+3"
        run(["convert", png, "(", "+clone", "-background", "black", "-shadow", shadow, ")",
             "+swap", "-background", "none", "-layers", "merge", "+repage",
             "-resize", "1920x1080!", png], "title-shadow")

    ins = ["-i", joined]
    fc2, cur = [], "[0:v]"
    for n, (sid, offs, tdur, style, lines) in enumerate(T):
        t0 = ftime(sid, offs); t1 = t0 + tdur
        ins += ["-loop", "1", "-t", "190", "-i", os.path.join(tdir, f"t{n:02d}.png")]
        idx = n + 1
        fc2.append(
            f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.7:alpha=1,"
            f"fade=t=out:st={t1-0.7:.2f}:d=0.7:alpha=1,setpts=PTS-STARTPTS[ov{n}]")
        nxt = f"[o{n}]"
        fc2.append(f"{cur}[ov{n}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'{nxt}")
        cur = nxt
    fc2.append(f"{cur}fade=t=in:st=0:d=1.2[vout]")
    titled = os.path.join(BASE, "work/titled.mp4")
    run(["ffmpeg", "-v", "error"] + ins +
        ["-filter_complex", ";".join(fc2), "-map", "[vout]",
         "-r", "24", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-an", "-y", titled], "titles")

    # ---------------- audio mux ----------------
    final = os.path.join(OUT, "TenFifty_NWTRS_Promo.mp4")
    run(["ffmpeg", "-v", "error", "-i", titled, "-i", os.path.join(BASE, "work/song.mp3"),
         "-filter_complex", "[1:a]afade=t=out:st=183.2:d=1.7,aresample=48000[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-t", "184.92", "-movflags", "+faststart", "-y", final], "mux")
    print("FINAL:", final, dur_of(final))

if __name__ == "__main__":
    main()
