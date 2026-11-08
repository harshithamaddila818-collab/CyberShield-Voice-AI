
import os
from pathlib import Path
import subprocess
import tempfile
import time

import imageio_ffmpeg

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_BYTES, GNANI_API_KEY, GEMINI_API_KEY
from backend.security import install_rate_limit
from backend.services.prisma_service import transcribe_audio
from backend.services.threat_engine import analyze_text,combine_verdicts
from backend.services.gemini_service import analyze_with_gemini
from backend.services.timbre_service import synthesize_warning


app = FastAPI(
    title="CyberShield Voice AI",
    version="1.0.0",
    description="Voice-first Telugu and English scam detection demo"
)
from backend.features import router as features_router

app.include_router(features_router)

install_rate_limit(app)

# CORS_ORIGINS="https://my-demo.example" restricts browsers; default "*" keeps local development easy.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
    if origin.strip()
] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


class TextRequest(BaseModel):
    text: str = Field(max_length=5000)


class SpeakRequest(BaseModel):
    text: str = Field(max_length=4000)
    language: str = "te-IN"


@app.get("/")
def home():
    return {
        "message": "CyberShield Voice AI API is running",
        "docs": "/docs",
        "app": "/app/"
    }


@app.get("/health")
def health():
    from backend.services.gemini_service import _gemini_enabled, _model_chain

    return {
        "status": "ok",
        "service": "CyberShield Voice AI",
        "components": {
            "gnani_prisma_stt": bool(GNANI_API_KEY),
            "gnani_timbre_tts": bool(GNANI_API_KEY),
            "gemini": bool(GEMINI_API_KEY) and _gemini_enabled(),
            "rule_engine": True
        },
        "gemini_models": _model_chain()
    }


# The web page is served by the same server, so a public demo needs ONE URL:
# http://127.0.0.1:8000/app/  (local)  or  https://<your-host>/app/  (deployed)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount(
        "/app",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend"
    )


def build_result(text):
    started = time.perf_counter()
    rule_analysis = analyze_text(text)
    rules_done = time.perf_counter()
    ai_analysis = analyze_with_gemini(text)
    gemini_done = time.perf_counter()

    final_analysis = combine_verdicts(
        rule_analysis,
        ai_analysis
    )

    if not isinstance(ai_analysis, dict) or not ai_analysis.get("enabled"):
        gemini_status = "off"
    elif ai_analysis.get("error"):
        gemini_status = "quota" if ai_analysis.get("error") == "QuotaExceeded" else "error"
    else:
        gemini_status = "ok"

    return {
        "transcript": text,
        "analysis": final_analysis,
        "rule_analysis": rule_analysis,
        "ai_analysis": ai_analysis,
        "pipeline": {
            "rules_ms": round((rules_done - started) * 1000),
            "gemini_ms": round((gemini_done - rules_done) * 1000),
            "gemini_status": gemini_status
        },
        "disclaimer": (
            "This is an assistive risk assessment, not a guarantee "
            "that a message is safe or fraudulent."
        )
    }


def _timed_transcribe(filename, content, language_code):
    """Run Gnani Prisma STT and report how long it took (milliseconds)."""
    started = time.perf_counter()
    stt = transcribe_audio(filename, content, language_code)
    return stt, round((time.perf_counter() - started) * 1000)


@app.post("/api/analyze-text")
def analyze_message(payload: TextRequest):
    if not payload.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide message text."
        )

    return build_result(payload.text)


@app.post("/api/analyze-audio")
async def analyze_audio(
    audio: UploadFile = File(...),
    language_code: str = Form("indic-auto")
):
    suffix = Path(audio.filename or "").suffix.lower()

    browser_formats = {".webm", ".mp4"}

    if suffix not in ALLOWED_AUDIO_EXTENSIONS and suffix not in browser_formats:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. Use: "
                + ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
                + ", .webm, .mp4"
            )
        )

    content = await audio.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio file is empty."
        )

    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large. Maximum upload size is 15 MB."
        )

    try:
        if suffix in browser_formats:
            # Convert browser recording to 16 kHz mono WAV
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = Path(temp_dir) / f"recording{suffix}"
                output_path = Path(temp_dir) / "recording.wav"

                input_path.write_bytes(content)

                try:
                    subprocess.run(
                        [
                            ffmpeg_exe,
                            "-y",
                            "-i", str(input_path),
                            "-vn",
                            "-ar", "16000",
                            "-ac", "1",
                            "-c:a", "pcm_s16le",
                            str(output_path)
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                except subprocess.TimeoutExpired:
                    raise HTTPException(
                        status_code=422,
                        detail="Audio conversion timed out. Please try a shorter recording."
                    )

                except subprocess.CalledProcessError as exc:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            "Audio conversion failed. Please record again. "
                            + (exc.stderr or "")[-500:]
                        )
                    )

                if not output_path.exists():
                    raise HTTPException(
                        status_code=422,
                        detail="Audio conversion failed."
                    )

                audio_content = output_path.read_bytes()

                stt, stt_ms = _timed_transcribe(
                    "recording.wav",
                    audio_content,
                    language_code
                )

        else:
            # Existing supported audio formats
            stt, stt_ms = _timed_transcribe(
                audio.filename or "recording.wav",
                content,
                language_code
            )

        if not stt["transcript"].strip():
            raise HTTPException(
                status_code=422,
                detail="No speech detected. Try a clearer recording."
            )

        result = build_result(stt["transcript"])
        result["pipeline"]["stt_ms"] = stt_ms

        result["transcription"] = {
            "model": stt["model"],
            "detected_language_code": stt["detected_language_code"],
            "request_id": stt["request_id"]
        }

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )


@app.post("/api/speak")
def speak(payload: SpeakRequest):
    if not payload.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text is required."
        )

    try:
        audio_content = synthesize_warning(
            payload.text,
            payload.language
        )

        return Response(
            content=audio_content,
            media_type="audio/wav",
            headers={
                "Content-Disposition": (
                    'inline; filename="cybershield-warning.wav"'
                )
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )
