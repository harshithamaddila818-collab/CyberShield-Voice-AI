"""Gemini resilience checks against a LOCAL fake Gemini server (no real quota is used).
Run from the project root:   python -m tests.test_gemini_resilience
Covers: model fallback, 404 retired model, 429 quota memory, 503 busy, cache, off-switch."""
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ["CYBERSHIELD_GEMINI_CACHE"] = os.path.join(tempfile.mkdtemp(), "cache.json")
os.environ["GEMINI_API_KEY"] = "fake-key"
os.environ["GEMINI_MODEL"] = "model-a"
os.environ["GEMINI_FALLBACK_MODELS"] = "model-b,model-c"

QUOTA, GONE, BUSY, CALLS = set(), set(), set(), []
OK = {"candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps({
    "threat_type": "Phishing", "confidence": 90, "explanation": "e", "recommended_action": "r",
    "language": "English", "voice_warning_en": "w", "voice_warning_te": "w"})}]}, "finishReason": "STOP"}]}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        model = self.path.split("/models/")[1].split(":")[0]
        CALLS.append(model)
        if model in GONE:
            code, body = 404, {"error": {"code": 404, "message": "retired", "status": "NOT_FOUND"}}
        elif model in QUOTA:
            code, body = 429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED",
                                         "details": [{"retryDelay": "6000s"}]}}
        elif model in BUSY:
            code, body = 503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}}
        else:
            code, body = 200, OK
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()

from google import genai
from google.genai import types

real_client = genai.Client
base_url = f"http://127.0.0.1:{server.server_address[1]}"
genai.Client = lambda api_key=None, http_options=None: real_client(
    api_key=api_key,
    http_options=types.HttpOptions(base_url=base_url, timeout=getattr(http_options, "timeout", None)),
)

import backend.services.gemini_service as g

failures = []


def check(name, condition):
    print(("PASS" if condition else "FAIL"), name)
    if not condition:
        failures.append(name)


def call(message):
    CALLS.clear()
    return g.analyze_with_gemini(message), list(CALLS)


r, calls = call("m1")
check("healthy primary answers with one call", r.get("threat_type") == "Phishing" and calls == ["model-a"])

QUOTA.add("model-a")
r, calls = call("m2")
check("429 on primary -> fallback model answers", r.get("threat_type") == "Phishing" and calls == ["model-a", "model-b"])
r, calls = call("m3")
check("quota memory: exhausted model is not called again", calls == ["model-b"])
r, calls = call("m2")
check("cache hit uses zero requests", r.get("threat_type") == "Phishing" and calls == [])

GONE.add("model-b")
r, calls = call("m4")
check("404 retired model is skipped, next one answers", r.get("threat_type") == "Phishing" and calls == ["model-b", "model-c"])

BUSY.add("model-c")
r, calls = call("m5")
check("503 busy on every model -> graceful error (no crash)", r.get("enabled") is True and r.get("error") and "rule-based" in r.get("note", ""))

BUSY.clear()
QUOTA.update({"model-a", "model-b", "model-c"})
g._blocked_until.clear()
g._unavailable_models.clear()
r, calls = call("m6")
check("all models out of quota -> QuotaExceeded note", r.get("error") == "QuotaExceeded")
r, calls = call("m7")
check("after that, zero requests are wasted", calls == [])

os.environ["GEMINI_ENABLED"] = "false"
r, calls = call("m8")
check("GEMINI_ENABLED=false makes no request", r.get("enabled") is False and calls == [])

print("\nAll Gemini resilience checks passed." if not failures else f"\n{len(failures)} FAILED: {failures}")
raise SystemExit(len(failures))
