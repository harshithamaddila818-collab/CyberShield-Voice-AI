# CyberShield Voice AI – 2-minute demo script (voice-first)

**Before recording:** run `python warm_cache.py` (while Gemini quota is available) so your text demo messages answer
instantly. Start uvicorn, open http://127.0.0.1:8000/app/ and press Ctrl+F5. Record two short voice clips first
(one Telugu scam call, one genuine message) so the demo does not depend on live speaking.

| Time | Do | Say |
|---|---|---|
| 0:00 | Home page | "Scam calls and WhatsApp voice notes in Telugu reach people every day, and most checkers only read English text. CyberShield listens." |
| 0:15 | Upload the **Telugu scam clip** → Analyze Audio | "Gnani Prisma turns the Telugu speech into text and detects the language." |
| 0:35 | Point at the result + the **How this result was produced** strip | "Verdict with reasons. Below you can see each stage: Prisma, rules, Gemini, and Gnani Timbre." |
| 0:50 | The Telugu voice warning plays by itself | "Timbre answers in Telugu, the language the speaker used. The warning is written for this message." |
| 1:10 | Paste the English scam text (`Your SBI account is blocked. Share the OTP immediately to unblock it.`) | "Same pipeline for text: HIGH, 75, with the reason: it asks for an OTP." |
| 1:25 | Paste the genuine OTP (`123456 is your OTP for login. Do not share this code with anyone.`) | "A real bank OTP stays LOW. A genuine-message guard stops false alarms." |
| 1:40 | Scroll to the toolkit: PDF report, history, URL check | "Reports, history, URL checks and recovery steps." |
| 1:50 | Show the README accuracy table | "Rules alone: 0 false alarms in 92 genuine messages, but only ~40% recall on new scam types. So Gemini adds a second opinion, and it can raise a score but never decide alone." |

**If Gemini is slow or out of quota:** the page still shows the rule result at once and the pipeline strip says so. Present it as a built-in safety net.
