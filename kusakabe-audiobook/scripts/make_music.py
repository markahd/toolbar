#!/usr/bin/env python3
"""Generate an original instrumental track with Google Lyria 3 via OpenRouter.

Usage: python3 scripts/make_music.py OUT.mp3 "prompt text" [--clip]
"""
import base64, json, os, sys, pathlib
import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
KEY = os.getenv("OPENROUTER_API_KEY", "").strip()


def main(out, prompt, clip=False):
    model = "google/lyria-3-clip-preview" if clip else "google/lyria-3-pro-preview"
    body = {"model": model, "stream": True, "modalities": ["text", "audio"],
            "audio": {"format": "mp3"}, "messages": [{"role": "user", "content": prompt}]}
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, stream=True, timeout=600,
                      headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    if r.status_code != 200:
        raise SystemExit(f"error {r.status_code}: {r.text[:500]}")
    buf, text = [], []
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        ev = json.loads(data)
        if "error" in ev:
            raise SystemExit(f"stream error: {ev['error']}")
        for ch in ev.get("choices", []):
            d = ch.get("delta", {})
            a = d.get("audio") or {}
            if a.get("data"):
                buf.append(a["data"])
            if d.get("content"):
                text.append(d["content"])
    if not buf:
        raise SystemExit("no audio returned; text: " + "".join(text)[:300])
    pathlib.Path(out).write_bytes(b"".join(base64.b64decode(b) for b in buf))
    print("wrote", out, "| text:", "".join(text)[:200])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--clip" in sys.argv)
