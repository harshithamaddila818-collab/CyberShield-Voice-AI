"""Automated API checks (no real Gnani / Gemini calls, no network).
Run from the project root:   python -m tests.test_api
Gnani Prisma/Timbre are replaced by tiny fakes so the full request path is exercised."""
import os
import tempfile

os.environ["GEMINI_ENABLED"] = "false"          # rules only: deterministic and free
os.environ["RATE_LIMIT_PER_MIN"] = "12"
os.environ["CYBERSHIELD_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient

import backend.main as app_module

app_module.transcribe_audio = lambda name, content, lang="indic-auto": {
    "transcript": "Your SBI account is blocked. Share the OTP immediately.",
    "model": "fake-prisma", "detected_language_code": "en-IN", "request_id": "t1",
}
app_module.synthesize_warning = lambda text, language="te-IN": b"RIFFfakewav"

client = TestClient(app_module.app)
failures = []


def check(name, condition):
    print(("PASS" if condition else "FAIL"), name)
    if not condition:
        failures.append(name)


r = client.get("/health").json()
check("health reports components", r["status"] == "ok" and r["components"]["rule_engine"] is True)

r = client.post("/api/analyze-text", json={"text": "Your SBI account is blocked. Share the OTP immediately to unblock it."}).json()
check("scam text -> HIGH", r["analysis"]["risk_level"] == "HIGH")
check("response keeps the original structure", {"transcript", "analysis", "rule_analysis", "ai_analysis", "disclaimer"} <= set(r))
check("response has pipeline timings", {"rules_ms", "gemini_ms", "gemini_status"} <= set(r["pipeline"]))

r = client.post("/api/analyze-text", json={"text": "123456 is your OTP. Do not share this code with anyone."}).json()
check("genuine OTP -> LOW", r["analysis"]["risk_level"] == "LOW" and r["analysis"]["risk_score"] == 0)

r = client.post("/api/analyze-text", json={"text": "మీ ఖాతా KYC అప్‌డేట్ చేయకపోతే ఈరోజే బ్లాక్ అవుతుంది"}).json()
check("Telugu KYC scam -> MEDIUM or HIGH", r["analysis"]["risk_level"] in ("MEDIUM", "HIGH"))

check("empty text -> 400", client.post("/api/analyze-text", json={"text": "   "}).status_code == 400)
check("over-long text -> 422", client.post("/api/analyze-text", json={"text": "x" * 5001}).status_code == 422)

r = client.post("/api/analyze-audio", files={"audio": ("clip.wav", b"RIFFxxxx", "audio/wav")})
j = r.json()
check("audio -> Prisma -> verdict", r.status_code == 200 and j["analysis"]["risk_level"] == "HIGH" and "stt_ms" in j["pipeline"])
check("bad audio type -> 400", client.post("/api/analyze-audio", files={"audio": ("a.txt", b"x", "text/plain")}).status_code == 400)
check("empty audio -> 400", client.post("/api/analyze-audio", files={"audio": ("a.wav", b"", "audio/wav")}).status_code == 400)

r = client.post("/api/speak", json={"text": "Be careful.", "language": "te-IN"})
check("speak -> audio/wav", r.status_code == 200 and r.headers["content-type"] == "audio/wav")

h = client.post("/api/history", json={"transcript": "t", "analysis": {"risk_score": 75, "risk_level": "HIGH"}, "ai_analysis": {}})
check("history save + list", h.status_code == 200 and client.get("/api/history").json()["items"])
check("PDF report", client.post("/api/report-pdf", json={"transcript": "t", "analysis": {"risk_score": 75, "risk_level": "HIGH", "signals": ["x"]}, "ai_analysis": {}}).content[:4] == b"%PDF")
check("URL check flags a shortener", client.post("/api/scan-url", json={"url": "http://bit.ly/x"}).json()["risk_score"] > 0)
check("web page served at /app/", "CyberShield" in client.get("/app/").text)

codes = [client.post("/api/analyze-text", json={"text": "hello"}).status_code for _ in range(15)]
check("rate limit returns 429 after the limit", 429 in codes)
check("rate-limited reply keeps CORS header", client.post("/api/analyze-text", json={"text": "x"}, headers={"Origin": "http://a.example"}).headers.get("access-control-allow-origin") == "*")

print("\nAll API checks passed." if not failures else f"\n{len(failures)} check(s) FAILED: {failures}")
raise SystemExit(len(failures))
