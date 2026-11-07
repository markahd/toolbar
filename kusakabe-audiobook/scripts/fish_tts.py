#!/usr/bin/env python3
"""Generate audiobook audio from full_book_tts/*.txt with Fish Audio.

Usage:
  python3 scripts/fish_tts.py                # every chapter not yet generated
  python3 scripts/fish_tts.py ch01 ch02      # specific chapters
  python3 scripts/fish_tts.py --force ch01   # regenerate

Settings come from .env (see .env.example). Output: audio/chNN.mp3
"""
import os, re, sys, time, pathlib
import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_URL = "https://api.fish.audio/v1/tts"
KEY = os.getenv("FISH_API_KEY", "").strip()
VOICE = os.getenv("FISH_VOICE_ID", "").strip()
MODEL = os.getenv("FISH_MODEL", "s1").strip()
FMT = os.getenv("FISH_FORMAT", "mp3").strip()
MAX_CHARS = int(os.getenv("FISH_MAX_CHARS", "1800"))


def chunks(text, limit=MAX_CHARS):
    """Split at paragraph boundaries; split an oversized paragraph at sentence ends."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces = []
    for p in paras:
        if len(p) <= limit:
            pieces.append(p)
            continue
        cur = ""
        for s in re.split(r"(?<=[.!?])\s+", p):
            if cur and len(cur) + len(s) + 1 > limit:
                pieces.append(cur)
                cur = s
            else:
                cur = f"{cur} {s}".strip()
        if cur:
            pieces.append(cur)
    out, cur = [], ""
    for p in pieces:
        if cur and len(cur) + len(p) + 2 > limit:
            out.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        out.append(cur)
    return out


def tts(text):
    body = {"text": text, "format": FMT, "normalize": True, "latency": "normal"}
    if VOICE:
        body["reference_id"] = VOICE
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "model": MODEL}
    for attempt in range(5):
        r = requests.post(API_URL, json=body, headers=headers, timeout=300)
        if r.status_code == 200:
            return r.content
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** (attempt + 1))
            continue
        raise SystemExit(f"Fish Audio error {r.status_code}: {r.text[:500]}")
    raise SystemExit("Fish Audio: too many retries")


def main(argv):
    if not KEY:
        raise SystemExit("FISH_API_KEY is empty. Fill in .env first.")
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    src = sorted((ROOT / "full_book_tts").glob("ch*_tts.txt"))
    if wanted:
        src = [p for p in src if p.name.split("_")[0] in wanted]
    outdir = ROOT / "audio"
    outdir.mkdir(exist_ok=True)
    for path in src:
        name = path.name.split("_")[0]
        out = outdir / f"{name}.{FMT}"
        if out.exists() and not force:
            print(f"skip {name} (exists)")
            continue
        parts = chunks(path.read_text(encoding="utf-8"))
        print(f"{name}: {len(parts)} requests")
        tmp = out.with_suffix(out.suffix + ".part")
        with open(tmp, "wb") as f:
            for i, part in enumerate(parts, 1):
                f.write(tts(part))  # MP3 frames concatenate cleanly
                print(f"  {i}/{len(parts)}", flush=True)
        tmp.rename(out)
        print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
