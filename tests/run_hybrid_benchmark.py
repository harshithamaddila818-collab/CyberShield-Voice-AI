"""OPTIONAL: rules + Gemini benchmark on the fresh BLIND4 set (needs Gemini quota, ~24 requests).
Run:  python -m tests.run_hybrid_benchmark          (stops safely if the quota runs out)
Compare its numbers with the rules-only run to see what Gemini adds."""
import time
from backend.services.threat_engine import analyze_text, combine_verdicts
from backend.services.gemini_service import analyze_with_gemini
from tests.benchmark_messages import BLIND4

tp = fp = tn = fn = done = 0
for label, text in BLIND4:
    ai = analyze_with_gemini(text)
    if ai.get("error") == "QuotaExceeded":
        print("Gemini quota used up - stopping early.")
        break
    r = combine_verdicts(analyze_text(text), ai)
    scam = r["risk_level"] in ("MEDIUM", "HIGH")
    done += 1
    if label == "scam": tp += scam; fn += (not scam)
    else: fp += scam; tn += (not scam)
    print(f"{r['risk_level']:6s} {r['risk_score']:3d} ({'gemini ok' if ai.get('enabled') and not ai.get('error') else 'rules only'}) {label:7s} | {text[:60]}")
    time.sleep(4)

p = tp / (tp + fp) if tp + fp else 0
rc = tp / (tp + fn) if tp + fn else 0
f1 = 2 * p * rc / (p + rc) if p + rc else 0
print(f"\nHybrid on {done} BLIND4 messages: TP={tp} FN={fn} FP={fp} TN={tn} | precision {p:.1%} recall {rc:.1%} F1 {f1:.1%} FPR {fp/(fp+tn) if fp+tn else 0:.1%}")
