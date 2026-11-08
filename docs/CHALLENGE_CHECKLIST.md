# Challenge requirements checklist

Sources: press coverage of the challenge ([CXOToday](https://cxotoday.com/media-coverage/gnani-ai-launches-the-great-indian-ai-internship-challenge/),
[FintechBizNews](https://fintechbiznews.com/fintech-technology/great-indian-ai-internship-challenge-by-gnani-ai)) and the project brief.
The official rules and judging criteria are on **gnani.ai/internship**; they were not available when this was written. Check them and tick the last column yourself.

| Requirement | Status | Evidence |
|---|---|---|
| Identify a real user need | done | Scam messages and calls in Telugu; voice-first, Telugu-first (README intro) |
| Working solution built with Gnani models/APIs | done | Prisma STT + Timbre TTS in the main flow (`prisma_service.py`, `timbre_service.py`) |
| Meaningful, visible use of Gnani | done | Voice scan auto-detects language, answers with a spoken warning in that language; pipeline strip shows each Gnani step |
| Gnani **Evon** | **open** | Not found in public documentation; not used. Read gnani.ai/internship to see whether it is required |
| Show how it could make a difference | partly | Impact argument is qualitative; no user study, no real-world numbers |
| Documentation | done | README, architecture diagram, API table, limitations |
| Testing and measured results | partly | 4 automated suites; rules benchmark (honest blind numbers); voice and hybrid benchmarks **not run yet** |
| Public demo | **to do** | `render.yaml` ready, not deployed. Fallback: demo video + GitHub repo |
| Demo video | **to do** | `DEMO_SCRIPT.md` |
| LinkedIn / X post | **to do** | `LINKEDIN_POST.md` (add the video and GitHub links) |
| Submit before **10 Nov 2026** | **to do** | |
