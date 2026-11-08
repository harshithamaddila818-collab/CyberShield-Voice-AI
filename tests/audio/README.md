# Voice samples for the Prisma benchmark

1. Record each sentence in `labels.csv` (column `reference`) in your own voice, 5–15 seconds each.
   Phone voice recorder or the app's microphone button is fine. Read the sentence naturally.
2. Save the clips in THIS folder, named by id: `v01.m4a`, `v02.wav`, `v03.mp3` … (wav, mp3, m4a, ogg, flac, aac).
   Missing clips are skipped, so you can start with a few.
3. From the project root run (needs `GNANI_API_KEY` in `.env`):

       python -m tests.run_voice_benchmark

   Add `--hybrid` to also use Gemini (uses quota).
4. The script prints the table and writes `tests/voice_results.md`. Paste the real numbers into the README.

What it measures
- **WER** (word error rate) of Gnani Prisma against your reference sentence.
- **Text-only** detection (reference text) vs **voice** detection (Prisma transcript): shows how much speech recognition affects the verdict.
- Precision, recall, F1 and false-positive rate on the voice clips (scam = MEDIUM/HIGH).

Honest limits: one speaker, your own accent and microphone, short scripted sentences. Report it exactly that way.
