#!/usr/bin/env python3
"""Mechanical checks for chapters. Usage: python3 scripts/check_chapter.py ch01 [ch02 ...]"""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
NUMS = ["zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
        "thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen","twenty",
        "twenty-one","twenty-two","twenty-three","twenty-four","twenty-five"]
TARGET = {n: 4200 for n in range(1, 25)}; TARGET.update({6: 4300, 16: 4300, 18: 4300, 23: 4300, 25: 2000})
ok = True
for arg in sys.argv[1:]:
    n = int(arg[2:])
    md = (ROOT / "chapters" / f"{arg}.md").read_text()
    tts = (ROOT / "full_book_tts" / f"{arg}_tts.txt").read_text()
    words = len(re.findall(r"[A-Za-z0-9'’-]+", md))
    t = TARGET[n]; problems = []
    if not (t * 0.9 <= words <= t * 1.1): problems.append(f"word count {words} vs target {t}")
    first = tts.splitlines()[0] if tts else ""
    if not first.lower().startswith(f"chapter {NUMS[n]}."): problems.append(f"TTS header: {first!r}")
    if len(tts.splitlines()) < 2 or tts.splitlines()[1].strip(): problems.append("no blank line after TTS header")
    bad = sorted(set(re.findall(r"[*_#\[\]{}<>|~`=+@^\\/]|---|[\U0001F300-\U0001FAFF]", tts)))
    if bad: problems.append(f"TTS symbols: {bad}")
    digits = re.findall(r".{0,20}\d.{0,20}", tts)
    if digits: problems.append(f"TTS digits: {digits[:5]}")
    sd = md.count("Simple Domain")
    if sd > 3: problems.append(f"'Simple Domain' x{sd}")
    sk = len(re.findall(r"shikata", md, re.I))
    if sk and n not in (24, 25): problems.append(f"shikata ga nai used x{sk}")
    long = [s for s in re.split(r"(?<=[.!?])\s+", tts) if len(s.split()) > 40]
    if long: problems.append(f"{len(long)} sentences over 40 words")
    tw = len(re.findall(r"[A-Za-z0-9'’-]+", tts))
    print(f"{arg}: md {words} words, tts {tw} words" + ("" if not problems else "\n  - " + "\n  - ".join(problems)))
    ok &= not problems
sys.exit(0 if ok else 1)
