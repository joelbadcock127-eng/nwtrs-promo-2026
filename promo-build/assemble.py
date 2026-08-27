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
        concat([i for i in range(0, 35) if i not in (25, 27)], r1)
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
        (0, 2.2, 5.2, "open", ["TASMANIA PRESENTS", "TEN FIFTY BAKERS"]),
        (1, 0.10, 3.2, "lt", ["1,137 PRIVATE ACRES"]),
        (3, 0.20, 3.6, "lt", ["23 KM OF WILD TRAILS"]),
        (8, 0.15, 2.9, "lt", ["SWAMP · FOREST · COAST"]),
        (11, 0.60, 4.0, "lt", ["YOU WON'T RUN ALONE"]),
        (12, 0.40, 4.0, "lt", ["TRAIL RUNNING COUNTRY"]),
        (18, 0.50, 6.4, "big", ["THEN COME HOME", "TO TEN FIFTY"]),
        (20, 0.20, 3.6, "lt", ["OFF-GRID LUXURY · SLEEPS 10"]),
        (29, 0.20, 3.4, "lt", ["WOOD-FIRED SAUNA"]),
        (31, 0.20, 3.4, "lt", ["OUTDOOR BATHS"]),
        (37, 0.30, 3.6, "lt", ["EVENINGS BY THE FIRE"]),
        (40, 0.70, 6.0, "lt", ["SOME NIGHTS, THE SKY JOINS IN"]),
    ]
    # lyric captions at the exact sung times (absolute seconds, from transcription)
    LYR = [
        (24.60, 4.4, "“morning light through tall gum trees”"),
        (36.20, 5.2, "“no clock, no place I need to be”"),
        (54.50, 4.4, "“nothing here but sky and land”"),
    ]
    R2_START = starts[35]
    def ftime(shot, offset):
        t = starts[shot] + offset
        if shot >= 35:
            t -= XF[0]
        return t

    # unify shot-keyed titles and absolute-time lyric captions
    ITEMS = [(ftime(sid, offs), tdur, style, lines) for sid, offs, tdur, style, lines in T]
    ITEMS += [(t0, d, "lyr", [txt]) for t0, d, txt in LYR]

    # render title PNGs
    tdir = os.path.join(BASE, "titles"); os.makedirs(tdir, exist_ok=True)
    for n, (t0abs, tdur, style, lines) in enumerate(ITEMS):
        png = os.path.join(tdir, f"t{n:02d}.png")
        if style == "open":
            cmd = ["convert", "-size", "1920x1080", "xc:none",
                   "-font", F6, "-pointsize", "34", "-kerning", "16",
                   "-gravity", "center",
                   "-fill", "#000000C0", "-annotate", "+2-87", lines[0],
                   "-fill", GOLD, "-annotate", "+0-90", lines[0],
                   "-font", F7, "-pointsize", "88", "-kerning", "10", "-fill", "white",
                   "-annotate", "+0+10", lines[1],
                   png]
        elif style == "big":
            cmd = ["convert", "-size", "1920x1080", "xc:none",
                   "-font", F7, "-pointsize", "84", "-kerning", "8",
                   "-fill", "white", "-gravity", "center",
                   "-annotate", "+0-285", lines[0],
                   "-font", F6, "-pointsize", "54", "-kerning", "14",
                   "-fill", "#000000C0", "-annotate", "+3-167", lines[1],
                   "-fill", GOLD, "-annotate", "+0-170", lines[1],
                   png]
        elif style == "lyr":
            cmd = ["convert", "-size", "1920x1080", "xc:none",
                   "-fill", GOLD, "-draw", "rectangle 122,944 202,948",
                   "-font", F5, "-pointsize", "40", "-kerning", "4",
                   "-fill", "#E4DFD2", "-gravity", "southwest",
                   "-annotate", "+120+70", lines[0],
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
        shadow = "95x8+0+4" if style in ("big", "open") else "80x6+0+3"
        run(["convert", png, "(", "+clone", "-background", "black", "-shadow", shadow, ")",
             "+swap", "-background", "none", "-layers", "merge", "+repage",
             "-resize", "1920x1080!", png], "title-shadow")

    ins = ["-i", joined]
    fc2, cur = [], "[0:v]"
    for n, (t0abs, tdur, style, lines) in enumerate(ITEMS):
        t0 = t0abs; t1 = t0 + tdur
        ins += ["-loop", "1", "-t", "190", "-i", os.path.join(tdir, f"t{n:02d}.png")]
        idx = n + 1
        fc2.append(
            f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.7:alpha=1,"
            f"fade=t=out:st={t1-0.7:.2f}:d=0.7:alpha=1,setpts=PTS-STARTPTS[ov{n}]")
        nxt = f"[o{n}]"
        fc2.append(f"{cur}[ov{n}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'{nxt}")
        cur = nxt
    # persistent corner URL through the house/night acts (bottom-right, subtle)
    urlpng = os.path.join(tdir, "url.png")
    run(["convert", "-size", "1920x1080", "xc:none",
         "-font", F6, "-pointsize", "27", "-kerning", "6",
         "-fill", "white", "-gravity", "southeast",
         "-annotate", "+96+64", "TENFIFTYBAKERS.COM.AU", urlpng], "url-png")
    run(["convert", urlpng, "(", "+clone", "-background", "black", "-shadow", "70x4+0+2", ")",
         "+swap", "-background", "none", "-layers", "merge", "+repage",
         "-resize", "1920x1080!", urlpng], "url-shadow")
    u0 = ftime(18, 0.5)
    u1 = ftime(41, 0.0) + 4.1
    nu = len(ITEMS)
    ins += ["-loop", "1", "-t", "190", "-i", urlpng]
    fc2.append(
        f"[{nu+1}:v]format=rgba,colorchannelmixer=aa=0.62,"
        f"fade=t=in:st={u0:.2f}:d=1.0:alpha=1,"
        f"fade=t=out:st={u1-1.0:.2f}:d=1.0:alpha=1,setpts=PTS-STARTPTS[ovu]")
    fc2.append(f"{cur}[ovu]overlay=0:0:enable='between(t,{u0:.2f},{u1:.2f})'[ou]")
    cur = "[ou]"
    # persistent QR from the offer card to the end of the video
    qrpng = os.path.join(tdir, "qr_corner.png")
    run(["convert", "-size", "1920x1080", "xc:none",
         "(", os.path.join(BASE, "cards/qr_card.png"), "-resize", "300x", ")",
         "-gravity", "south", "-geometry", "+0+30", "-composite", qrpng], "qr-corner")
    pdurs = [dur_of(p) for p in [r1, r2] +
             [f"{SEG}/{i:03d}.mp4" for i in (42, 43)]]
    q0 = pdurs[0] + pdurs[1] + pdurs[2] - (XF[0] + XF[1] + XF[2]) + 0.4
    nq = len(ITEMS) + 1
    ins += ["-loop", "1", "-t", "190", "-i", qrpng]
    fc2.append(
        f"[{nq+1}:v]format=rgba,fade=t=in:st={q0:.2f}:d=0.8:alpha=1,"
        f"fade=t=out:st=182.90:d=1.6:alpha=1,setpts=PTS-STARTPTS[ovq]")
    fc2.append(f"{cur}[ovq]overlay=0:0:enable='between(t,{q0:.2f},184.92)'[oq]")
    cur = "[oq]"
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
