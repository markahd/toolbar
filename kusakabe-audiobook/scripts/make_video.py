#!/usr/bin/env python3
"""Generate one video clip via OpenRouter's Video API (async job, polled until done).

Usage:
  python3 scripts/make_video.py OUT.mp4 "prompt" [--ref ref.png] [--first-frame img.png]
         [--duration 10] [--resolution 720p] [--aspect 16:9] [--model x-ai/grok-imagine-video-1.5-lite]
Prints the USD cost OpenRouter reports.
"""
import argparse, base64, os, pathlib, time
import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
API = "https://openrouter.ai/api/v1/videos"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def data_url(path):
    p = pathlib.Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("prompt")
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--first-frame")
    ap.add_argument("--duration", type=int, default=10)
    ap.add_argument("--resolution", default="720p")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--model", default="x-ai/grok-imagine-video-1.5-lite")
    a = ap.parse_args()
    body = {"model": a.model, "prompt": a.prompt, "duration": a.duration,
            "resolution": a.resolution, "aspect_ratio": a.aspect}
    if a.ref:
        body["input_references"] = [{"type": "image_url", "image_url": {"url": data_url(r)}} for r in a.ref]
    if a.first_frame:
        body["frame_images"] = [{"type": "image_url", "image_url": {"url": data_url(a.first_frame)},
                                 "frame_type": "first_frame"}]
    r = requests.post(API, json=body, headers=H, timeout=120)
    if r.status_code not in (200, 202):
        raise SystemExit(f"submit error {r.status_code}: {r.text[:500]}")
    job = r.json()["id"]
    while True:
        time.sleep(8)
        j = requests.get(f"{API}/{job}", headers=H, timeout=60).json()
        if j.get("status") in ("completed", "failed", "cancelled", "expired"):
            break
    if j["status"] != "completed":
        raise SystemExit(f"job {j['status']}: {j.get('error')}")
    v = requests.get(f"{API}/{job}/content", headers=H, timeout=300)
    pathlib.Path(a.out).write_bytes(v.content)
    print(f"wrote {a.out} | cost ${j.get('usage', {}).get('cost')}")


if __name__ == "__main__":
    main()
