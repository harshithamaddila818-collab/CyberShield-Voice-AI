import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GNANI_STT_URL = "https://api.vachana.ai/stt/v3"
GNANI_TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
GNANI_STT_MODEL = os.getenv("GNANI_STT_MODEL", "prisma-v3.0")
GNANI_TTS_MODEL = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5")
GNANI_TTS_TELUGU_VOICE = os.getenv("GNANI_TTS_TELUGU_VOICE", "Suhana")
GNANI_TTS_ENGLISH_VOICE = os.getenv("GNANI_TTS_ENGLISH_VOICE", "Kaveri")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
MAX_AUDIO_BYTES = 15 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
