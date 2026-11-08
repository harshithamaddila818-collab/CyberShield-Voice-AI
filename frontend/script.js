const API_BASE = (function () {
    // Local development (Live Server on :5500 or opening the file directly) talks to the
    // backend on :8000. When the page is served BY the backend (/app/ locally or on a
    // hosted demo) the API is simply on the same origin.
    const local = ["127.0.0.1", "localhost", ""].includes(location.hostname);
    return local && location.port !== "8000" ? "http://127.0.0.1:8000" : location.origin;
})();

// Key used to keep the latest scan across an accidental page reload
// (for example VS Code Live Server auto-reloading). Shared with features.js.
const LAST_SCAN_KEY = "cybershield:last-scan";

// ==================== ELEMENTS ====================

const $ = (id) => document.getElementById(id);

const recordButton = $("recordButton");
const recordStatus = $("recordStatus");
const recordTimer = $("recordTimer");
const audioFile = $("audioFile");
const languageSelect = $("language");

// ==================== GLOBAL VARIABLES ====================

let mediaRecorder = null;
let audioChunks = [];
let recordedAudioFile = null;
let recordingInterval = null;
let recordingSeconds = 0;

let lastLanguage = "en-IN";
let lastTranscript = "";
let warningObjectUrl = null;
let scanCompleted = false;
let lastScanData = null;

// ==================== UI HELPERS ====================

function showLoading(show) {
    $("loading").classList.toggle("hidden", !show);
}

function showError(message) {
    $("error").textContent = message;
    $("error").classList.remove("hidden");
}

function clearError() {
    $("error").textContent = "";
    $("error").classList.add("hidden");
}

function setBusy(busy) {
    $("analyzeAudio").disabled = busy;
    $("analyzeText").disabled = busy;
    $("speakWarning").disabled = busy;
}

function setText(id, value) {
    const element = $(id);

    if (element) {
        element.textContent = value;
    }
}

// When a NEW scan starts, hide the previous result so the screen never shows
// an old score next to the "Analyzing..." spinner. displayResults() shows the
// section again as soon as the new result arrives.
function hideResultsForNewScan() {
    $("results").classList.add("hidden");
}

function showResultsSection() {
    const resultsSection = $("results");

    resultsSection.classList.remove("hidden");
    resultsSection.removeAttribute("hidden");
}

async function getErrorMessage(response) {
    try {
        const data = await response.json();

        if (Array.isArray(data.detail)) {
            return data.detail
                .map(item => item.msg || "Validation error")
                .join(", ");
        }

        return data.detail || data.message ||
            `Request failed (${response.status})`;

    } catch {
        return `Request failed (${response.status})`;
    }
}

function getWarningLanguage(text = "") {
    if (/[ఀ-౿]/.test(text)) {
        return "te-IN";
    }

    if (languageSelect.value === "te-IN") {
        return "te-IN";
    }

    return "en-IN";
}

// ==================== PERSONALIZED VOICE WARNING TEXT ====================
// Builds the sentence spoken by Gnani Timbre for the CURRENT scan.
// Order: Gemini's voice script (if available) -> rule-based template that
// uses the real risk level and score -> generic safety sentence.

const VOICE_FALLBACK_STATIC = {
    "en-IN": "Warning! This message may be suspicious. Never share your OTP, banking PIN, or password. Verify through the official channel.",
    "te-IN": "జాగ్రత్త! ఈ సందేశం అనుమానాస్పదంగా ఉంది. మీ OTP లేదా బ్యాంకింగ్ PIN ఎవరికీ చెప్పకండి. అధికారిక మార్గంలో ధృవీకరించండి."
};

