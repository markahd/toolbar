#!/usr/bin/env python3
"""Generate one image with GPT Image via OpenRouter, optionally with reference images.

Usage:
  python3 scripts/make_image.py OUT.png "prompt" [--ref ref1.png --ref ref2.png]
         [--aspect 16:9] [--quality low] [--model openai/gpt-image-2]
Prints the USD cost OpenRouter reports for the call.
"""
import argparse, base64, os, pathlib, sys
import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
KEY = os.getenv("OPENROUTER_API_KEY", "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("prompt")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--quality", default="low")
    ap.add_argument("--model", default="openai/gpt-image-2")
    a = ap.parse_args()
    body = {"model": a.model, "prompt": a.prompt, "n": 1, "quality": a.quality,
            "aspect_ratio": a.aspect, "output_format": "png"}
    if a.ref:
        body["input_references"] = [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," +
             base64.b64encode(pathlib.Path(r).read_bytes()).decode()}} for r in a.ref]
    r = requests.post("https://openrouter.ai/api/v1/images", json=body, timeout=600,
                      headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    if r.status_code != 200:
        raise SystemExit(f"error {r.status_code}: {r.text[:500]}")
    j = r.json()
    pathlib.Path(a.out).write_bytes(base64.b64decode(j["data"][0]["b64_json"]))
    u = j.get("usage", {})
    print(f"wrote {a.out} | cost ${u.get('cost')} | tokens {u.get('completion_tokens')}")


if __name__ == "__main__":
    main()
