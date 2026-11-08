
"""Optional CyberShield features: history, PDF reports, URL checks and emergency guidance."""

import json
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from html import escape as html_escape
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Additional safety features"])


# The history database is kept outside the project folder.
_LEGACY_DB = Path(__file__).resolve().parent / "data" / "scan_history.db"

DB_PATH = Path(
    os.environ.get("CYBERSHIELD_DB")
    or Path.home() / ".cybershield" / "scan_history.db"
)

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if not DB_PATH.exists() and _LEGACY_DB.exists():
    shutil.copy2(_LEGACY_DB, DB_PATH)


class SaveScan(BaseModel):
    transcript: str = Field(max_length=5000)
    analysis: dict = {}
    ai_analysis: dict = {}


class UrlRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)


class EmergencyRequest(BaseModel):
    situation: str


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            transcript TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            result_json TEXT NOT NULL
        )
    """)

    return conn


# ---------------- SCAN HISTORY ----------------

@router.post("/history")
def save_history(payload: SaveScan):
    a = payload.analysis or {}

    score = max(0, min(100, int(a.get("risk_score", 0) or 0)))
    level = str(a.get("risk_level", "LOW")).upper()

    now = datetime.now(timezone.utc).isoformat()
    data = payload.model_dump()

    with db() as conn:
        cur = conn.execute(
            """
            INSERT INTO scans(
                created_at, transcript, risk_score,
                risk_level, result_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                now,
                payload.transcript[:5000],
                score,
                level,
                json.dumps(data, ensure_ascii=False)
            )
        )

        scan_id = cur.lastrowid

    return {
        "id": scan_id,
        "created_at": now,
        "risk_score": score,
        "risk_level": level
    }


@router.get("/history")
def get_history(limit: int = 30):
    limit = max(1, min(100, limit))

    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, transcript,
                   risk_score, risk_level
            FROM scans
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return {"items": [dict(row) for row in rows]}


@router.get("/history/{scan_id}")
def get_scan(scan_id: int):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM scans WHERE id = ?",
            (scan_id,)
        ).fetchone()

    if not row:
        raise HTTPException(404, "Scan not found")

    item = dict(row)
    item["result"] = json.loads(item.pop("result_json"))

    return item


@router.delete("/history/{scan_id}")
def delete_scan(scan_id: int):
    with db() as conn:
        cur = conn.execute(
            "DELETE FROM scans WHERE id = ?",
            (scan_id,)
        )

    if cur.rowcount == 0:
        raise HTTPException(404, "Scan not found")

    return {"deleted": True, "id": scan_id}


@router.delete("/history")
def clear_history():
    with db() as conn:
        conn.execute("DELETE FROM scans")

    return {"deleted": True}


# ---------------- URL SCANNER ----------------

@router.post("/scan-url")
def scan_url(payload: UrlRequest):
    raw = payload.url.strip()

    candidate = raw if "://" in raw else "https://" + raw
    parsed = urlparse(candidate)

    host = (parsed.hostname or "").lower()

    if not host:
        raise HTTPException(
            400,
            "Please enter a valid URL or domain."
        )

    reasons = []

    if parsed.scheme != "https":
        reasons.append("The URL does not use HTTPS.")

    if host.startswith("xn--") or ".xn--" in host:
        reasons.append(
            "Internationalized/punycode domain; verify spelling carefully."
        )

    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        reasons.append(
            "The link uses a raw IP address instead of a normal domain."
        )

    if any(
        x in host
        for x in (
            "bit.ly",
            "tinyurl.com",
            "t.co",
            "goo.gl",
            "cutt.ly",
            "is.gd"
        )
    ):
        reasons.append(
            "URL shortener hides the final destination."
        )

    if host.count("-") >= 3:
        reasons.append(
            "The domain contains several hyphens; check for impersonation."
        )

    if len(host) > 50:
        reasons.append(
            "The domain name is unusually long."
        )

    if any(
        host.endswith(t)
        for t in (
            ".zip",
            ".mov",
            ".click",
            ".top",
            ".work",
            ".gq"
        )
    ):
        reasons.append(
            "The top-level domain is commonly abused; "
            "this alone does not prove fraud."
        )

    score = min(95, len(reasons) * 20)

    return {
        "url": raw,
        "host": host,
        "risk_score": score,
        "risk_level": (
            "HIGH" if score >= 60
            else "MEDIUM" if score >= 20
            else "LOW"
        ),
        "signals": reasons,
        "checked_reputation": False,
        "note": (
            "This is an offline URL-structure check, "
            "not a live reputation or malware scan. "
            "Do not open suspicious links."
        )
    }


# ---------------- EMERGENCY GUIDANCE ----------------

