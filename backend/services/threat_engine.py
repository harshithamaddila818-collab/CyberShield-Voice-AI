
import re
from urllib.parse import urlparse

"""Bilingual rule engine for Indian scam detection."""

PATTERNS = [
    # OTP disclosure requests
        (
        r"(?:share|tell|send|reveal|forward|provide).{0,45}(?:otp|one.?time password|verification code)|"
        r"(?:otp|one.?time password|verification code).{0,45}(?:share|tell|send|reveal|forward)|"
        r"(?:ఓటిపి|ఓటీపీ|పిన్).{0,35}(?:చెప్ప|పంప|షేర్)|"
        r"(?:చెప్ప|పంప|షేర్).{0,35}(?:ఓటిపి|ఓటీపీ|పిన్)|"
        r"(?:ఓటిపి|ఓటీపీ).{0,25}(?:చెప్పండి|పంపండి|ఇవ్వండి)|"
        r"(?:చెప్పండి|పంపండి|ఇవ్వండి).{0,25}(?:ఓటిపి|ఓటీపీ)|"
        r"\bOTP\b.{0,25}(?:చెప్పండి|పంపండి|ఇవ్వండి)|"
        r"(?:చెప్పండి|పంపండి|ఇవ్వండి).{0,25}\bOTP\b",
        75,
        "Asks the recipient to disclose an OTP or verification code",
        "OTP scam"
    ),
    # Banking credentials
    (
        r"(?:upi pin|debit card pin|cvv|card number|net.?banking password).{0,45}(?:enter|share|send|tell|provide)|"
        r"(?:enter|share|send|tell|provide).{0,45}(?:upi pin|debit card pin|cvv|net.?banking password)|"
        r"(?:యూపీఐ పిన్|యుపిఐ పిన్|సివివి).{0,35}(?:చెప్ప|పంప|ఎంటర్)",
        60,
        "Requests sensitive banking credentials",
        "Banking credential scam"
    ),

    # Digital arrest
    (
        r"digital arrest|under digital arrest|video call.{0,35}(?:police|cbi|customs)|"
        r"(?:cbi|police|customs).{0,45}(?:arrest|investigation|video call)|"
        r"డిజిటల్ అరెస్ట్|వీడియో కాల్.{0,30}(?:పోలీసు|సీబీఐ)|"
        r"పోలీసులమని.{0,30}(?:చెప్పి|బెదిరించి)",
        85,
        "Uses digital-arrest threats or impersonates law enforcement",
        "Digital arrest scam"
    ),

    # UPI collect/payment fraud
    (
        r"(?:approve|accept|pay).{0,35}(?:upi )?(?:collect|payment) request|"
        r"(?:upi )?collect request|request money.{0,35}(?:upi|pin)|"
        r"(?:receive|get).{0,25}money.{0,35}(?:scan|qr|pin)|"
        r"scan.{0,25}qr.{0,35}(?:receive|get|refund|payment)|"
        r"కలెక్ట్ రిక్వెస్ట్|డబ్బులు పొందడానికి.{0,30}(?:పిన్|క్యూఆర్)|"
        r"డబ్బులు రావాలంటే.{0,30}(?:పిన్|క్యూఆర్)",
        75,
        "Asks the recipient to approve a payment or enter a PIN to receive money",
        "UPI payment scam"
    ),

    # Fake job/task scams
    (
        r"(?:part.?time|work from home|telegram task|like.{0,15}review).{0,70}(?:deposit|recharge|investment|task|commission|earning)|"
        r"(?:deposit|recharge|pay).{0,45}(?:to get|unlock|complete).{0,30}(?:task|job|earning|commission)|"
        r"registration fee.{0,40}(?:job|work|interview)|"
        r"టాస్క్.{0,35}(?:డిపాజిట్|రీఛార్జ్|డబ్బు)|"
        r"పని ఇస్తామని.{0,30}(?:ఫీజు|డిపాజిట్)",
        75,
        "Promises job earnings but requires deposits, recharges, or paid tasks",
        "Fake job/task scam"
    ),

    # Electricity disconnection scams
    (
        r"(?:electricity|power).{0,50}(?:disconnect|cut off|suspend).{0,40}(?:today|tonight|hours|pay)|"
        r"(?:pay|click).{0,35}(?:electricity|power) bill.{0,35}(?:avoid|prevent).{0,20}(?:disconnect|cut)|"
        r"(?:electricity|power).{0,70}(?:pay immediately|payment immediately|click here)|"
        r"విద్యుత్.{0,35}(?:కట్|డిస్‌కనెక్ట్|నిలిపి)|"
        r"కరెంట్.{0,35}(?:కట్|తీసేస్తా)",
        75,
        "Threatens immediate electricity disconnection to pressure payment",
        "Electricity bill scam"
    ),

    # KYC scams
    (
        r"(?:kyc|know your customer).{0,45}(?:blocked|expired|suspend|update immediately|verify now)|"
        r"(?:account|bank).{0,35}kyc.{0,35}(?:block|suspend)|"
        r"కేవైసీ.{0,35}(?:అప్‌డేట్|బ్లాక్|గడువు)|"
        r"కెవైసి.{0,35}(?:అప్‌డేట్|బ్లాక్)|"
        r"(?:kyc|కేవైసీ|కెవైసి).{0,70}(?:బ్లాక్|సస్పెండ్|గడువు|క్లోజ్|నిలిపి)",
        60,
        "Uses an urgent KYC/account-blocking claim",
        "KYC scam"
    ),

    # Loan scams
    (
        r"(?:loan app|instant loan).{0,50}(?:processing fee|upfront fee|advance fee)|"
        r"(?:pay|send).{0,30}(?:advance|processing).{0,20}fee.{0,30}(?:loan|approval)|"
        r"లోన్.{0,35}(?:ముందస్తు ఫీజు|ప్రాసెసింగ్ ఫీజు)",
        65,
        "Requests an upfront fee for loan approval",
        "Loan scam"
    ),

    # Courier scams
    (
        r"(?:courier|parcel|customs).{0,60}(?:held|seized|illegal|pending).{0,40}(?:pay|fee|link)|"
        r"(?:delivery|parcel).{0,40}(?:small fee|redelivery fee).{0,35}(?:link|pay)|"
        r"కొరియర్.{0,35}(?:ఆపారు|పట్టుకున్నారు|ఫీజు)",
        60,
        "Uses a parcel/customs problem to demand payment",
        "Courier scam"
    ),

    # Fake customer care / remote access
    (
        r"(?:customer care|helpline|support).{0,45}(?:anydesk|teamviewer|screen share|remote access)|"
        r"(?:install|download).{0,35}(?:anydesk|teamviewer|remote access)|"
        r"(?:refund|cashback).{0,40}(?:scan|qr|upi pin)|"
        r"కస్టమర్ కేర్.{0,35}(?:యాప్|స్క్రీన్ షేర్)",
        65,
        "Requests remote access or uses a suspicious refund flow",
        "Fake customer-care scam"
    ),

    # Authority impersonation
    (
        r"(?:police|cbi|customs|rbi officer|bank officer).{0,50}(?:arrest|case|account|money laundering)|"
        r"(?:arrest|legal action).{0,35}(?:pay|transfer|settle)|"
        r"పోలీసులు.{0,35}(?:అరెస్ట్|కేసు)|అరెస్ట్ చేస్తామని",
        55,
        "Uses authority impersonation or legal threats",
        "Impersonation scam"
    ),

    # Prize scams
    (
        r"(?:won|winner|claim).{0,35}(?:lottery|prize|gift|reward).{0,40}(?:fee|tax|pay)|"
        r"(?:lottery|prize).{0,40}(?:processing fee|claim fee)|"
        r"లాటరీ.{0,30}(?:గెలిచారు|బహుమతి).{0,30}(?:ఫీజు|చెల్లించు)",
        55,
        "Promises a prize but asks for a fee",
        "Prize scam"
    ),

    # Account locked / suspended + a request to act (English)
    (
        r"(?:account|wallet|card|sim|number).{0,40}(?:locked|blocked|suspended|frozen|deactivated|disconnected|deactivation).{0,90}(?:reactivate|verify now|update now|click|link|press \d|download|call (?:this|our)|speak to)|"
        r"(?:mobile|sim|phone) number.{0,40}(?:will be )?(?:disconnect|deactivat|block).{0,70}(?:press \d|call|speak|officer)",
        55,
        "Claims your account or number is locked and pushes you to act",
        "Account lock scam"
    ),

    # Asking the user to read out / hand over a received code (OTP social engineering)
    (
        r"(?:sent|received|got|came).{0,35}(?:code|otp|pin).{0,70}(?:read (?:it )?out|read (?:it )?to|tell (?:me|us)|give (?:me|us)|share|send (?:it|me|us))|"
        r"(?:read out|tell me|give me).{0,25}(?:the )?(?:code|otp|pin)|"
        r"(?:otp|ఓటిపి|ఓటీపీ|pin).{0,25}(?:cheppandi|cheppu|chepandi|pampandi|ivvandi|share cheyyandi)",
        75,
        "Asks the recipient to read out or hand over a received code",
        "OTP scam"
    ),

    # Earn-money / task scams with a payment to start
    (
        r"(?:earn|income|salary).{0,40}(?:per day|a day|daily|/day).{0,90}(?:telegram|whatsapp|first pay|pay rs|deposit|join)|"
        r"(?:like|liking|review|rating).{0,30}(?:video|videos|youtube|product).{0,70}(?:earn|commission|paid|pay)|"
        r"(?:first )?pay (?:rs\.?|₹)? ?\d+.{0,40}(?:activate|unlock|start|join)|"
        r"(?:రిజిస్ట్రేషన్ ఫీజు|రిజిస్ట్రేషన్ ఛార్జ్).{0,40}(?:కట్ట|చెల్లి|ఉద్యోగం|ఆఫర్)|"
        r"(?:ఉద్యోగం|జాబ్).{0,60}(?:ఫీజు|డిపాజిట్).{0,25}(?:కట్ట|చెల్లి|చేయండి)",
        75,
        "Promises easy earnings or a job but asks you to pay first",
        "Fake job/task scam"
    ),

    # Legal / government impersonation (Aadhaar, TRAI, tax)
    (
        r"(?:aadhaar|aadhar|pan card|sim card).{0,60}(?:suspended|blocked|illegal|misuse|cancelled).{0,110}(?:officer|police|arrest|contact|call|whatsapp)|"
        r"(?:cyber ?crime|narcotics|customs) officer.{0,60}(?:whatsapp|call|contact|arrest)",
        70,
        "Impersonates a government or law-enforcement officer",
        "Impersonation scam"
    ),

    # Refund / tax refund that needs bank or card details
    (
        r"(?:refund|cashback|reward).{0,60}(?:pending|approved|credited|waiting).{0,100}(?:submit|enter|share|verify|provide).{0,40}(?:bank|card|account) details|"
        r"(?:submit|enter|share|provide).{0,30}(?:your )?(?:bank|card|debit card|credit card) (?:details|number)",
        60,
        "Asks for your bank or card details to release a refund",
        "Refund scam"
    ),

    # Telugu written in English letters (Tenglish)
    (
        r"(?:kyc|account|akkaunt).{0,60}(?:lekapothe|leka pothe|lekunte|cheyyakapothe).{0,40}(?:block|close|suspend)|"
        r"(?:account|akkaunt).{0,30}(?:block|close|suspend) ?(?:avutundi|avuthundi|avtundi|avuthundi)|"
        r"(?:kyc|aadhaar|pan).{0,25}update cheyyandi",
        60,
        "Warns that your account will be closed unless you act (Tenglish)",
        "KYC scam"
    ),

    # Telugu: remote screen sharing / app download for "customer care"
    (
        r"స్క్రీన్ షేర్.{0,40}(?:చేయండి|చేయమని)|(?:యాప్).{0,30}డౌన్లోడ్.{0,60}(?:స్క్రీన్ షేర్|కస్టమర్ కేర్)",
        65,
        "Asks you to share your screen or install an app for remote help",
        "Fake customer-care scam"
    ),

    # Suspicious links
    (
        r"(?:click|open).{0,25}(?:link|here).{0,45}(?:verify|update|block|claim)|"
        r"(?:bit\.ly|tinyurl\.com|t\.co|cutt\.ly)",
        15,
        "Pressures the recipient to open a link or uses a URL shortener",
        "Suspicious link"
    ),

    # Urgency combined with an action
    (
        r"(?:urgent|immediately|right now|within \d+ minutes|వెంటనే|అత్యవసరం|తక్షణమే).{0,50}(?:pay|click|share|verify|transfer|చెల్లించు|పంపు)",
        15,
        "Combines urgency with a requested action",
        "Social engineering"
    ),
]


