# 🛡️ CyberShield Voice AI

**Speak or paste a suspicious message. Get a verdict, the reasons, and a spoken warning in Telugu or English.**

Built for the Gnani.ai *Great Indian AI Internship Challenge*. The idea: many Indians get scam
calls, WhatsApp voice notes and SMS in **Telugu**, and most scam checkers only read English text.
CyberShield is **voice-first**: a recording goes in, a spoken warning in the speaker's language comes out.

<p align="center">
  <img src="docs/screenshots/voice-flow-preview.png" width="640" alt="Voice scan result with pipeline strip"><br>
  <em>UI capture from a local test run (Gnani and Gemini calls were stubbed for the capture, so the timings shown are not real).</em>
</p>

## How Gnani AI is used (core of the product, not an add-on)

| Step | Gnani product | What it does here |
|---|---|---|
| 1. Listen | **Prisma STT** | Turns a Telugu / English recording (≤ 30 s) into text and auto-detects the language. Browser recordings are converted to 16 kHz WAV first. |
| 2. Decide | rules + Gemini | Scam verdict (see below) |
| 3. Warn | **Timbre TTS** | Speaks a warning written for *this* message, **in the language the speaker used** (Telugu voice for Telugu audio). A voice scan plays it automatically. |

The result page shows a **"How this result was produced"** strip with the time each stage took
(Prisma → rules → Gemini → Timbre), so the Gnani steps are visible, not hidden.

## Architecture

```mermaid
flowchart LR
    U["User: voice or text"] --> FE["Web app (HTML / CSS / JS)"]
    FE -- "audio" --> API["FastAPI backend"]
    API -- "recording" --> PR["Gnani Prisma STT"]
    PR -- "transcript + language" --> API
    API --> RULES["Rule engine<br/>Telugu + English + Tenglish<br/>genuine-OTP guard"]
    API --> GEM["Gemini<br/>cache · model fallback · quota guard"]
    RULES --> FUSE["Fusion<br/>Gemini can raise a score,<br/>never decide alone"]
    GEM --> FUSE
    FUSE -- "verdict JSON" --> FE
    FE -- "warning text + language" --> API
    API -- "text" --> TT["Gnani Timbre TTS"]
    TT -- "Telugu / English WAV" --> FE
```

## How the verdict is decided (not a plain average)

1. **Rule engine** (`backend/services/threat_engine.py`): specific Indian scam patterns (OTP, KYC, digital arrest,
   UPI collect, fake jobs, electricity, loan, courier, prize, remote access, refund, family emergency…) in Telugu,
   English and Tenglish; a *signal-combination* layer (two or more different scam ingredients together, one alone never
   counts, capped at MEDIUM); and a **genuine-OTP guard** so a real "Do not share this code" message stays LOW.
2. **Gemini** gives an independent opinion (threat type, confidence, explanation, voice script).
3. **Fusion** (`combine_verdicts`): Gemini can only **raise** the score.
   Rules found something and Gemini strongly agrees → **HIGH**. Rules found nothing → Gemini alone reaches **MEDIUM at most**,
   so an AI mistake or a prompt-injected message cannot create a HIGH alert alone. A genuine-OTP notice always stays LOW.
   If Gemini is unavailable the rule result is shown and nothing breaks.

## Measured accuracy: rules only (no Gemini)

Scam = MEDIUM/HIGH, genuine = LOW. Reproduce: `python -m tests.run_benchmark`.
All messages were written by the project author (184 in total: 92 scam, 92 genuine; Telugu, English, Tenglish, tricky genuine alerts).

| Message set | n | Precision | Recall | False-positive rate | Note |
|---|---|---|---|---|---|
| DEV / HELD-OUT / HARD | 81 | 100% | 100% | 0% | used while designing patterns, **not evidence** |
| BLIND, first run | 24 | 100% | 33.3% | 0% | before tuning on it |
| BLIND2, first run | 24 | 100% | 41.7% | 0% | before tuning on it |
| BLIND3, first run | 31 | 83.3% | 66.7% | 12.5% | the 2 false alarms were genuine-OTP guard bugs, fixed afterwards |
| **BLIND4 (new scam types, run once, never tuned on)** | **24** | **100%** | **41.7%** | **0%** | **the honest generalisation number** |
| All 184 after fixes | 184 | 100% | 88.0% | 0% | optimistic: most sets were tuned on |

**Honest reading.** The rules almost never raise a false alarm (0 of 92 genuine messages), but on scam types they
have never seen they catch only about **40%**. That is exactly why Gemini is part of the pipeline. The combined
rules + Gemini accuracy has **not** been measured yet (free-tier quota): `python -m tests.run_hybrid_benchmark` measures it on BLIND4.
The benchmark is small and self-written, so treat the numbers as indicative, not as a production accuracy claim.

