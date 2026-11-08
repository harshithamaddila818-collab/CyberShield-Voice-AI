import requests
from backend.config import GNANI_API_KEY, GNANI_TTS_URL, GNANI_TTS_MODEL, GNANI_TTS_TELUGU_VOICE, GNANI_TTS_ENGLISH_VOICE

def synthesize_warning(text, language="te-IN"):
    if not GNANI_API_KEY: raise RuntimeError("GNANI_API_KEY is missing. Add your Gnani API key to .env.")
    te = language.lower().startswith("te")
    payload = {"text": text[:1800], "voice": GNANI_TTS_TELUGU_VOICE if te else GNANI_TTS_ENGLISH_VOICE, "model": GNANI_TTS_MODEL, "language": "te-IN" if te else "en-IN", "speed": 1.0, "audio_config": {"sample_rate": 48000, "num_channels": 1, "sample_width": 2, "encoding": "linear_pcm", "container": "wav"}}
    response = requests.post(GNANI_TTS_URL, headers={"X-API-Key-ID": GNANI_API_KEY, "Content-Type": "application/json"}, json=payload, timeout=90)
    if not response.ok:
        try: detail = response.json()
        except Exception: detail = response.text[:500]
        raise RuntimeError(f"Gnani Timbre error ({response.status_code}): {detail}")
    return response.content