function buildVoiceWarning(data, language) {
    const isTelugu = language === "te-IN";

    if (!data || typeof data !== "object") {
        return VOICE_FALLBACK_STATIC[isTelugu ? "te-IN" : "en-IN"];
    }

    const ai = data.ai_analysis || {};
    const geminiText = isTelugu ? ai.voice_warning_te : ai.voice_warning_en;

    if (typeof geminiText === "string" && geminiText.trim()) {
        return geminiText.trim();
    }

    const analysis = data.analysis || {};
    const level = String(analysis.risk_level || "LOW").toUpperCase();
    const score = Math.max(0, Math.min(100, Number(analysis.risk_score) || 0));

    if (isTelugu) {
        if (level === "HIGH") {
            return "హెచ్చరిక! ఈ సందేశం చాలా ప్రమాదకరమైనది. మీ OTP, పిన్ లేదా పాస్‌వర్డ్ ఎవరికీ చెప్పకండి. లింక్‌ను క్లిక్ చేయకండి. అధికారిక యాప్ లేదా నంబర్ ద్వారా మాత్రమే ధృవీకరించండి.";
        }

        if (level === "MEDIUM") {
            return "జాగ్రత్త! ఈ సందేశం అనుమానాస్పదంగా ఉంది. పంపినవారిని అధికారిక మార్గంలో ధృవీకరించే వరకు స్పందించకండి, లింక్‌లను తెరవకండి.";
        }

        return "ఈ సందేశంలో స్పష్టమైన ప్రమాద సంకేతాలు కనిపించలేదు. అయినా OTP లేదా పిన్ ఎవరికీ చెప్పకండి, లింక్‌లను జాగ్రత్తగా తెరవండి.";
    }

    if (level === "HIGH") {
        return `Warning! This message is highly dangerous, with a risk score of ${score} out of 100. Do not share your OTP, PIN or password, and do not click any link. Verify only through the official app or phone number.`;
    }

    if (level === "MEDIUM") {
        return `Be careful! This message looks suspicious, with a risk score of ${score} out of 100. Do not reply or open any link until you verify the sender through an official channel.`;
    }

    return "No clear scam signs were found in this message. Still, never share your OTP or PIN, and open links carefully.";
}

window.getVoiceWarningText = buildVoiceWarning;

// ==================== LAST-SCAN PERSISTENCE ====================
// Browser storage can be unavailable (private mode, blocked cookies),
// so every access is wrapped and the app works without it.

function saveLastScan(data) {
    try {
        sessionStorage.setItem(LAST_SCAN_KEY, JSON.stringify(data));
    } catch {
        // Ignore: persistence is a convenience only.
    }
}

function loadLastScan() {
    try {
        const raw = sessionStorage.getItem(LAST_SCAN_KEY);
        const data = raw ? JSON.parse(raw) : null;

        return data && typeof data === "object" ? data : null;

    } catch {
        return null;
    }
}

// ==================== SAFE LIST RENDERING ====================

function addListItems(elementId, items, emptyMessage) {
    const list = $(elementId);

    if (!list) return;

    list.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        const li = document.createElement("li");
        li.textContent = emptyMessage;
        list.appendChild(li);
        return;
    }

    items.forEach((item) => {
        const li = document.createElement("li");

        if (typeof item === "string") {
            li.textContent = item;
        } else if (item && typeof item === "object") {
            li.textContent =
                item.message ||
                item.reason ||
                item.url ||
                JSON.stringify(item);
        } else {
            li.textContent = String(item);
        }

        list.appendChild(li);
    });
}

// Run one rendering step; a failure in one section must never blank
// the others or hide the results.
function renderStep(label, step) {
    try {
        step();
    } catch (error) {
        console.error(`CyberShield: failed to render ${label}:`, error);
    }
}

// ==================== DISPLAY SECURITY RESULTS ====================
// options.restored = true re-renders a previously saved scan after a page
// reload. It does NOT notify features.js, so history is never saved twice.

