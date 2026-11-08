import requests
from backend.config import GNANI_API_KEY, GNANI_STT_URL, GNANI_STT_MODEL

def transcribe_audio(filename, content, language_code="indic-auto"):
    if not GNANI_API_KEY:
        raise RuntimeError("GNANI_API_KEY is missing. Add your Gnani API key to .env.")
    response = requests.post(GNANI_STT_URL, headers={"X-API-Key-ID": GNANI_API_KEY}, data={"model": GNANI_STT_MODEL, "language_code": language_code}, files={"audio_file": (filename, content)}, timeout=90)
    if not response.ok:
        try: detail = response.json()
        except Exception: detail = response.text[:500]
        raise RuntimeError(f"Gnani Prisma error ({response.status_code}): {detail}")
    body = response.json()
    if not body.get("success", False): raise RuntimeError(f"Gnani transcription failed: {body}")
    return {"transcript": body.get("transcript", ""), "model": body.get("model", GNANI_STT_MODEL), "detected_language_code": body.get("detected_language_code"), "request_id": body.get("request_id")}
