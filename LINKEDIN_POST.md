## LinkedIn / X post (edit the bracketed parts)

🛡️ I built **CyberShield Voice AI** for the Gnani.ai "Great Indian AI Internship Challenge".

Scam calls, WhatsApp voice notes and SMS in India often arrive in Telugu, and most scam checkers only read English text.
CyberShield is voice-first: speak or upload a message and it tells you whether it is a scam, why, and speaks a warning back in the same language.

🎙️ Gnani Prisma STT: Telugu / English speech to text, language auto-detected
🧠 Bilingual rule engine + Gemini, combined by an explicit fusion rule (AI can raise a score, never decide alone)
🔊 Gnani Timbre TTS: a warning written for that message, spoken in Telugu or English

What I learned (the honest part): my rules scored 100% on messages I had tuned them on, but only about 42% recall on scam types they had never seen, with 0 false alarms on 92 genuine messages. Measuring on fresh, never-tuned sets is what pushed me to make Gemini a second opinion instead of the only brain. I also made the Gemini calls free-tier safe (cache, model fallback, quota memory) and fixed a 100-second hang caused by IPv6 on my network.

Stack: FastAPI · Python · Gemini · Gnani Prisma & Timbre · HTML/CSS/JS · 35 automated checks + a 184-message benchmark
Demo: [video link]  |  Code: [GitHub link]

#GnaniAI #VoiceAI #Telugu #CyberSecurity #GenAI #IndiaAI