function displayResults(data, options = {}) {

    const restored = Boolean(options.restored);

    if (!data || typeof data !== "object") {
        showError("Invalid response received from the server.");
        return;
    }

    scanCompleted = true;

    showResultsSection();

    // Support normal and nested response structures.
    const analysis =
        data.analysis ||
        data.result?.analysis ||
        data.result ||
        data;

    // ==================== RISK SCORE ====================

    const rawScore =
        analysis.risk_score ??
        analysis.score ??
        data.risk_score ??
        0;

    const parsedScore = Number(rawScore);

    const score = Number.isFinite(parsedScore)
        ? Math.max(0, Math.min(100, parsedScore))
        : 0;

    let risk = String(
        analysis.risk_level ||
        analysis.risk ||
        data.risk_level ||
        "LOW"
    ).toUpperCase();

    // Determine risk level if backend did not provide it
    // (same thresholds as backend/services/threat_engine.py).
    if (!analysis.risk_level && !data.risk_level) {
        if (score >= 70) {
            risk = "HIGH";
        } else if (score >= 35) {
            risk = "MEDIUM";
        } else {
            risk = "LOW";
        }
    }

    renderStep("risk score", () => {
        setText("score", score);

        const badge = $("riskBadge");

        badge.textContent = risk;
        badge.className = "risk-badge";

        if (risk === "HIGH") {
            badge.classList.add("high");
        } else if (risk === "MEDIUM") {
            badge.classList.add("medium");
        }

        $("meterFill").style.width = `${score}%`;
    });

    // ==================== TRANSCRIPT ====================

    const transcript =
        data.transcript ||
        data.text ||
        data.transcription?.text ||
        "";

    renderStep("transcript", () => {
        setText("transcript", transcript || "No transcript available.");
    });

    lastTranscript = transcript;
    lastScanData = data;

    // ==================== THREAT INDICATORS ====================

    renderStep("threat indicators", () => {
        addListItems(
            "signals",
            analysis.signals,
            "No major threat indicators detected."
        );
    });

    // ==================== URL SECURITY ====================

    renderStep("URL check", () => {
        const urlItems = (analysis.urls || []).map(item => {

            if (typeof item === "string") {
                return item;
            }

            const reasons = Array.isArray(item.reasons)
                ? item.reasons.join("; ")
                : "";

            return `${item.url || "Unknown URL"} — ${item.risk || "Unknown risk"} (Score: ${item.score ?? "N/A"})${reasons ? " — " + reasons : ""}`;
        });

        addListItems(
            "urls",
            urlItems,
            "No URLs detected in this message."
        );
    });

    // ==================== RECOMMENDATIONS ====================

    renderStep("recommendations", () => {
        addListItems(
            "recommendations",
            analysis.recommendations,
            "Always verify suspicious messages through official channels."
        );
    });

    // ==================== GEMINI AI INSIGHTS ====================

    renderStep("Gemini insights", () => {
        const ai = data.ai_analysis || {};

        if (ai.enabled && !ai.error) {
            setText("aiStatus", "GEMINI ACTIVE");
        } else if (ai.error) {
            setText("aiStatus", "AI UNAVAILABLE");
        } else {
            setText("aiStatus", "RULE-BASED ONLY");
        }

        setText("aiThreatType", ai.threat_type || "Not available");

        setText("aiLanguage", ai.language || "Not identified");

        const confidence = Number(ai.confidence);

        if (
            ai.enabled &&
            !ai.error &&
            Number.isFinite(confidence) &&
            confidence > 0 &&
            confidence <= 100
        ) {
            setText("aiConfidence", `${confidence}%`);
        } else {
            setText("aiConfidence", "Not reported");
        }

        setText(
            "aiExplanation",
            ai.explanation ||
            ai.note ||
            ai.error ||
            "Gemini explanation is unavailable."
        );

        setText(
            "aiRecommendation",
            ai.recommended_action ||
            "Follow the safety recommendations above."
        );
    });

    // ==================== DISCLAIMER ====================

    setText(
        "disclaimer",
        data.disclaimer ||
        "This is an automated safety assessment. It cannot guarantee that a message or URL is safe."
    );

    // Keep last detected language.
    lastLanguage = getWarningLanguage(transcript);

    // Remember this scan so an accidental page reload cannot lose it.
    saveLastScan(data);

    // Notify features.js (Explainable Detection + Scan History) ONCE per
    // real scan. Skipped when re-rendering a saved scan after a reload.
    if (!restored) {
        document.dispatchEvent(
            new CustomEvent("cybershield:scan-complete", {
                detail: data
            })
        );
    }

    console.log("CyberShield scan displayed:", {
        score,
        risk,
        restored
    });
}

