from backend.services.threat_engine import analyze_text

r = analyze_text("OTP చెప్పండి వెంటనే")
print(r["risk_score"], r["risk_level"], r["threat_type"])