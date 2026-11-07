#!/usr/bin/env python3
"""Lay background music under narrated chapters, following music_cues.json.

Usage:
  python3 scripts/mix_audio.py              # every chapter with a voice track
  python3 scripts/mix_audio.py ch05 ch16    # specific chapters

Inputs:  audio/chNN.mp3 + audio/chNN.timing.json (from make_audio.py),
         music files named in music_cues.json "tracks" (kept out of git).
Output:  final/chNN.mp3. Chapters with no cues are copied with loudness
         normalised only, so the whole book plays at one level.

Each cue: {"track": name, "from": text, "to": text or null, "swell": bool}
  from   the paragraph where the music fades in (must start a paragraph)
  to     the paragraph where it fades out; null = chapter end
  swell  at chapter end, raise the music after the last line and let it
         play out for about 20 seconds
"""
import json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
AUDIO, FINAL = ROOT / "audio", ROOT / "final"
CUES = json.loads((ROOT / "music_cues.json").read_text())

VOICE_LUFS = -16    # narration level
BED_LUFS = -31      # music under the voice: 15 LU below it
SWELL_GAIN = 2.6    # about +8 dB once the voice has finished
LEAD_IN = 3.0       # music fades in alone this long before its paragraph
TAIL = 22.0         # seconds of music after the last line when swelling


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def find(timing, anchor):
    for t in timing:
        if t["text"].startswith(anchor[:60]):
            return t["start"]
    raise SystemExit(f"cue anchor not found at a chunk start: {anchor!r}")


def mix(name):
    voice = AUDIO / f"{name}.mp3"
    cues = CUES["chapters"].get(name, [])
    FINAL.mkdir(exist_ok=True)
    out = FINAL / f"{name}.mp3"
    vlen = dur(voice)
    timing = json.loads((AUDIO / f"{name}.timing.json").read_text()) if cues else []
    swell = any(c.get("to") is None and c.get("swell") for c in cues)
    lead = max([LEAD_IN - find(timing, c["from"]) for c in cues] + [0.0])  # room before ch start
    total = lead + vlen + (TAIL if swell else 1.5)

    inputs = ["-i", str(voice)]
    graph = [f"[0:a]aresample=44100,loudnorm=I={VOICE_LUFS}:TP=-1.5:LRA=11,aresample=44100,"
             f"aformat=channel_layouts=stereo,adelay={int(lead*1000)}|{int(lead*1000)},"
             f"apad=whole_dur={total:.2f},asplit={len(cues)+1}" + "".join(f"[v{i}]" for i in range(len(cues)+1))]
    beds = []
    for i, c in enumerate(cues):
        track = ROOT / CUES["tracks"][c["track"]]["file"]
        offset = CUES["tracks"][c["track"]].get("offset", 0)
        start = lead + find(timing, c["from"]) - LEAD_IN
        end = lead + (find(timing, c["to"]) if c.get("to") else vlen)
        voice_end = lead + vlen
        if c.get("to") is None:
            end = total
        length = end - start
        inputs += ["-stream_loop", "-1", "-ss", str(offset), "-i", str(track)]
        vol = "1"
        if c.get("to") is None and c.get("swell"):
            ve = voice_end - start
            vol = f"if(lt(t,{ve:.2f}),1,min({SWELL_GAIN},1+{SWELL_GAIN-1}*(t-{ve:.2f})/4))"
        fade_out = 10.0 if c.get("to") is None else 6.0
        graph.append(
            f"[{i+1}:a]atrim=duration={length:.2f},asetpts=PTS-STARTPTS,aresample=44100,"
            f"aformat=channel_layouts=stereo,loudnorm=I={BED_LUFS}:TP=-8,aresample=44100,"
            f"volume='{vol}':eval=frame,afade=t=in:d=4,afade=t=out:st={max(0, length-fade_out):.2f}:d={fade_out},"
            f"adelay={int(start*1000)}|{int(start*1000)},apad=whole_dur={total:.2f}[m{i}]")
        graph.append(f"[m{i}][v{i+1}]sidechaincompress=threshold=0.03:ratio=4:attack=100:release=1500:knee=6[d{i}]")
        beds.append(f"[d{i}]")
    graph.append(f"[v0]{''.join(beds)}amix=inputs={len(beds)+1}:normalize=0:duration=first,alimiter=limit=0.95[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph),
                    "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "160k", str(out)], check=True)
    print(f"{name}: {len(cues)} cue(s) -> {out} ({dur(out)/60:.1f} min)")


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(p.stem for p in AUDIO.glob("ch??.mp3"))
    for n in names:
        mix(n)
