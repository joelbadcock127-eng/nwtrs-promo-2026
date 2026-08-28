#!/usr/bin/env python3
"""NWTRS-website cut: film + aurora + host-announcement card + centred logo card.

No offer card, no booking card, no QR, no promo code. Ends ~165.7s so the
3-second music fade sits in the instrumental gap after 'stillness settling
everywhere' (ends ~163.0) and completes before 'time loosens' (starts 165.76).
Reuses the existing r1/r2 intermediates and title PNGs; festival outputs are
not touched.
"""
import json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(BASE, "segments")
GOLD = "#CCB268"
F5 = os.path.join(BASE, "fonts/Montserrat-500.ttf")
TARGET_END = 165.70  # audio+video end; vocal re-entry at 165.76

def run(cmd, tag):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL[{tag}]:", r.stderr[-1200:])
        sys.exit(1)

def dur_of(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip())

def main():
    # ---------- centred web end card (logo + place line + URL only) ----------
    logo = os.path.join(BASE, "cards/logo_w.png")
    run(["convert", os.path.join(BASE, "cards/bg_dark.png"),
         logo, "-gravity", "north", "-geometry", "+0+330", "-composite",
         "-font", F5, "-pointsize", "34", "-kerning", "14", "-fill", "#D9D4C8",
         "-gravity", "north", "-annotate", "+0+652", "BAKERS BEACH · TASMANIA",
         "-font", F5, "-pointsize", "30", "-kerning", "8", "-fill", GOLD,
         "-annotate", "+0+728", "TENFIFTYBAKERS.COM.AU",
         os.path.join(BASE, "cards/card4web.png")], "card4web")

    r1 = os.path.join(BASE, "work/r1.mp4")
    r2 = os.path.join(BASE, "work/r2.mp4")
    c1 = os.path.join(SEG, "042.mp4")
    XF = [0.8, 1.0, 0.7]
    d0, d1, d2 = dur_of(r1), dur_of(r2), dur_of(c1)
    base_len = d0 + d1 + d2 - XF[0] - XF[1]
    c4dur = round(TARGET_END - (base_len - XF[2]), 3)
    print(f"parts {d0:.2f} {d1:.2f} {d2:.2f} -> end card {c4dur:.2f}s")
    assert 5.5 <= c4dur <= 7.5, "end card duration out of range"

    c4 = os.path.join(SEG, "045w.mp4")
    fade_st = c4dur - 1.7
    run(["ffmpeg", "-v", "error", "-loop", "1", "-framerate", "24",
         "-i", os.path.join(BASE, "cards/card4web.png"),
         "-vf", f"scale=1920:1080,fps=24,fade=t=out:st={fade_st:.2f}:d=1.6",
         "-r", "24", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-t", f"{c4dur:.3f}", "-an", "-y", c4], "endcard-seg")

    # ---------- xfade join ----------
    parts = [r1, r2, c1, c4]
    durs = [d0, d1, d2, dur_of(c4)]
    fc, off, cur = [], 0.0, "[0:v]"
    for k in range(1, len(parts)):
        off = off + durs[k - 1] - XF[k - 1]
        outl = f"[x{k}]"
        fc.append(f"{cur}[{k}:v]xfade=transition=fade:duration={XF[k-1]}:offset={off:.3f}{outl}")
        cur = outl
    joined = os.path.join(BASE, "work/joined_web.mp4")
    run(["ffmpeg", "-v", "error"] + sum([["-i", p] for p in parts], []) +
        ["-filter_complex", ";".join(fc), "-map", cur,
         "-r", "24", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-an", "-y", joined], "xfade")
    total = dur_of(joined)
    print("joined_web dur:", total)

    # ---------- overlays: reuse existing title PNGs, same timings, NO QR ----------
    tl = json.load(open(os.path.join(BASE, "work/timeline.json")))
    starts = {i: st for i, st, d in tl}

    def ftime(shot, offset):
        t = starts[shot] + offset
        if shot >= 35:
            t -= XF[0]
        return t

    TT = [(0, 2.2, 5.2), (1, 0.10, 3.2), (3, 0.20, 3.6), (8, 0.15, 2.9),
          (11, 0.60, 4.0), (12, 0.40, 4.0), (18, 0.50, 6.4), (20, 0.20, 3.6),
          (29, 0.20, 3.4), (31, 0.20, 3.4), (37, 0.30, 3.6), (40, 0.70, 6.0)]
    ITEMS = [(ftime(s, o), d) for s, o, d in TT]
    ITEMS += [(24.60, 4.4), (36.20, 5.2), (54.50, 4.4)]  # lyric captions

    tdir = os.path.join(BASE, "titles")
    ins = ["-i", joined]
    fc2, cur = [], "[0:v]"
    for n, (t0, tdur) in enumerate(ITEMS):
        png = os.path.join(tdir, f"t{n:02d}.png")
        assert os.path.exists(png), png
        t1 = t0 + tdur
        ins += ["-loop", "1", "-t", str(int(total) + 5), "-i", png]
        idx = n + 1
        fc2.append(f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.7:alpha=1,"
                   f"fade=t=out:st={t1-0.7:.2f}:d=0.7:alpha=1,setpts=PTS-STARTPTS[ov{n}]")
        fc2.append(f"{cur}[ov{n}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[o{n}]")
        cur = f"[o{n}]"
    # corner URL, same window as the festival cut
    u0 = ftime(18, 0.5)
    u1 = ftime(41, 0.0) + 4.1
    nu = len(ITEMS)
    ins += ["-loop", "1", "-t", str(int(total) + 5), "-i", os.path.join(tdir, "url.png")]
    fc2.append(f"[{nu+1}:v]format=rgba,colorchannelmixer=aa=0.62,"
               f"fade=t=in:st={u0:.2f}:d=1.0:alpha=1,"
               f"fade=t=out:st={u1-1.0:.2f}:d=1.0:alpha=1,setpts=PTS-STARTPTS[ovu]")
    fc2.append(f"{cur}[ovu]overlay=0:0:enable='between(t,{u0:.2f},{u1:.2f})'[ou]")
    fc2.append("[ou]fade=t=in:st=0:d=1.2[vout]")
    titled = os.path.join(BASE, "work/titled_web.mp4")
    run(["ffmpeg", "-v", "error"] + ins +
        ["-filter_complex", ";".join(fc2), "-map", "[vout]",
         "-r", "24", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-an", "-y", titled], "titles")

    # ---------- mux with 3s music fade ending with the video ----------
    fade0 = total - 3.0
    final = os.path.join(BASE, "out/TenFifty_NWTRS_Web.mp4")
    run(["ffmpeg", "-v", "error", "-i", titled, "-i", os.path.join(BASE, "work/song.mp3"),
         "-filter_complex", f"[1:a]afade=t=out:st={fade0:.2f}:d=3.0,aresample=48000[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-t", f"{total:.3f}", "-movflags", "+faststart", "-y", final], "mux")
    print("WEB FINAL:", final, dur_of(final))

if __name__ == "__main__":
    main()
