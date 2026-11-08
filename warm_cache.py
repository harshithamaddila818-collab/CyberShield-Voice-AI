"""Run ONCE when Gemini quota is available:  python warm_cache.py
Saves Gemini's answer for your demo messages in ~/.cybershield/gemini_cache.json.
Later, scanning the SAME message needs no Gemini request (works even when quota is over).
Edit DEMO_MESSAGES to the exact texts you will use in your demo video."""
import time

from backend.services.gemini_service import analyze_with_gemini

DEMO_MESSAGES = [
    "Your SBI account is blocked. Share the OTP immediately to unblock it.",
    "Dear customer, your KYC is expired. Click http://sbi-kyc-update.top to update now or account will be suspended.",
    "Congratulations! You won Rs 25 lakh lottery. Pay Rs 5000 processing fee to claim.",
    "123456 is your OTP for login. Do not share this code with anyone.",
]

for i, text in enumerate(DEMO_MESSAGES, 1):
    result = analyze_with_gemini(text)
    status = result.get("error") or ("ok: " + str(result.get("threat_type")))
    print(f"{i}/{len(DEMO_MESSAGES)} -> {status}")
    if result.get("error") == "QuotaExceeded":
        print("Quota over. Try again after it resets.")
        break
    time.sleep(7)  # stay well below the per-minute limit
