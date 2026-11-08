"""Run:  python diag_models.py
Times ONE tiny request on each model (3 requests total, same IPv4 route as the app). Gives up on a model after 40s."""
import concurrent.futures as cf
import time

from google import genai
from backend.config import GEMINI_API_KEY
from backend.services.gemini_service import _http_options

MODELS = ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
client = genai.Client(api_key=GEMINI_API_KEY, http_options=_http_options())
pool = cf.ThreadPoolExecutor(max_workers=3)

for model in MODELS:
    started = time.time()
    future = pool.submit(
        client.models.generate_content,
        model=model,
        contents='Reply with JSON only: {"ok": true}',
    )
    try:
        text = (future.result(timeout=40).text or "")[:60].replace("\n", " ")
        print(f"{model:24s} {time.time()-started:6.1f}s  OK   {text}", flush=True)
    except cf.TimeoutError:
        print(f"{model:24s} >40s  STILL WAITING (given up)", flush=True)
    except Exception as exc:
        print(f"{model:24s} {time.time()-started:6.1f}s  FAIL {type(exc).__name__}: {str(exc)[:150]}", flush=True)

import os
os._exit(0)