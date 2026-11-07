#!/usr/bin/env python3
"""Join final/ch01.mp3 ... final/ch25.mp3 into one audiobook file with chapter markers.

Usage: python3 scripts/assemble_book.py [--mp3]
Output: final/The_Circle_That_Doesnt_Need_a_Name.m4b (AAC, chapter markers, 64 kbps)
        or .mp3 with --mp3 (96 kbps, chapter markers as ID3 CHAP frames)
"""
import re, subprocess, sys, pathlib, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FINAL = ROOT / "final"
TITLE = "The Circle That Doesn't Need a Name"


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def chapter_title(n):
    md = (ROOT / "chapters" / f"ch{n:02d}.md").read_text().splitlines()[0]
    return re.sub(r"^#\s*", "", md).strip()


def main(mp3=False):
    files = [FINAL / f"ch{n:02d}.mp3" for n in range(1, 26)]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise SystemExit("missing: " + ", ".join(missing))
    meta = [";FFMETADATA1", f"title={TITLE}", "album=" + TITLE, "artist=Read by Sarah (Fish Audio)",
            "genre=Audiobook", ""]
    t = 0
    for n, f in enumerate(files, 1):
        d = int(dur(f) * 1000)
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={t}", f"END={t + d}",
                 "title=" + chapter_title(n).replace("=", "\\=").replace(";", "\\;"), ""]
        t += d
    with tempfile.TemporaryDirectory() as tmp:
        lst = pathlib.Path(tmp) / "list.txt"
        lst.write_text("".join(f"file '{f}'\n" for f in files))
        mf = pathlib.Path(tmp) / "meta.txt"
        mf.write_text("\n".join(meta))
        name = "The_Circle_That_Doesnt_Need_a_Name"
        if mp3:
            out = FINAL / f"{name}.mp3"
            codec = ["-c:a", "libmp3lame", "-b:a", "96k", "-id3v2_version", "3"]
        else:
            out = FINAL / f"{name}.m4b"
            codec = ["-c:a", "aac", "-b:a", "64k", "-f", "mp4"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-i", str(mf), "-map_metadata", "1", "-map_chapters", "1", "-vn", *codec, str(out)],
                       check=True)
    print(f"{out} | {t/3600000:.2f} h | {out.stat().st_size/1e6:.0f} MB")


if __name__ == "__main__":
    main("--mp3" in sys.argv)