### Voice benchmark (Prisma on real recordings)

`tests/audio/labels.csv` holds 20 scripted Telugu / English sentences (10 scam, 10 genuine). Record them, drop the clips
in `tests/audio/`, run `python -m tests.run_voice_benchmark`. It reports Prisma word-error-rate, precision, recall, F1 and
false-positive rate on the **voice path** versus the **text path**. *Results: not run yet, no recordings are included.*
(On the 20 reference sentences as text, rules alone score precision 100% / recall 60%; number words and Telugu
verb-final word order were the main gaps and were then fixed.)

## Automated tests

| Command | What it checks | Status |
|---|---|---|
| `python -m tests.run_benchmark` | detection metrics on 184 messages | passes |
| `python -m tests.test_fusion` | Gemini + rules fusion rules (8 cases) | 8/8 |
| `python -m tests.test_api` | all endpoints, response structure, limits, rate limit, CORS (18 checks, Gnani faked) | 18/18 |
| `python -m tests.test_gemini_resilience` | model fallback, 404/429/503, quota memory, cache, off-switch against a local fake Gemini server (9 checks) | 9/9 |

Real Gnani Prisma / Timbre calls and real Gemini calls are exercised by hand on the author's machine; they are not part of the automated tests.

## Reliability and security

- **Gemini free tier:** result cache, automatic fallback between models, memory of quota (no wasted calls after a 429),
  retired-model (404) and overload (503) handling, 12 s timeout, IPv4-only connection (fixes ~100 s hangs seen on some networks).
- **Per-IP rate limit** on analyze/speak endpoints (`RATE_LIMIT_PER_MIN`, default 30), input size limits, audio type and size checks.
- **API keys** only in `.env` / host environment, never in the repo. `CORS_ORIGINS` can restrict browser origins.
- **Privacy:** message text is sent to Gemini for analysis and audio to Gnani Prisma; scan history is stored locally (SQLite) and can be deleted in the app.

## Run it locally (Windows PowerShell, one command at a time)

```
cd CyberShield-Voice-AI
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env        # open .env and add GNANI_API_KEY and GEMINI_API_KEY
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/app/** (the backend serves the page, one URL). Developing with VS Code Live Server
(`frontend/index.html` on port 5500) also still works. Restart uvicorn after backend code changes.

Health check: http://127.0.0.1:8000/health · API docs: http://127.0.0.1:8000/docs

## Deploy a public demo (Render, free tier)

`render.yaml` is included. Push the repo to GitHub → Render → *New* → *Blueprint* → choose the repo → add
`GNANI_API_KEY` and `GEMINI_API_KEY` in *Environment*. Public URL: `https://<your-service>.onrender.com/app/`.
The free tier sleeps when idle (first load can take ~1 min) and its disk is temporary (history resets). *Not yet deployed or tested on Render.*
Keep `RATE_LIMIT_PER_MIN` low on a public demo so visitors cannot use up your Gnani credits and Gemini quota.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | status of Gnani / Gemini / rules |
| POST | `/api/analyze-text` | `{ "text": "..." }` → `analysis`, `rule_analysis`, `ai_analysis`, `pipeline` |
| POST | `/api/analyze-audio` | audio file → Prisma transcript → same result + `transcription`, `pipeline.stt_ms` |
| POST | `/api/speak` | `{ "text", "language" }` → Timbre WAV |
| GET/POST/DELETE | `/api/history` | scan history |
| POST | `/api/report-pdf` | PDF report |
| POST | `/api/scan-url` | offline URL structure check |
| POST | `/api/emergency-guidance` | recovery steps |

## Project structure

```
backend/   main.py · config.py · security.py · features.py
           services/ prisma_service.py · timbre_service.py · gemini_service.py · threat_engine.py
frontend/  index.html · style.css · script.js · features.js
tests/     benchmark_messages.py · run_benchmark.py · run_voice_benchmark.py · run_hybrid_benchmark.py
           test_fusion.py · test_api.py · test_gemini_resilience.py · audio/ (voice-sample scripts)
docs/      screenshots/ · CHALLENGE_CHECKLIST.md
warm_cache.py   pre-saves Gemini answers for the demo messages
```

## Limitations

- Assistive tool, **not** a guarantee that a message is safe or fraudulent. URL check is offline structure only.
- Rule recall on unseen scam types is about 40%; the rules + Gemini accuracy is unmeasured; the voice benchmark has not been run.
- Gemini free-tier quota limits how many new messages can be analysed per day (cache and fallback soften this).
- Single-instance demo design: rate limit and cache are in memory.
