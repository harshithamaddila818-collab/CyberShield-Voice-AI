"""Voice benchmark: real audio -> Gnani Prisma -> CyberShield verdict.

Run from the project root:   python -m tests.run_voice_benchmark [--hybrid]
Reads tests/audio/labels.csv and the clips tests/audio/<id>.<ext>. Writes tests/voice_results.md.
Only the clips you actually recorded are used.
"""
import csv
import re
import sys
import time
import unicodedata
from pathlib import Path

from backend.services.prisma_service import transcribe_audio
from backend.services.threat_engine import analyze_text, combine_verdicts

AUDIO_DIR = Path(__file__).parent / "audio"
EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac")


def normalize(text):
    text = unicodedata.normalize("NFC", text or "").lower()
    text = re.sub(r"[‌‍]", "", text)          # zero-width joiners vary between engines
    text = re.sub(r"[^\w\s]", " ", text)               # punctuation
    return text.split()


def word_error_rate(reference, hypothesis):
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i]
        for j, h in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h)))
        prev = cur
    return prev[-1] / len(ref)


def find_clip(clip_id):
    for ext in EXTENSIONS:
        path = AUDIO_DIR / f"{clip_id}{ext}"
        if path.exists():
            return path
    return None


def verdict(text, use_gemini):
    rule = analyze_text(text)
    if not use_gemini:
        return rule
    from backend.services.gemini_service import analyze_with_gemini
    return combine_verdicts(rule, analyze_with_gemini(text))


def metrics(rows, key):
    tp = sum(1 for r in rows if r["expected"] == "scam" and r[key])
    fn = sum(1 for r in rows if r["expected"] == "scam" and not r[key])
    fp = sum(1 for r in rows if r["expected"] == "genuine" and r[key])
    tn = sum(1 for r in rows if r["expected"] == "genuine" and not r[key])
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return dict(tp=tp, fn=fn, fp=fp, tn=tn, precision=precision, recall=recall, f1=f1, fpr=fpr)


def main():
    use_gemini = "--hybrid" in sys.argv
    with open(AUDIO_DIR / "labels.csv", encoding="utf-8", newline="") as f:
        labels = list(csv.DictReader(f))

    rows = []
    for item in labels:
        clip = find_clip(item["id"])
        if not clip:
            continue
        started = time.perf_counter()
        try:
            stt = transcribe_audio(clip.name, clip.read_bytes(), "indic-auto")
        except Exception as exc:
            print(f"{item['id']}: Prisma failed: {exc}")
            continue
        stt_s = time.perf_counter() - started
        heard = stt["transcript"]
        voice = verdict(heard, use_gemini)
        text_only = verdict(item["reference"], use_gemini)
        rows.append({
            "id": item["id"], "expected": item["expected"], "language": item["language"],
            "wer": word_error_rate(item["reference"], heard), "stt_s": stt_s, "heard": heard,
            "voice_level": voice["risk_level"], "voice_pred": voice["risk_level"] in ("MEDIUM", "HIGH"),
            "text_pred": text_only["risk_level"] in ("MEDIUM", "HIGH"),
        })
        r = rows[-1]
        print(f"{r['id']} {r['expected']:7s} WER {r['wer']:.0%} {r['stt_s']:.1f}s -> {r['voice_level']}")

    if not rows:
        print("No clips found. See tests/audio/README.md.")
        return

    mode = "rules + Gemini" if use_gemini else "rules only"
    out = [f"# Voice benchmark ({mode})", "", f"Clips used: {len(rows)} (single speaker, scripted sentences)", ""]
    for lang, name in (("te", "Telugu"), ("en", "English"), (None, "All")):
        subset = [r for r in rows if lang is None or r["language"] == lang]
        if not subset:
            continue
        wer = sum(r["wer"] for r in subset) / len(subset)
        latency = sum(r["stt_s"] for r in subset) / len(subset)
        v, t = metrics(subset, "voice_pred"), metrics(subset, "text_pred")
        out += [
            f"## {name} ({len(subset)} clips)",
            f"- Prisma mean WER: **{wer:.1%}**, mean STT time: {latency:.1f} s",
            f"- Voice path (Prisma transcript): precision {v['precision']:.1%}, recall {v['recall']:.1%}, "
            f"F1 {v['f1']:.1%}, false-positive rate {v['fpr']:.1%} (TP {v['tp']} FN {v['fn']} FP {v['fp']} TN {v['tn']})",
            f"- Text path (reference text): precision {t['precision']:.1%}, recall {t['recall']:.1%}, "
            f"F1 {t['f1']:.1%}, false-positive rate {t['fpr']:.1%}",
            "",
        ]
    report = "\n".join(out)
    (Path(__file__).parent / "voice_results.md").write_text(report, encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main()