// Make display function accessible to other frontend scripts.
window.displayResults = displayResults;

// ==================== TEXT MESSAGE ANALYSIS ====================

$("analyzeText").addEventListener("click", async () => {

    // Ignore clicks while a scan is already running.
    if ($("analyzeText").disabled) return;

    clearError();

    const text = $("messageText").value.trim();

    if (!text) {
        showError("Please paste a message before scanning.");
        return;
    }

    hideResultsForNewScan();
    showLoading(true);
    setBusy(true);

    try {

        const response = await fetch(
            `${API_BASE}/api/analyze-text`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text })
            }
        );

        if (!response.ok) {
            throw new Error(await getErrorMessage(response));
        }

        const data = await response.json();

        lastLanguage = getWarningLanguage(text);

        displayResults(data);
        $("warningLanguage").value = lastLanguage;
        startPipeline(data, false);

    } catch (error) {

        showError(
            error.message ||
            "Unable to analyze this message. Check your backend."
        );

    } finally {

        showLoading(false);
        setBusy(false);
    }
});

// ==================== AUDIO FILE SELECTION ====================

audioFile.addEventListener("change", () => {

    recordedAudioFile = null;

    if (audioFile.files.length > 0) {

        $("fileName").textContent =
            audioFile.files[0].name;

    } else {

        $("fileName").textContent =
            "No file selected";
    }
});

// ==================== AUDIO ANALYSIS ====================