# ---------------------------------------------------------------------------
# Generic "signal combination" layer.
# Specific patterns above only catch wording we have seen. Scams usually mix
# several of these ingredients, so when TWO OR MORE different ingredients
# appear together we add a moderate score. One ingredient alone never counts
# (so normal messages that mention "pay" or "OTP" are not flagged).
# The generic layer can reach MEDIUM only; it cannot make a message HIGH.
# ---------------------------------------------------------------------------
GENERIC_SIGNALS = [
    (
        "secret",
        40,
        "Asks you to confirm, enter or hand over a secret code or PIN",
        r"(?:\botp\b|\bpin\b|\bcvv\b|password|verification code|ఓటిపి|ఓటీపీ|పిన్).{0,40}"
        r"(?:confirm|enter|share|tell|send|give|read|provide|ఎంటర్|చెప్ప|పంప)|"
        r"(?:confirm|enter|share|tell|send|give|read|provide|ఎంటర్|చెప్ప|పంప).{0,40}"
        r"(?:\botp\b|\bpin\b|\bcvv\b|password|verification code|ఓటిపి|ఓటీపీ|పిన్)"
    ),
    (
        "payment",
        20,
        "Demands a payment or fee",
        # amount = digits, Rs/₹, or number words (speech-to-text often spells amounts out)
        r"(?:\bpay\b|\bsend\b|\btransfer\b|\bdeposit\b|చెల్లించ|కట్టండి|పంపండి).{0,45}"
        r"(?:rs\.?|₹|inr|\d{2,}|\b(?:hundred|thousand|lakh|lakhs|crore|rupees)\b|వేలు|వేల|లక్షలు|లక్ష|కోట్లు|రూపాయ)|"
        r"(?:\bpay\b|\bsend\b|\bdeposit\b|చెల్లించ).{0,35}(?:fee|charge|charges|advance|deposit|ఫీజు|ఛార్జ్)|"
        r"(?:fee|charges|dues)\b.{0,25}(?:rs\.?|₹|\d{2,})|(?:rs\.?|₹)\s?\d.{0,40}(?:fee|charges|dues)|"
        r"డబ్బు(?:లు)?.{0,20}(?:పంపండి|కట్టండి|చెల్లించండి)|"
        # Telugu word order is verb-final: "<amount> <verb>"
        r"(?:రూపాయలు|రూపాయ|వేలు|వేల|లక్షలు|లక్ష|కోట్లు|\d{2,}).{0,25}"
        r"(?:కట్టండి|చెల్లించండి|పంపండి|డిపాజిట్ చేయండి|జమ చేయండి)"
    ),
    (
        "emergency",
        20,
        "Claims a family emergency and asks for urgent money",
        r"accident|hospital|kidnap|in police custody|medical emergency|ప్రమాదం|ఆసుపత్రి"
    ),
    (
        "income",
        15,
        "Promises easy income or a work-from-home job",
        r"work from home|part.?time job|earn(?:ing)?\b.{0,30}(?:daily|per day|a day|weekly|monthly)|"
        r"ఇంటి నుండి పని|ఇంటి నుంచి పని|రోజుకు.{0,15}సంపాదించ"
    ),
    (
        "fear",
        20,
        "Uses a threat such as blocking, cancelling, arrest or disconnection",
        r"arrest|blocked|\blocked\b|suspend|cancel(?:led)?\b|disconnect|freez|frozen|on hold|deactivat|illegal|"
        r"misuse|legal action|cut off|నిలిపి|అరెస్ట్|బ్లాక్|కట్ చేస్|క్లోజ్|దుర్వినియోగ|సస్పెండ్"
    ),
    (
        "lure",
        15,
        "Offers something too good to be true (prize, refund, free item, subsidy)",
        r"\bfree\b|\bwin\b|\bwon\b|lucky|prize|lottery|subsidy|cashback|refund|సబ్సిడీ|బహుమతి|లాటరీ"
    ),
    (
        "contact",
        15,
        "Pushes you to open a link, scan a QR code or contact an unknown number or officer",
        r"https?://|www\.|bit\.ly|whatsapp|\bqr\b|క్యూఆర్|scan|లింక్|(?:contact|call).{0,25}(?:officer|number|executive)|కాల్ చేసి|కాల్ చేయండి|వాట్సాప్"
    ),
]
GENERIC_MAX_SCORE = 55

