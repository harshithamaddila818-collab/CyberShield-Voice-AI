"""Run:  python -m tests.test_fusion   (no network). Checks the Gemini + rules fusion rules."""
from backend.services.threat_engine import analyze_text, combine_verdicts

def ai(t, c): return {"enabled": True, "threat_type": t, "confidence": c}
def run(text, a):
    r = combine_verdicts(analyze_text(text), a); return r["risk_level"], r["risk_score"], r.get("verdict_source")

checks = [
    # (name, text, ai, expected_level)
    ("Gemini alone, strong -> MEDIUM not HIGH", "Hello, please see the attached holiday photos.", ai("Phishing", 98), "MEDIUM"),
    ("Gemini alone, weak -> LOW", "Hello, please see the attached holiday photos.", ai("Phishing", 40), "LOW"),
    ("Gemini 'Unknown' is not a scam", "Hello there", ai("Unknown", 95), "LOW"),
    ("Rules MEDIUM + Gemini strong -> HIGH", "మీ ఖాతా KYC గడువు ముగిసింది, అప్‌డేట్ చేయండి", ai("Fake KYC", 95), "HIGH"),
    ("Gemini says safe -> rules unchanged", "Your OTP is 123456. Do not share it with anyone.", ai("No obvious scam", 90), "LOW"),
    ("Gemini error -> rules only", "Your SBI account is blocked. Share the OTP immediately.", {"enabled": True, "error": "QuotaExceeded"}, "HIGH"),
    ("Gemini off -> rules only", "Hello there", {"enabled": False}, "LOW"),
    ("Genuine OTP guard beats Gemini", "123456 is your OTP. Do not share this code with anyone.", ai("OTP Scam", 99), "LOW"),
]
bad = 0
for name, text, a, want in checks:
    level, score, src = run(text, a)
    ok = level == want; bad += not ok
    print(("PASS" if ok else "FAIL"), f"{name:44s} -> {level} {score} ({src})")
print("\nAll fusion checks passed." if not bad else f"\n{bad} check(s) FAILED.")
raise SystemExit(bad)