async function analyzeAudioFile(file) {

    // Ignore clicks while a scan is already running.
    if ($("analyzeAudio").disabled) return;

    clearError();

    if (!file) {
        showError("Please record or select an audio file first.");
        return;
    }

    if (file.size > 30 * 1024 * 1024) {
        showError("File is too large. Choose an audio file under 30 MB.");
        return;
    }

    const formData = new FormData();

    formData.append("audio", file, file.name);

    const selectedLanguage = languageSelect.value;

    formData.append(
        "language_code",
        selectedLanguage
    );

    hideResultsForNewScan();
    showLoading(true);
    setBusy(true);
    let speakAfterScan = false;


    try {

        const response = await fetch(
            `${API_BASE}/api/analyze-audio`,
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {
            throw new Error(await getErrorMessage(response));
        }

        const data = await response.json();

        const transcript =
            data.transcript ||
            data.text ||
            data.transcription?.text ||
            "";

        const detectedLanguage =
            data.detected_language_code ||
            data.transcription?.detected_language_code ||
            "";

        if (detectedLanguage.startsWith("te")) {
            lastLanguage = "te-IN";
        } else if (detectedLanguage.startsWith("en")) {
            lastLanguage = "en-IN";
        } else {
            lastLanguage = getWarningLanguage(transcript);
        }

        displayResults(data);

        // Voice-first: a voice scan is answered with a spoken warning in
        // the same language the speaker used (Gnani Timbre).
        $("warningLanguage").value = lastLanguage;
        startPipeline(data, true);
        speakAfterScan = true;

    } catch (error) {

        showError(
            error.message ||
            "Audio analysis failed. Check the audio format and backend connection."
        );

    } finally {

        showLoading(false);
        setBusy(false);

        // Voice-first: buttons are enabled again, now speak the warning.
        if (speakAfterScan) {
            $("speakWarning").click();
        }
    }
}

$("analyzeAudio").addEventListener("click", () => {

    const file =
        recordedAudioFile ||
        audioFile.files[0];

    analyzeAudioFile(file);
});

// ==================== MICROPHONE RECORDING ====================

function formatTime(seconds) {

    const minutes = Math.floor(seconds / 60);

    const remaining = seconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`;
}

function stopRecording() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {
        mediaRecorder.stop();
    }
}

recordButton.addEventListener("click", async () => {

    clearError();

    if (
        mediaRecorder &&
        mediaRecorder.state === "recording"
    ) {
        stopRecording();
        return;
    }

    if (
        !navigator.mediaDevices?.getUserMedia ||
        !window.MediaRecorder
    ) {
        showError(
            "Your browser does not support microphone recording. Try Chrome."
        );
        return;
    }

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        audioChunks = [];
        recordingSeconds = 0;

        let options = {};

        if (
            MediaRecorder.isTypeSupported(
                "audio/webm;codecs=opus"
            )
        ) {
            options.mimeType = "audio/webm;codecs=opus";
        } else if (
            MediaRecorder.isTypeSupported("audio/mp4")
        ) {
            options.mimeType = "audio/mp4";
        }

        mediaRecorder = new MediaRecorder(
            stream,
            options
        );

        mediaRecorder.ondataavailable = (event) => {

            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {

            clearInterval(recordingInterval);

            stream.getTracks().forEach(track => {
                track.stop();
            });

            const mimeType =
                mediaRecorder.mimeType || "audio/webm";

            let extension = "webm";

            if (mimeType.includes("mp4")) {
                extension = "mp4";
            } else if (mimeType.includes("ogg")) {
                extension = "ogg";
            }

            const blob = new Blob(
                audioChunks,
                { type: mimeType }
            );

            recordedAudioFile = new File(
                [blob],
                `cybershield-recording.${extension}`,
                { type: mimeType }
            );

            $("fileName").textContent =
                `Recorded audio (${recordedAudioFile.name})`;

            recordStatus.textContent =
                "Recording completed. Ready to analyze.";

            recordButton.innerHTML =
                "<span>●</span> Record Again";

            recordTimer.textContent =
                formatTime(recordingSeconds);
        };

        mediaRecorder.start();

        recordStatus.textContent =
            "Recording in progress...";

        recordButton.innerHTML =
            "<span>■</span> Stop Recording";

        recordingInterval = setInterval(() => {

            recordingSeconds++;

            recordTimer.textContent =
                formatTime(recordingSeconds);

            if (recordingSeconds >= 30) {
                stopRecording();
            }

        }, 1000);

    } catch (error) {

        showError(
            "Microphone access failed. Allow microphone permission in Chrome."
        );

        recordStatus.textContent =
            "Microphone permission required.";
    }
});

// ==================== VOICE PIPELINE STRIP ====================
// Shows which step produced what: Gnani Prisma (speech to text) ->
// rules + Gemini (verdict) -> Gnani Timbre (spoken warning).
let pipelineState = null;

function formatMs(ms) {
    if (ms === undefined || ms === null) return "";
    return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${ms} ms`;
}

function renderPipeline() {
    const card = $("pipelineCard");
    const list = $("pipelineSteps");
    if (!card || !list || !pipelineState) return;

    const p = pipelineState.pipeline || {};
    const steps = [];

    if (pipelineState.fromAudio) {
        steps.push({
            gnani: true,
            title: "🎙 Gnani Prisma STT",
            detail: [
                pipelineState.detectedLanguage || "language auto-detected",
                formatMs(p.stt_ms)
            ].filter(Boolean).join(" · ")
        });
    } else {
        steps.push({
            skipped: true,
            title: "🎙 Gnani Prisma STT",
            detail: "not used (text typed or pasted)"
        });
    }

    steps.push({
        title: "🛡 Rule engine",
        detail: `Telugu + English patterns · ${formatMs(p.rules_ms) || "instant"}`
    });

    const geminiLabels = {
        ok: "analysed",
        off: "switched off",
        quota: "daily quota used up (rules only)",
        error: "unavailable (rules only)"
    };
    steps.push({
        title: "🤖 Gemini AI",
        detail: [geminiLabels[p.gemini_status] || "", formatMs(p.gemini_ms)]
            .filter(Boolean).join(" · ")
    });

    steps.push({
        gnani: true,
        title: "🔊 Gnani Timbre TTS",
        detail: pipelineState.ttsMs
            ? `${pipelineState.ttsLanguage} warning · ${formatMs(pipelineState.ttsMs)}`
            : "tap Generate Voice Warning"
    });

    list.textContent = "";

    steps.forEach((step) => {
        const li = document.createElement("li");
        if (step.gnani) li.classList.add("gnani");
        if (step.skipped) li.classList.add("skipped");

        const strong = document.createElement("strong");
        strong.textContent = step.title;

        const span = document.createElement("span");
        span.textContent = step.detail;

        li.append(strong, span);
        list.appendChild(li);
    });

    card.classList.remove("hidden");
}

function startPipeline(data, fromAudio) {
    pipelineState = {
        pipeline: data.pipeline || {},
        fromAudio,
        detectedLanguage:
            data.transcription?.detected_language_code || "",
        ttsMs: 0,
        ttsLanguage: ""
    };
    renderPipeline();
}

// ==================== TEXT TO SPEECH ====================

$("speakWarning").addEventListener("click", async () => {

    clearError();

    const selectedWarningLanguage =
        $("warningLanguage").value;

    // Personalized to the current scan (risk level, Gemini advice).
    const warningText = buildVoiceWarning(
        lastScanData,
        selectedWarningLanguage
    );

    $("speakWarning").disabled = true;

    $("speakWarning").textContent =
        "Generating voice...";
    const ttsStarted = performance.now();

    try {

        const response = await fetch(
            `${API_BASE}/api/speak`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    text: warningText,
                    language: selectedWarningLanguage
                })
            }
        );

        if (!response.ok) {
            throw new Error(await getErrorMessage(response));
        }

        const blob = await response.blob();

        if (warningObjectUrl) {
            URL.revokeObjectURL(warningObjectUrl);
        }

        warningObjectUrl =
            URL.createObjectURL(blob);

        const audio = $("warningAudio");

        audio.src = warningObjectUrl;

        audio.classList.remove("hidden");

        audio.onerror = () => {
            showError(
                "Voice audio could not be played by this browser."
            );
        };

        if (pipelineState) {
            pipelineState.ttsMs = Math.round(performance.now() - ttsStarted);
            pipelineState.ttsLanguage =
                selectedWarningLanguage.startsWith("te") ? "Telugu" : "English";
            renderPipeline();
        }

        try {
            await audio.play();
        } catch (playError) {
            // Some browsers block automatic playback; the player is visible,
            // so the user can just press play.
            if (playError.name !== "NotAllowedError") throw playError;
        }

    } catch (error) {

        showError(
            error.message ||
            "Unable to generate voice warning."
        );

    } finally {

        $("speakWarning").disabled = false;

        $("speakWarning").textContent =
            "Generate Voice Warning";
    }
});

// ==================== INITIALIZATION ====================

$("loading").classList.add("hidden");
$("error").classList.add("hidden");

// If the page was reloaded after a scan, show that scan again instead of
// an empty (hidden) results section. Otherwise start with results hidden.
const savedScan = loadLastScan();

if (savedScan) {
    displayResults(savedScan, { restored: true });
} else {
    $("results").classList.add("hidden");
}

console.log(
    "CyberShield Voice AI frontend initialized successfully."
);