URL_RE = re.compile(
    r"https?://[^\s<>()]+|www\.[^\s<>()]+",
    re.IGNORECASE
)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co",
    "is.gd", "cutt.ly", "rb.gy"
}

SUSPICIOUS_TLDS = (
    ".xyz", ".top", ".click",
    ".work", ".loan", ".shop"
)


def inspect_url(url):
    url = url.rstrip(".,!?;:")
    parsed = urlparse(
        url if "://" in url else "https://" + url
    )
    host = (parsed.hostname or "").lower()

    score = 0
    reasons = []

    if not host:
        return {
            "url": url,
            "risk": "unknown",
            "score": 0,
            "reasons": ["Could not parse URL"]
        }

    if host in SHORTENERS:
        score += 25
        reasons.append("URL shortener hides the final destination")

    if host.endswith(SUSPICIOUS_TLDS):
        score += 15
        reasons.append("Uses a less common domain ending")

    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        score += 25
        reasons.append("Uses an IP address instead of a normal domain")

    if "@" in url:
        score += 20
        reasons.append("Contains an @ symbol that may disguise the destination")

    if host.startswith("xn--") or ".xn--" in host:
        score += 15
        reasons.append("Contains an internationalized/punycode domain")

    return {
        "url": url,
        "host": host,
        "risk": (
            "suspicious" if score >= 25
            else "review" if score > 0
            else "no obvious signal"
        ),
        "score": min(score, 100),
        "reasons": reasons
    }


