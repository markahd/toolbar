#!/usr/bin/env python3
"""Generate audiobook audio from full_book_tts/*.txt with Fish Audio Drama 3,
called through OpenRouter's text-to-speech endpoint.

Usage:
  python3 scripts/make_audio.py                # every chapter not yet generated
  python3 scripts/make_audio.py ch01 ch02      # specific chapters
  python3 scripts/make_audio.py --force ch01   # regenerate

Settings come from .env (see .env.example). Output: audio/chNN.mp3
"""
import os, re, sys, time, json, pathlib, subprocess, tempfile
import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_URL = "https://openrouter.ai/api/v1/audio/speech"
KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL = os.getenv("TTS_MODEL", "fish-audio/drama-3").strip()
# Fish Audio reference_id; default is "Sarah" (Fish Official). Empty string = model default.
VOICE = os.getenv("TTS_VOICE", "933563129e564b19a115bedd57b7406a").strip()
FMT = "mp3"
# Delivery direction sent to Drama 3 (OpenRouter prepends it as a [direction]).
INSTRUCTIONS = os.getenv("TTS_INSTRUCTIONS", "warm, gentle, intimate audiobook narration, unhurried, a soft smile in the voice").strip()
MAX_CHARS = int(os.getenv("TTS_MAX_CHARS", "1800"))


def chunks(text, limit=MAX_CHARS, breaks=()):
    """Split at paragraph boundaries; split an oversized paragraph at sentence ends.
    A paragraph starting with any string in `breaks` always starts a new chunk
    (music cues use this so they land on an exact sentence)."""
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
        forced = any(p.startswith(b) for b in breaks)
        if cur and (forced or len(cur) + len(p) + 2 > limit):
            out.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        out.append(cur)
    return out


def tts(text):
    # Drama 3 reads [square brackets] as stage directions; the TTS files contain none.
    body = {"model": MODEL, "input": text, "response_format": FMT}
    if VOICE:
        body["voice"] = VOICE
    if INSTRUCTIONS:
        body["instructions"] = INSTRUCTIONS
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    for attempt in range(5):
        r = requests.post(API_URL, json=body, headers=headers, timeout=300)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("audio"):
            return r.content
        if r.status_code in (429, 500, 502, 503, 504, 524, 529):
            time.sleep(2 ** (attempt + 1))
            continue
        raise SystemExit(f"TTS error {r.status_code}: {r.text[:500]}")
    raise SystemExit("TTS: too many retries")


def duration(data):
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        f.write(data); f.flush()
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", f.name], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def cue_breaks(name):
    path = ROOT / "music_cues.json"
    if not path.exists():
        return ()
    cues = json.loads(path.read_text()).get("chapters", {}).get(name, [])
    return tuple(a for c in cues for a in (c.get("from"), c.get("to")) if a)


def main(argv):
    if not KEY:
        raise SystemExit("OPENROUTER_API_KEY is empty. Fill in .env first.")
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
        parts = chunks(path.read_text(encoding="utf-8"), breaks=cue_breaks(name))
        print(f"{name}: {len(parts)} requests")
        tmp = out.with_suffix(out.suffix + ".part")
        timing, t = [], 0.0
        with open(tmp, "wb") as f:
            for i, part in enumerate(parts, 1):
                data = tts(part)
                f.write(data)  # MP3 frames concatenate cleanly
                d = duration(data)
                timing.append({"start": round(t, 3), "dur": round(d, 3), "text": part[:80]})
                t += d
                print(f"  {i}/{len(parts)}", flush=True)
        tmp.rename(out)
        # Chunk start times, used by mix_audio.py to place music cues
        (outdir / f"{name}.timing.json").write_text(json.dumps(timing, indent=1))
        print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
