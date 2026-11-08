"""Run:  python diag_gemini.py   (uses 1 Gemini request). Shows WHERE the time goes."""
import socket, time

HOST = "generativelanguage.googleapis.com"

def step(name, fn):
    t = time.time()
    try:
        out = fn()
        print(f"{name:28s} {time.time()-t:6.1f}s  OK   {out}", flush=True)
    except Exception as exc:
        print(f"{name:28s} {time.time()-t:6.1f}s  FAIL {type(exc).__name__}: {exc}", flush=True)

step("1 DNS lookup", lambda: socket.getaddrinfo(HOST, 443)[0][4][0])
step("2 DNS IPv4 only", lambda: socket.getaddrinfo(HOST, 443, socket.AF_INET)[0][4][0])
step("3 TCP connect (IPv4)", lambda: socket.create_connection(
    (socket.getaddrinfo(HOST, 443, socket.AF_INET)[0][4][0], 443), timeout=10).close())

from backend.services import gemini_service as g
print("models:", g._model_chain(), "timeout ms:", g.HTTP_TIMEOUT_MS, flush=True)
msg = f"Your KYC is expired, update immediately or account will be blocked. ref {time.time()}"
def _call():
    r = g.analyze_with_gemini(msg)  # ONE request only
    return {k: r.get(k) for k in ("enabled", "error", "threat_type", "confidence", "note")}

step("4 full Gemini call", _call)