@router.post("/emergency-guidance")
def emergency(payload: EmergencyRequest):
    s = payload.situation.lower()

    if "otp" in s or "password" in s or "pin" in s or "shared" in s:
        steps = [
            "Contact your bank or service provider immediately "
            "using its official app/website/number.",

            "Change the affected password/PIN and revoke active "
            "sessions where possible.",

            "Block or freeze the affected card/account if you "
            "suspect access.",

            "Do not share any further OTPs or verification codes."
        ]

        label = "You shared an OTP, PIN or password"

    elif (
        "money" in s
        or "transfer" in s
        or "paid" in s
        or "payment" in s
    ):
        steps = [
            "Call India's cybercrime helpline 1930 immediately "
            "to report financial cyber fraud.",

            "Submit a complaint at https://cybercrime.gov.in "
            "and keep the acknowledgement number.",

            "Contact your bank/payment app immediately and "
            "request a transaction hold or dispute.",

            "Save transaction IDs, messages, phone numbers "
            "and screenshots; do not delete evidence."
        ]

        label = "You transferred money"

    else:
        steps = [
            "Close the page and do not enter passwords, OTPs, "
            "card details or UPI PINs.",

            "If you downloaded an app/file, do not open it; "
            "uninstall suspicious apps and run a trusted security scan.",

            "If you entered credentials, change them from the "
            "official app/site and sign out other sessions.",

            "Contact your bank immediately if financial details "
            "were entered or a payment was initiated."
        ]

        label = "You clicked a suspicious link"

    return {
        "situation": label,
        "steps": steps,
        "urgent_note": (
            "If money was lost in India, report it immediately "
            "through 1930 and the official cybercrime portal."
        )
    }


# ---------------- PDF SECURITY REPORT ----------------
_FONT_DIR = Path(__file__).resolve().parent / "fonts"


def _register_pdf_font():
    """Return a font name for PDFs: bundled Noto Telugu, then Windows Nirmala, then Helvetica."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        ("NotoSansTelugu", _FONT_DIR / "NotoSansTelugu-Regular.ttf", None),
        ("Nirmala", Path("C:/Windows/Fonts/Nirmala.ttc"), 0),
    ]
    for name, path, sub_index in candidates:
        if name in pdfmetrics.getRegisteredFontNames():
            return name
        if not path.exists():
            continue
        try:
            if sub_index is None:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            else:
                pdfmetrics.registerFont(TTFont(name, str(path), subfontIndex=sub_index))
            return name
        except Exception as e:
            print(f"PDF font {name} could not be loaded: {e}")
    print("No Telugu PDF font found; using Helvetica (Telugu text will show as boxes).")
    return "Helvetica"
@router.post("/report-pdf")
def report_pdf(payload: SaveScan):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        a = payload.analysis or {}
        ai = payload.ai_analysis or {}

        buf = BytesIO()

        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm
        )

                # Register Telugu-capable font (bundled Noto, then Nirmala, then Helvetica).
        _PDF_FONT = _register_pdf_font()

        styles = getSampleStyleSheet()

        # Apply the chosen font to all report styles.
        for style_name in styles.byName:
            styles[style_name].fontName = _PDF_FONT

        story = [
            Paragraph(
                "CyberShield Voice AI — Security Scan Report",
                styles["Title"]
            ),
            Spacer(1, 8)
        ]

        esc = lambda x: html_escape(str(x))

        story += [
            Paragraph(
                "Generated: " +
                datetime.now().astimezone().strftime(
                    "%Y-%m-%d %H:%M %Z"
                ),
                styles["Normal"]
            ),

            Paragraph(
                f"Rule-based risk: "
                f"{esc(a.get('risk_level', 'LOW'))} — "
                f"{esc(a.get('risk_score', 0))}/100",
                styles["Heading2"]
            ),

            Paragraph(
                "Scanned text: " +
                esc(payload.transcript[:5000]),
                styles["BodyText"]
            ),

            Spacer(1, 8),

            Paragraph(
                "Threat indicators",
                styles["Heading2"]
            )
        ]

        signals = a.get("signals") or [
            "No major indicators detected by the rule-based engine."
        ]

        story += [
            Paragraph(
                "• " + esc(signal),
                styles["BodyText"]
            )
            for signal in signals
        ]

        story += [
            Spacer(1, 8),

            Paragraph(
                "AI explanation",
                styles["Heading2"]
            ),

            Paragraph(
                esc(
                    ai.get("explanation")
                    or ai.get("note")
                    or "Not available"
                ),
                styles["BodyText"]
            ),

            Paragraph(
                "Recommended action",
                styles["Heading2"]
            ),

            Paragraph(
                esc(
                    ai.get("recommended_action")
                    or "Verify through official channels."
                ),
                styles["BodyText"]
            ),

            Spacer(1, 10),

            Paragraph(
                "Disclaimer: Assistive assessment only. "
                "It is not a guarantee that content is safe or fraudulent. "
                "URL reputation was not checked unless explicitly stated.",
                styles["Italic"]
            )
        ]

        doc.build(story)

        return Response(
            buf.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                'attachment; filename="cybershield-security-report.pdf"'
            }
        )

    except ImportError:
        raise HTTPException(
            500,
            "PDF dependency missing. Install reportlab "
            "in your project virtual environment."
        )
