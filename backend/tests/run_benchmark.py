from backend.tests.benchmark_messages import BENCHMARK_MESSAGES
from backend.services.threat_engine import analyze_text, combine_verdicts
from backend.services.gemini_service import analyze_with_gemini

results = []

for item in BENCHMARK_MESSAGES:
    rules = analyze_text(item["text"])
    ai = analyze_with_gemini(item["text"])
    final = combine_verdicts(rules, ai)

    results.append({
        "id": item["id"],
        "category": item["category"],
        "expected": item["expected"],
        "actual": final["risk_level"],
        "score": final["risk_score"],
        "correct": item["expected"] == final["risk_level"]
    })

total = len(results)
correct = sum(row["correct"] for row in results)
accuracy = (correct / total) * 100

print("\nCYBERSHIELD 40-MESSAGE BENCHMARK")
print("-" * 65)

for row in results:
    status = "PASS" if row["correct"] else "FAIL"
    print(
        f'{row["id"]:02} | {row["category"]:<24} | '
        f'{row["expected"]:<6} | {row["actual"]:<6} | '
        f'{row["score"]:>3}/100 | {status}'
    )

print("-" * 65)
print(f"Correct: {correct}/{total}")
print(f"Accuracy: {accuracy:.2f}%")
print("Review failed cases before changing detection rules.")