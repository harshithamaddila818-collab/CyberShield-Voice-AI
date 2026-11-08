"""Rules-only benchmark.  Run from the project root:  python -m tests.run_benchmark
Calls the rule engine directly (no Gemini, no quota, no network).
scam = MEDIUM or HIGH,  genuine = LOW."""
import sys
from backend.services.threat_engine import analyze_text
from tests.benchmark_messages import DEV, HELD_OUT, HARD, BLIND, BLIND2, BLIND3, BLIND4


def evaluate(name, data, show_errors=True):
    tp = fp = tn = fn = 0
    errors = []
    for label, text in data:
        r = analyze_text(text)
        predicted_scam = r["risk_level"] in ("MEDIUM", "HIGH")
        if label == "scam" and predicted_scam: tp += 1
        elif label == "scam": fn += 1; errors.append(("MISSED scam", r, text))
        elif predicted_scam: fp += 1; errors.append(("FALSE ALARM", r, text))
        else: tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    acc = (tp + tn) / len(data)
    print(f"\n=== {name}: {len(data)} messages ({tp+fn} scam / {tn+fp} genuine) ===")
    print(f"TP={tp} FN={fn} FP={fp} TN={tn}")
    print(f"Accuracy {acc:.1%} | Precision {precision:.1%} | Recall {recall:.1%} | F1 {f1:.1%} | False-positive rate {fpr:.1%}")
    if show_errors:
        for kind, r, text in errors:
            print(f"  {kind}: {r['risk_level']} {r['risk_score']} | {text[:80]}")
    return dict(tp=tp, fn=fn, fp=fp, tn=tn, precision=precision, recall=recall, f1=f1, fpr=fpr, acc=acc)


if __name__ == "__main__":
    evaluate("DEV set (used while tuning)", DEV)
    evaluate("HELD-OUT set (never used for tuning)", HELD_OUT)
    evaluate("HARD set (realistic paraphrases, Tenglish, tricky genuine)", HARD)
    evaluate("BLIND set (written after tuning, run once)", BLIND)
    evaluate("BLIND2 set (fresh, written after all tuning, run once)", BLIND2)
    evaluate("BLIND3 set (fresh, written after the final rule changes, run once)", BLIND3)
    evaluate("BLIND4 set (fresh, written after ALL rule changes, run once)", BLIND4)
    evaluate("ALL", DEV + HELD_OUT + HARD + BLIND + BLIND2 + BLIND3 + BLIND4, show_errors=False)
