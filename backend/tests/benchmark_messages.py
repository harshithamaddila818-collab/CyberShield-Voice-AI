BENCHMARK_MESSAGES = [
    # Genuine messages — LOW
    {
        "id": 1,
        "language": "English",
        "category": "Genuine OTP",
        "text": "Your HDFC Bank OTP is 482916. Do not share this OTP with anyone.",
        "expected": "LOW"
    },
    {
        "id": 2,
        "language": "English",
        "category": "Genuine Banking",
        "text": "Your account statement is ready. Please log in through the official bank app.",
        "expected": "LOW"
    },
    {
        "id": 3,
        "language": "English",
        "category": "Genuine Delivery",
        "text": "Your parcel has been shipped and will be delivered tomorrow.",
        "expected": "LOW"
    },
    {
        "id": 4,
        "language": "English",
        "category": "Genuine Electricity",
        "text": "Your electricity bill payment was received successfully. Thank you.",
        "expected": "LOW"
    },
    {
        "id": 5,
        "language": "English",
        "category": "Genuine Transaction",
        "text": "Your bank account was credited with the amount you requested.",
        "expected": "LOW"
    },
    {
        "id": 6,
        "language": "Telugu",
        "category": "Genuine OTP",
        "text": "మీ OTP 482916. ఈ OTP ని ఎవరికీ చెప్పవద్దు.",
        "expected": "LOW"
    },
    {
        "id": 7,
        "language": "Telugu",
        "category": "Genuine Payment",
        "text": "మీ బిల్లు చెల్లింపు విజయవంతంగా పూర్తయింది.",
        "expected": "LOW"
    },
    {
        "id": 8,
        "language": "Telugu",
        "category": "Genuine Delivery",
        "text": "మీ పార్సెల్ రేపు డెలివరీ అవుతుంది.",
        "expected": "LOW"
    },
    {
        "id": 9,
        "language": "Telugu",
        "category": "Genuine Banking",
        "text": "మీ బ్యాంక్ ఖాతా స్టేట్‌మెంట్ సిద్ధంగా ఉంది.",
        "expected": "LOW"
    },
    {
        "id": 10,
        "language": "Telugu",
        "category": "Genuine Transaction",
        "text": "మీ ఖాతాలో డబ్బులు జమ అయ్యాయి.",
        "expected": "LOW"
    },

    # Scam messages — HIGH
    {
        "id": 11,
        "language": "English",
        "category": "OTP Scam",
        "text": "Your bank account will be blocked. Send your OTP immediately to verify your account.",
        "expected": "HIGH"
    },
    {
        "id": 12,
        "language": "English",
        "category": "Digital Arrest",
        "text": "You are under digital arrest. CBI officers will arrest you unless you transfer money immediately.",
        "expected": "HIGH"
    },
    {
        "id": 13,
        "language": "English",
        "category": "UPI Scam",
        "text": "Approve this UPI collect request and enter your PIN to receive your refund.",
        "expected": "HIGH"
    },
    {
        "id": 14,
        "language": "English",
        "category": "Fake Job",
        "text": "Earn money through Telegram tasks. Deposit money to unlock your next task and commission.",
        "expected": "HIGH"
    },
    {
        "id": 15,
        "language": "English",
        "category": "Electricity Scam",
        "text": "Your electricity connection will be disconnected tonight. Pay immediately using this link.",
        "expected": "HIGH"
    },
    {
        "id": 16,
        "language": "English",
        "category": "KYC Scam",
        "text": "Your bank KYC has expired. Update immediately or your account will be blocked.",
        "expected": "HIGH"
    },
    {
        "id": 17,
        "language": "English",
        "category": "Loan Scam",
        "text": "Pay an advance processing fee to receive your instant loan approval.",
        "expected": "HIGH"
    },
    {
        "id": 18,
        "language": "English",
        "category": "Courier Scam",
        "text": "Your parcel has been seized by customs. Pay the release fee using this link.",
        "expected": "HIGH"
    },
    {
        "id": 19,
        "language": "English",
        "category": "Remote Access Scam",
        "text": "Install AnyDesk and share your screen to receive your bank refund.",
        "expected": "HIGH"
    },
    {
        "id": 20,
        "language": "English",
        "category": "Prize Scam",
        "text": "You won a lottery prize. Pay the processing fee immediately to claim your reward.",
        "expected": "HIGH"
    },
    {
        "id": 21,
        "language": "Telugu",
        "category": "OTP Scam",
        "text": "మీ ఖాతా బ్లాక్ అవుతుంది. మీ OTP వెంటనే మాకు పంపండి.",
        "expected": "HIGH"
    },
    {
        "id": 22,
        "language": "Telugu",
        "category": "Digital Arrest",
        "text": "మీరు డిజిటల్ అరెస్ట్‌లో ఉన్నారు. డబ్బులు పంపకపోతే అరెస్ట్ చేస్తాము.",
        "expected": "HIGH"
    },
    {
        "id": 23,
        "language": "Telugu",
        "category": "UPI Scam",
        "text": "డబ్బులు పొందడానికి UPI కలెక్ట్ రిక్వెస్ట్ అంగీకరించి పిన్ ఎంటర్ చేయండి.",
        "expected": "HIGH"
    },
    {
        "id": 24,
        "language": "Telugu",
        "category": "Fake Job",
        "text": "టెలిగ్రామ్ టాస్క్ పూర్తి చేయడానికి ముందుగా డిపాజిట్ చేయండి.",
        "expected": "HIGH"
    },
    {
        "id": 25,
        "language": "Telugu",
        "category": "Electricity Scam",
        "text": "మీ విద్యుత్ కనెక్షన్ వెంటనే కట్ అవుతుంది. వెంటనే చెల్లించండి.",
        "expected": "HIGH"
    },
    {
        "id": 26,
        "language": "Telugu",
        "category": "KYC Scam",
        "text": "మీ బ్యాంక్ KYC బ్లాక్ అయింది. వెంటనే అప్‌డేట్ చేయండి.",
        "expected": "HIGH"
    },
    {
        "id": 27,
        "language": "Telugu",
        "category": "Loan Scam",
        "text": "లోన్ పొందడానికి ముందుగా ప్రాసెసింగ్ ఫీజు చెల్లించండి.",
        "expected": "HIGH"
    },
    {
        "id": 28,
        "language": "Telugu",
        "category": "Courier Scam",
        "text": "మీ కొరియర్‌ను ఆపారు. డెలివరీ కోసం ఫీజు చెల్లించండి.",
        "expected": "HIGH"
    },
    {
        "id": 29,
        "language": "Telugu",
        "category": "Remote Access Scam",
        "text": "రిఫండ్ పొందడానికి యాప్ ఇన్‌స్టాల్ చేసి స్క్రీన్ షేర్ చేయండి.",
        "expected": "HIGH"
    },
    {
        "id": 30,
        "language": "Telugu",
        "category": "Prize Scam",
        "text": "మీరు లాటరీ గెలిచారు. బహుమతి పొందడానికి ఫీజు చెల్లించండి.",
        "expected": "HIGH"
    },

    # Medium — suspicious, requires verification
    {
        "id": 31,
        "language": "English",
        "category": "Suspicious Link",
        "text": "Please click this link to verify your account: http://example.xyz",
        "expected": "MEDIUM"
    },
    {
        "id": 32,
        "language": "English",
        "category": "Urgent Request",
        "text": "Please verify your account immediately to avoid service interruption.",
        "expected": "MEDIUM"
    },
    {
        "id": 33,
        "language": "English",
        "category": "Unknown Sender",
        "text": "Hello, contact our support team regarding your account.",
        "expected": "MEDIUM"
    },
    {
        "id": 34,
        "language": "English",
        "category": "Unexpected Payment",
        "text": "A payment request is waiting for your approval. Please check it.",
        "expected": "MEDIUM"
    },
    {
        "id": 35,
        "language": "English",
        "category": "Unexpected Reward",
        "text": "You have been selected for a special reward. Contact us for details.",
        "expected": "MEDIUM"
    },
    {
        "id": 36,
        "language": "Telugu",
        "category": "Suspicious Link",
        "text": "మీ ఖాతాను ధృవీకరించడానికి ఈ లింక్‌ను తెరవండి.",
        "expected": "MEDIUM"
    },
    {
        "id": 37,
        "language": "Telugu",
        "category": "Urgent Request",
        "text": "మీ ఖాతా వివరాలను వెంటనే తనిఖీ చేయండి.",
        "expected": "MEDIUM"
    },
    {
        "id": 38,
        "language": "Telugu",
        "category": "Unknown Sender",
        "text": "మీ ఖాతా గురించి మా సపోర్ట్ టీమ్‌ను సంప్రదించండి.",
        "expected": "MEDIUM"
    },
    {
        "id": 39,
        "language": "Telugu",
        "category": "Unexpected Payment",
        "text": "మీకు ఒక పేమెంట్ రిక్వెస్ట్ వచ్చింది. దయచేసి తనిఖీ చేయండి.",
        "expected": "MEDIUM"
    },
    {
        "id": 40,
        "language": "Telugu",
        "category": "Unexpected Reward",
        "text": "మీకు ప్రత్యేక బహుమతి వచ్చింది. వివరాల కోసం మమ్మల్ని సంప్రదించండి.",
        "expected": "MEDIUM"
    },
]