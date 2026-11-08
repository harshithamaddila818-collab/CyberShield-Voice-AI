"""Run:  python diag_net.py   (uses 2 Gemini requests). Tests normal route vs IPv4-only route."""
import concurrent.futures as cf
import time

import httpx
from backend.config import GEMINI_API_KEY

URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
BODY = {"contents": [{"parts": [{"text": 'Reply with JSON only: {"ok": true}'}]}]}
HEAD = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
pool = cf.ThreadPoolExecutor(max_workers=4)

def call(ipv4_only):
    transport = httpx.HTTPTransport(local_address="0.0.0.0") if ipv4_only else httpx.HTTPTransport()
    with httpx.Client(transport=transport, timeout=60) as c:
        r = c.post(URL, headers=HEAD, json=BODY)
        return r.status_code

for label, ipv4 in (("A normal route", False), ("B IPv4-only route", True)):
    t = time.time()
    f = pool.submit(call, ipv4)
    try:
        print(f"{label:20s} {time.time()-t:6.1f}s  HTTP {f.result(timeout=50)}", flush=True)
    except cf.TimeoutError:
        print(f"{label:20s} >50s  STILL WAITING", flush=True)
    except Exception as exc:
        print(f"{label:20s} {time.time()-t:6.1f}s  FAIL {type(exc).__name__}: {str(exc)[:120]}", flush=True)

import os
os._exit(0)