def _is_genuine_otp_notice(text):
    """Identify informational OTP notices that explicitly warn against sharing."""
    lower = text.lower()

    has_otp = bool(re.search(
        r"\botp\b|one.?time password|"
        r"(?:verification|security|login|sign.?in|confirmation) code|passcode|"
        r"ఓటిపి|ఓటీపీ",
        lower
    ))

    explicit_do_not_share = bool(re.search(
        r"do not (?:ever )?(?:share|give|tell|forward)|don't (?:share|give|tell)|"
        r"never (?:share|give|tell)|not to share|"
        r"కావద్దు.*(?:ఓటిపి|ఓటీపీ)|"
        r"ఎవరికీ.{0,20}(?:చెప్పవద్దు|చెప్పకండి|చెప్పొద్దు|చెప్పకూడదు|షేర్ చేయవద్దు|షేర్ చేయకండి)",
        lower
    ))

    asks_to_share = bool(re.search(
        r"(?:share|tell|send|forward|provide).{0,35}(?:otp|code)|"
        r"(?:otp|code).{0,35}(?:share|tell|send)|"
        r"(?:ఓటిపి|ఓటీపీ).{0,25}(?:చెప్పండి|పంపండి|షేర్ చేయండి)",
        lower
    ))

    if explicit_do_not_share:
        asks_to_share = False

    return has_otp and explicit_do_not_share and not asks_to_share



