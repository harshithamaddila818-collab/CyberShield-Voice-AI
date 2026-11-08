"""Run:  python diag_sdk.py   (3 Gemini requests). Raw httpx vs Google SDK, same IPv4 route."""
import concurrent.futures as cf
import os
import time

import httpx
from google import genai
from backend.config import GEMINI_API_KEY
from backend.services.gemini_service import _http_options

MODEL = "gemini-2.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
BODY = {"contents": [{"parts": [{"text": 'Reply with JSON only: {"ok": true}'}]}]}
HEAD = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
pool = cf.ThreadPoolExecutor(max_workers=3)

def raw():
    with httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"), timeout=60) as c:
        return c.post(URL, headers=HEAD, json=BODY).status_code

client = genai.Client(api_key=GEMINI_API_KEY, http_options=_http_options())
def sdk():
    return bool(client.models.generate_content(model=MODEL, contents="Reply with JSON only: {\"ok\": true}").text)

for label, fn in (("1 raw httpx", raw), ("2 SDK (first call)", sdk), ("3 SDK (second call)", sdk)):
    t = time.time(); f = pool.submit(fn)
    try:
        print(f"{label:22s} {time.time()-t:6.1f}s  OK   {f.result(timeout=40)}", flush=True)
    except cf.TimeoutError:
        print(f"{label:22s} >40s  STILL WAITING", flush=True)
    except Exception as exc:
        print(f"{label:22s} {time.time()-t:6.1f}s  FAIL {type(exc).__name__}: {str(exc)[:100]}", flush=True)
os._exit(0)