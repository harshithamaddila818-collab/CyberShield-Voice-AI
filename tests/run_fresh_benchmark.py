"""Fresh-message benchmark: messages written by other people (research/raw_messages.txt).

Run from the project root:
    python -m tests.run_fresh_benchmark              # rules only (no API calls)
    python -m tests.run_fresh_benchmark --hybrid     # rules + Gemini (asks before using quota)

Rules are NOT changed by this script. Results are a baseline, not a tuning tool.
Writes research/evaluation_results.txt (use --out to choose another file).
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

from backend.services.threat_engine import analyze_text, combine_verdicts

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "research" / "raw_messages.txt"
DEFAULT_OUTPUT = ROOT / "research" / "evaluation_results.txt"

# Pre-registered BEFORE running: labels that are debatable (promotions / ambiguous alerts).
# (contributor, label, number)
DEBATABLE = {
    (1, "GENUINE", 2),   # "account debited 500/- ... contact the bank immediately"
    (2, "SCAM", 1),      # bank-style credit alert with a link
    (2, "SCAM", 2),      # pre-approved loan promotion
    (2, "SCAM", 3),      # GST / insurance promotion
}

# SHA256 of the files at the pre-fix baseline (recorded earlier in the project).
BASELINE_HASHES = {
    "backend/services/threat_engine.py": "15E0BEC31C3C2686F3FE78598F70FD3740B16E94ED4E1C0B4375C9CE1B18D310",
    "backend/services/gemini_service.py": "A123DC8FD8033EEE06D9009BC9EF2B6AC6E64DAB780BC40050C496E16634BD50",
}

LIMITS = [
    "30 messages from 5 contributors; far too small to prove production-level accuracy.",
    "Mostly English. Only 1 Tenglish message and no Telugu-script messages: this is NOT a Telugu test.",
    "Labels were supplied by the contributors and are not independently verified.",
    "Several messages look like real SMS pasted with personal details masked, not freshly invented.",
    "Links were replaced by [LINK REDACTED]; links are a strong scam signal, so scam messages are harder here than originally.",
    "Four labels are debatable (promotions / ambiguous alerts); results are shown with and without them.",
    "The detector was NOT changed after seeing these results.",
]


def parse_messages(path):
    text = path.read_text(encoding="utf-8-sig")
    messages = []
    contributor = None
    label = None
    current = None

    def flush():
        nonlocal current
        if current is not None:
            current["text"] = " ".join(current["text"].split())
            if current["text"]:
                messages.append(current)
        current = None

    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^COLLECTION SUMMARY", line, re.I):
            flush()
            break
        m = re.match(r"^CONTRIBUTOR\s+(\d+)\s*$", line, re.I)
        if m:
            flush()
            contributor, label = int(m.group(1)), None
            continue
        m = re.match(r"^(SCAM|GENUINE)\s*:\s*$", line, re.I)
        if m:
            flush()
            label = m.group(1).upper()
            continue
        if contributor is None or label is None:
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            flush()
            current = {"contributor": contributor, "label": label,
                       "number": int(m.group(1)), "text": m.group(2)}
            continue
        if not line:
            flush()
            continue
        if current is not None:          # continuation line of a multi-line message
            current["text"] += " " + line
    flush()
    return messages


def metrics(rows):
    tp = sum(1 for r in rows if r["label"] == "SCAM" and r["pred"])
    fn = sum(1 for r in rows if r["label"] == "SCAM" and not r["pred"])
    fp = sum(1 for r in rows if r["label"] == "GENUINE" and r["pred"])
    tn = sum(1 for r in rows if r["label"] == "GENUINE" and not r["pred"])
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return dict(tp=tp, fn=fn, fp=fp, tn=tn, precision=precision, recall=recall, f1=f1, fpr=fpr)


def metric_line(title, rows):
    if not rows:
        return f"{title}: no messages"
    m = metrics(rows)
    return (f"{title} (n={len(rows)}): precision {m['precision']:.1%}, recall {m['recall']:.1%}, "
            f"F1 {m['f1']:.1%}, false-positive rate {m['fpr']:.1%}  "
            f"[TP {m['tp']} FN {m['fn']} FP {m['fp']} TN {m['tn']}]")


def file_hash(relative):
    path = ROOT / relative
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def evaluate(messages, use_gemini):
    rows = []
    for msg in messages:
        rule = analyze_text(msg["text"])
        rule_level = rule["risk_level"]
        row = dict(msg)
        row["rule_level"] = rule_level
        row["rule_score"] = rule["risk_score"]
        row["rule_pred"] = rule_level in ("MEDIUM", "HIGH")
        if use_gemini:
            from backend.services.gemini_service import analyze_with_gemini
            ai = analyze_with_gemini(msg["text"])
            final = combine_verdicts(rule, ai)
            row["hyb_level"] = final["risk_level"]
            row["hyb_score"] = final["risk_score"]
            row["hyb_pred"] = final["risk_level"] in ("MEDIUM", "HIGH")
            # Did Gemini really answer? If not, this message is effectively rules-only.
            if isinstance(ai, dict) and ai.get("enabled") and not ai.get("error"):
                row["gemini_status"] = "answered"
                row["gemini_conf"] = ai.get("confidence")
            elif isinstance(ai, dict) and ai.get("error"):
                row["gemini_status"] = "NO ANSWER (" + str(ai.get("error")) + ")"
            else:
                row["gemini_status"] = "NO ANSWER (Gemini disabled or key missing)"
        rows.append(row)
    return rows


def build_report(rows, use_gemini):
    out = ["FRESH-MESSAGE BENCHMARK (research/raw_messages.txt)", ""]
    out.append("Scam = MEDIUM or HIGH, genuine = LOW. Contributor labels used as given.")
    out.append("")
    out.append("LIMITATIONS")
    out += [f"- {item}" for item in LIMITS]
    out.append("")
    out.append("CODE VERSION")
    for rel, baseline in BASELINE_HASHES.items():
        current = file_hash(rel)
        state = "matches the pre-fix baseline" if current == baseline else "DIFFERS from the pre-fix baseline"
        out.append(f"- {rel}: {state}")
    out.append("")

    systems = [("RULES ONLY", "rule")]
    if use_gemini:
        systems.append(("RULES + GEMINI", "hyb"))

    for title, key in systems:
        view = []
        for r in rows:
            c = dict(r)
            c["pred"] = r[f"{key}_pred"]
            c["is_debatable"] = (r["contributor"], r["label"], r["number"]) in DEBATABLE
            view.append(c)
        clean = [r for r in view if not r["is_debatable"]]
        out.append(f"== {title} ==")
        if key == "hyb":
            answered = sum(1 for r in rows if r.get("gemini_status") == "answered")
            out.append(f"Gemini answered {answered} of {len(rows)} messages.")
            if answered < len(rows):
                out.append("WARNING: the messages below without a Gemini answer were judged by the rules alone,")
                out.append("so these rules + Gemini numbers are only partly a hybrid result:")
                for r in rows:
                    if r.get("gemini_status") != "answered":
                        out.append(f"  C{r['contributor']} {r['label']} #{r['number']}: {r.get('gemini_status')}")
        out.append(metric_line("All messages", view))
        out.append(metric_line("Excluding the 4 debatable", clean))
        out.append("")
        wrong = [r for r in view if (r["label"] == "SCAM") != r["pred"]]
        out.append(f"Wrong verdicts ({len(wrong)}):")
        if not wrong:
            out.append("  none")
        for r in wrong:
            kind = "MISSED SCAM" if r["label"] == "SCAM" else "FALSE ALARM"
            flag = " [debatable label]" if r["is_debatable"] else ""
            out.append(f"  C{r['contributor']} {r['label']} #{r['number']}: {kind} -> "
                       f"{r[key + '_level']} {r[key + '_score']}{flag}")
            out.append(f"     {r['text'][:160]}")
        out.append("")

    out.append("PER-MESSAGE VERDICTS")
    for r in rows:
        line = f"C{r['contributor']} {r['label']:7s} #{r['number']}: rules {r['rule_level']} {r['rule_score']}"
        if use_gemini:
            line += f" | rules+Gemini {r['hyb_level']} {r['hyb_score']} [Gemini: {r.get('gemini_status')}"
            if r.get("gemini_conf") is not None:
                line += f", confidence {r['gemini_conf']}%"
            line += "]"
        out.append(line)
    out.append("")
    out.append("These numbers describe this small set only. They are not a production accuracy claim.")
    return "\n".join(out)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--hybrid", action="store_true", help="also run rules + Gemini (uses API quota)")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    messages = parse_messages(Path(args.input))
    n_scam = sum(1 for m in messages if m["label"] == "SCAM")
    print(f"Parsed {len(messages)} messages: {n_scam} scam-labelled, {len(messages) - n_scam} genuine-labelled, "
          f"{len({m['contributor'] for m in messages})} contributors.")
    if not messages:
        print("No messages found. Check the file format.")
        return

    use_gemini = args.hybrid
    if use_gemini:
        answer = input(f"This will make up to {len(messages)} Gemini calls and use free-tier quota. Type YES to continue: ")
        if answer.strip() != "YES":
            print("Gemini run cancelled; running rules only.")
            use_gemini = False

    report = build_report(evaluate(messages, use_gemini), use_gemini)
    Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()