def analyze_text(text):
    if not text or not text.strip():
        return {
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "threat_type": "No text",
            "signals": [],
            "urls": [],
            "recommendations": [
                "Provide a message or audio recording to analyze."
            ],
            "genuine_otp_notice": False
        }

    signals = []
    matched_types = []
    score = 0

    genuine_otp_notice = _is_genuine_otp_notice(text)

    for pattern, weight, reason, threat_type in PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):

            if (
                genuine_otp_notice
                and threat_type in {"OTP scam", "Social engineering"}
            ):
                continue

            score += weight
            signals.append(reason)
            matched_types.append(threat_type)

    # Generic combination layer (only when no genuine-OTP notice)
    if not genuine_otp_notice:
        hits = [
            (weight, reason)
            for name, weight, reason, pattern in GENERIC_SIGNALS
            if re.search(pattern, text, flags=re.IGNORECASE)
        ]

        if len(hits) >= 2:
            generic_score = min(sum(w for w, _ in hits), GENERIC_MAX_SCORE)

            if score < generic_score:
                score = generic_score

                for _, reason in hits:
                    signals.append(reason)

                if not matched_types:
                    matched_types.append("Suspicious message")

    urls = [
        inspect_url(url)
        for url in URL_RE.findall(text)
    ]

    for item in urls:
        score += round(item["score"] * 0.35)
        signals.extend(item["reasons"])

    score = min(score, 100)

    level = (
        "HIGH" if score >= 70
        else "MEDIUM" if score >= 35
        else "LOW"
    )

    if genuine_otp_notice and not signals and not urls:
        threat = "Informational OTP notification"
    elif matched_types:
        threat = matched_types[0]
    else:
        threat = (
            "No obvious scam pattern detected"
            if level == "LOW"
            else "Suspicious message"
        )

    recommendations = [
        "Never share OTPs, UPI PINs, CVVs, passwords, or full card details.",
        "Do not click links or scan QR codes from unexpected messages.",
        "Verify requests using the organisation's official app or phone number."
    ]

    if level == "HIGH":
        recommendations.insert(
            0,
            "Stop the interaction. Do not reply, pay, click links, or share codes."
        )
    elif level == "MEDIUM":
        recommendations.insert(
            0,
            "Pause and independently verify the sender before taking action."
        )

    if genuine_otp_notice:
        recommendations = [
            "Never share this OTP with anyone.",
            "If you did not initiate the transaction, contact your bank through its official channel.",
            "Monitor your account for unauthorised activity."
        ]

    return {
        "risk_score": score,
        "risk_level": level,
        "threat_type": threat,
        "signals": list(dict.fromkeys(signals)),
        "urls": urls,
        "recommendations": recommendations,
        "genuine_otp_notice": genuine_otp_notice
    }

    
def combine_verdicts(rule_analysis, ai_analysis):
    result = dict(rule_analysis)

    # Genuine OTP notification protection
    if (
        rule_analysis.get("genuine_otp_notice")
        and not rule_analysis.get("signals")
        and not rule_analysis.get("urls")
    ):
        result["risk_score"] = 0
        result["risk_level"] = "LOW"
        result["threat_type"] = "Informational OTP notification"
        result["verdict_source"] = "genuine_otp_guard"

        result["recommendations"] = [
            "Never share this OTP with anyone.",
            "If you did not initiate the transaction, contact your bank through its official channel.",
            "Monitor your account for unauthorised activity."
        ]

        return result

    if (
        not isinstance(ai_analysis, dict)
        or ai_analysis.get("error")
        or not ai_analysis.get("enabled")
    ):
        result["verdict_source"] = "rules_only"
        return result

    ai_type = str(ai_analysis.get("threat_type", "")).strip()

    try:
        ai_confidence = max(
            0,
            min(100, int(ai_analysis.get("confidence", 0) or 0))
        )
    except (ValueError, TypeError):
        ai_confidence = 0

    ai_says_scam = bool(
        ai_type
        and not re.search(
            r"unknown|no obvious|none|not a scam|safe|genuine|legitimate",
            ai_type,
            re.IGNORECASE
        )
    )

    rule_score = int(rule_analysis.get("risk_score", 0))
    fused_score = rule_score

    # Fusion rule: Gemini can RAISE the score, but never decides alone.
    # - If the rules already found something (score >= 35) and Gemini agrees
    #   strongly, the message becomes HIGH.
    # - If the rules found nothing, Gemini alone can reach MEDIUM at most
    #   (an AI mistake or prompt-injected text cannot create a HIGH alert).
    rules_found_something = rule_score >= 35

    if ai_says_scam and ai_confidence >= 85:
        fused_score = max(fused_score, 70 if rules_found_something else 55)
    elif ai_says_scam and ai_confidence >= 70:
        fused_score = max(fused_score, 55 if rules_found_something else 45)
    elif ai_says_scam and ai_confidence >= 60:
        fused_score = max(fused_score, 35)

    fused_score = min(fused_score, 100)

    result["risk_score"] = fused_score
    result["risk_level"] = (
        "HIGH" if fused_score >= 70
        else "MEDIUM" if fused_score >= 35
        else "LOW"
    )

    if ai_says_scam and ai_confidence >= 70 and rule_score < 35:
        result["threat_type"] = ai_type
        result["signals"] = list(dict.fromkeys(
            result.get("signals", [])
            + ["Gemini identified a likely scam pattern"]
        ))

    result["verdict_source"] = "rules_and_gemini"
    result["ai_confidence_support"] = ai_confidence

    if result["risk_level"] == "HIGH":
        first = "Stop the interaction. Do not reply, pay, click links, or share codes."
        result["recommendations"] = (
            [first] + [
                item for item in result.get("recommendations", [])
                if item != first
            ]
        )

    elif result["risk_level"] == "MEDIUM":
        first = "Pause and independently verify the sender before taking action."
        result["recommendations"] = (
            [first] + [
                item for item in result.get("recommendations", [])
                if item != first
            ]
        )

    return result
