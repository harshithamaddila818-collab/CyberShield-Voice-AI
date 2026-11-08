/* =========================================================

   CYBERSHIELD VOICE AI - SIX FEATURE TOOLKIT

   Load this file AFTER script.js

========================================================= */



(() => {

    "use strict";



    const API = (function () {
    // Local development (Live Server on :5500 or opening the file directly) talks to the
    // backend on :8000. When the page is served BY the backend (/app/ locally or on a
    // hosted demo) the API is simply on the same origin.
    const local = ["127.0.0.1", "localhost", ""].includes(location.hostname);
    return local && location.port !== "8000" ? "http://127.0.0.1:8000" : location.origin;
})();

    const $ = (id) => document.getElementById(id);



    let latest = null;



    // =====================================================

    // 1. TOOLKIT DESIGN

    // =====================================================



    const style = document.createElement("style");



    style.textContent = `

        .cs-extra {

            margin: 22px 0;

            padding: 18px;

            border: 1px solid #334155;

            border-radius: 14px;

            background: #0d1b2b;

            color: #e5edf7;

        }



        .cs-extra h2 {

            margin-top: 0;

        }



        .cs-extra h3 {

            margin: 8px 0;

        }



        .cs-grid {

            display: grid;

            grid-template-columns: repeat(

                auto-fit,

                minmax(230px, 1fr)

            );

            gap: 12px;

        }



        .cs-card {

            padding: 14px;

            border: 1px solid #334155;

            border-radius: 10px;

            overflow-wrap: anywhere;

        }



        .cs-extra button,

        .cs-extra select {

            margin: 5px 0;

            padding: 9px 12px;

            border-radius: 8px;

            border: 1px solid #64748b;

            background: #172b43;

            color: white;

            cursor: pointer;

        }



        .cs-extra button:hover {

            background: #24466b;

        }



        .cs-extra input {

            box-sizing: border-box;

            padding: 10px;

            width: 100%;

            background: #102238;

            color: white;

            border: 1px solid #64748b;

            border-radius: 8px;

        }



        .cs-extra li {

            margin: 8px 0;

            line-height: 1.5;

        }



        .cs-muted {

            color: #aabbd0;

            font-size: .9rem;

        }



        .cs-result {

            margin-top: 12px;

            padding: 10px;

            border-radius: 8px;

            background: #172b43;

            white-space: pre-wrap;

            overflow-wrap: anywhere;

        }



        .cs-section-title {

            color: #4dd8e8;

            font-weight: bold;

            margin-top: 14px;

        }

    `;



    document.head.appendChild(style);



    // =====================================================

    // CREATE TOOLKIT

    // =====================================================



    function createPanel() {



        if ($("csFeatures")) {

            return $("csFeatures");

        }



        const root = document.createElement("section");



        root.id = "csFeatures";

        root.className = "cs-extra";



        root.innerHTML = `

            <h2>CyberShield Safety Toolkit</h2>



            <p class="cs-muted">

                Extra checks and recovery tools.

                URL checks are offline structural checks,

                not live website reputation scans.

            </p>



            <div class="cs-grid">



                <!-- FEATURE 1 -->



                <div class="cs-card">

                    <h3>1. Explainable Detection</h3>



                    <p id="csExplain">

                        Scan a message to see why it was flagged.

                    </p>



                    <ul id="csPhrases"></ul>

                </div>



                <!-- FEATURE 2 -->



                <div class="cs-card">

                    <h3>2. PDF Security Report</h3>



                    <p class="cs-muted">

                        Download your latest scan report.

                    </p>



                    <button id="csPdf">

                        Download PDF Report

                    </button>

                </div>



                <!-- FEATURE 3 -->



                <div class="cs-card">

                    <h3>3. Scan History</h3>



                    <button id="csRefreshHistory">

                        Refresh History

                    </button>



                    <ul id="csHistory"></ul>

                </div>



                <!-- FEATURE 4 -->



                <div class="cs-card">

                    <h3>4. Personalized Voice Warning</h3>



                    <select id="csVoiceLang">

                        <option value="en-IN">English</option>

                        <option value="te-IN">తెలుగు</option>

                    </select>



                    <button id="csSpeak">

                        Speak Scan Recommendation

                    </button>

                </div>



                <!-- FEATURE 5 -->



                <div class="cs-card">

                    <h3>5. URL Scanner</h3>



                    <input

                        id="csUrl"

                        type="text"

                        placeholder="Paste a suspicious URL"

                    >



                    <button id="csScanUrl">

                        Check URL

                    </button>



                    <div id="csUrlResult" class="cs-result">

                        URL scan results will appear here.

                    </div>

                </div>



                <!-- FEATURE 6 -->



                <div class="cs-card">

                    <h3>6. Emergency Guidance</h3>



                    <select id="csEmergency">

                        <option value="clicked">

                            I clicked a suspicious link

                        </option>



                        <option value="otp shared">

                            I shared an OTP / PIN / password

                        </option>



                        <option value="money transfer">

                            I transferred money

                        </option>

                    </select>



                    <button id="csGetEmergency">

                        Show Recovery Steps

                    </button>



                    <ol id="csEmergencySteps"></ol>

                </div>



            </div>

        `;



        const results = $("results");



        if (results && results.parentNode) {

            results.parentNode.insertBefore(

                root,

                results.nextSibling

            );

        } else {

            document.body.appendChild(root);

        }



        return root;

    }



    const root = createPanel();



    // =====================================================

    // COMMON API REQUEST

    // =====================================================



    async function request(path, options = {}) {



        const response = await fetch(API + path, options);



        if (!response.ok) {



            let data = {};



            try {

                data = await response.json();

            } catch {

                // Ignore non-JSON errors

            }



            throw new Error(

                data.detail ||

                data.message ||

                `Request failed (${response.status})`

            );

        }



        return response;

    }



    // =====================================================

    // 2. EXPLAINABLE THREAT DETECTION

    // =====================================================



    function addTextItem(list, text) {



        const li = document.createElement("li");



        li.textContent = String(text);



        list.appendChild(li);

    }



    function explain(data) {



        const analysis = data.analysis || {};

        const ai = data.ai_analysis || {};



        const score = Math.max(

            0,

            Math.min(

                100,

                Number(analysis.risk_score ?? 0)

            )

        );



        const risk = String(

            analysis.risk_level || "LOW"

        ).toUpperCase();



        const transcript =

            data.transcript ||

            data.text ||

            "";



        // Show risk score immediately



        $("csExplain").textContent =

            `RISK LEVEL: ${risk} | RISK SCORE: ${score}/100`;



        const list = $("csPhrases");



        list.replaceChildren();



        // Threat indicators



        const heading1 = document.createElement("li");



        heading1.textContent = "THREAT INDICATORS";



        heading1.className = "cs-section-title";



        list.appendChild(heading1);



        const signals = Array.isArray(analysis.signals)

            ? analysis.signals

            : [];



        if (signals.length > 0) {



            signals.forEach(signal => {



                addTextItem(

                    list,

                    typeof signal === "string"

                        ? signal

                        : JSON.stringify(signal)

                );



            });



        } else {



            addTextItem(

                list,

                "No major threat indicators detected."

            );

        }



        // Highlight suspicious phrases



        const heading2 = document.createElement("li");



        heading2.textContent = "SUSPICIOUS PHRASES";



        heading2.className = "cs-section-title";



        list.appendChild(heading2);



        const patterns = [

            /\botp\b/gi,

            /\b(?:share|send|tell|verify)\b/gi,

            /\b(?:blocked|locked|suspended)\b/gi,

            /\b(?:immediately|urgent|now)\b/gi,

            /https?:\/\/\S+/gi,

            /మీ ఓటీపీ/gi,

            /వెంటనే/gi,

            /బ్లాక్/gi

        ];



        const found = new Set();



        // LOW-risk (genuine) messages are never highlighted as suspicious
        (risk === "LOW" ? [] : patterns).forEach(pattern => {



            const matches = transcript.match(pattern) || [];



            matches.forEach(match => found.add(match));



        });



        if (found.size > 0) {



            [...found].slice(0, 12).forEach(phrase => {



                addTextItem(

                    list,

                    `Detected phrase: "${phrase}"`

                );



            });



        } else {



            addTextItem(

                list,

                risk === "LOW"
                    ? "No suspicious phrases found."
                    : "No specific suspicious phrase highlighted."

            );

        }



        // Safety precautions



        const heading3 = document.createElement("li");



        heading3.textContent = "SAFETY PRECAUTIONS";



        heading3.className = "cs-section-title";



        list.appendChild(heading3);



        const recommendations = Array.isArray(

            analysis.recommendations

        )

            ? analysis.recommendations

            : [];



        if (recommendations.length > 0) {



            recommendations.forEach(item => {



                addTextItem(

                    list,

                    typeof item === "string"

                        ? item

                        : JSON.stringify(item)

                );



            });



        } else {



            addTextItem(

                list,

                "Verify suspicious messages using official channels."

            );

        }



        // Gemini recommendation



        const heading4 = document.createElement("li");



        heading4.textContent = "GEMINI AI RECOMMENDATION";



        heading4.className = "cs-section-title";



        list.appendChild(heading4);



        addTextItem(

            list,

            ai.recommended_action ||

            "Gemini recommendation is unavailable."

        );



        // Gemini explanation



        if (ai.explanation) {



            const heading5 = document.createElement("li");



            heading5.textContent = "AI EXPLANATION";



            heading5.className = "cs-section-title";



            list.appendChild(heading5);



            addTextItem(list, ai.explanation);

        }

    }



    // =====================================================

    // 3. SCAN HISTORY

    // =====================================================



    async function saveHistory(data) {



        const body = {

            transcript: data.transcript || data.text || "",

            analysis: data.analysis || {},

            ai_analysis: data.ai_analysis || {}

        };



        if (!body.transcript) return;



        try {



            await request("/api/history", {

                method: "POST",



                headers: {

                    "Content-Type": "application/json"

                },



                body: JSON.stringify(body)

            });



            await refreshHistory();



        } catch (error) {



            console.warn(

                "History save failed:",

                error.message

            );

        }

    }



    async function refreshHistory() {



        const list = $("csHistory");



        list.replaceChildren();



        try {



            const response = await request(

                "/api/history?limit=100"

            );



            const data = await response.json();



            const items = Array.isArray(data.items)

                ? data.items

                : [];



            if (items.length === 0) {



                list.textContent = "No saved scans yet.";



                return;

            }



            items.forEach(item => {



                const li = document.createElement("li");



                const openButton =

                    document.createElement("button");



                openButton.textContent =

                    `#${item.id} · ${item.risk_level} ` +

                    `${item.risk_score}/100 · ` +

                    `${new Date(item.created_at).toLocaleString()}`;



                openButton.onclick = async () => {



                    try {



                        const response = await request(

                            "/api/history/" + item.id

                        );



                        const full = await response.json();



                        latest = full.result;



                        if (latest) {
                             // Show the saved scan in the main report area.
    // restored:true means it is NOT saved to history again.
    if (typeof displayResults === "function") {
        displayResults(latest, { restored: true });
    }


                            explain(latest);
                            $("results")?.scrollIntoView({ behavior: "smooth" });

                        }



                    } catch (error) {



                        alert(error.message);

                    }

                };



                const deleteButton =

                    document.createElement("button");



                deleteButton.textContent = "Delete";



                deleteButton.onclick = async () => {



                    if (!confirm("Delete this scan history item?")) {

                        return;

                    }



                    try {



                        await request(

                            "/api/history/" + item.id,

                            { method: "DELETE" }

                        );



                        await refreshHistory();



                    } catch (error) {



                        alert(error.message);

                    }

                };



                li.append(

                    openButton,

                    deleteButton

                );



                list.appendChild(li);

            });



        } catch (error) {



            list.textContent =

                "Unable to load history: " + error.message;

        }

    }



    // =====================================================

    // Listen for the completed report; do not replace displayResults().
    // This keeps the main scanner independent from the optional toolkit.
    document.addEventListener("cybershield:scan-complete", (event) => {
        const data = event.detail;
        if (!data || typeof data !== "object") return;

        latest = data;
        explain(data);
        void saveHistory(data);
    });

    // =====================================================
        // 4. PDF SECURITY REPORT

    // =====================================================



    $("csPdf").addEventListener("click", async () => {



        if (!latest) {



            alert("Please scan a message before downloading a report.");



            return;

        }



        try {



            const response = await request(

                "/api/report-pdf",

                {

                    method: "POST",



                    headers: {

                        "Content-Type": "application/json"

                    },



                    body: JSON.stringify({

                        transcript: latest.transcript || "",

                        analysis: latest.analysis || {},

                        ai_analysis: latest.ai_analysis || {}

                    })

                }

            );



            const blob = await response.blob();



            const url = URL.createObjectURL(blob);



            const link = document.createElement("a");



            link.href = url;



            link.download =

                "cybershield-security-report.pdf";



            document.body.appendChild(link);



            link.click();



            link.remove();



            setTimeout(() => {

                URL.revokeObjectURL(url);

            }, 1000);



        } catch (error) {



            alert(

                "PDF generation failed: " + error.message

            );

        }

    });



    // =====================================================

    // 5. REFRESH HISTORY

    // =====================================================



    $("csRefreshHistory").addEventListener(

        "click",

        refreshHistory

    );



    // =====================================================

    // 6. URL SCANNER

    // =====================================================



    $("csScanUrl").addEventListener("click", async () => {



        const url = $("csUrl").value.trim();



        const output = $("csUrlResult");



        if (!url) {



            output.textContent = "Please enter a URL first.";



            return;

        }



        output.textContent = "Checking URL...";



        try {



            const response = await request(

                "/api/scan-url",

                {

                    method: "POST",



                    headers: {

                        "Content-Type": "application/json"

                    },



                    body: JSON.stringify({ url })

                }

            );



            const data = await response.json();



            const signals = Array.isArray(data.signals)

                ? data.signals.join("\n")

                : "No obvious structural warning.";



            output.textContent =

                `Risk Level: ${data.risk_level}\n` +

                `Risk Score: ${data.risk_score}/100\n` +

                `Indicators: ${signals}\n` +

                `${data.note || ""}`;



        } catch (error) {



            output.textContent =

                "URL scan failed: " + error.message;

        }

    });



    // =====================================================

    // 7. EMERGENCY GUIDANCE

    // =====================================================



    $("csGetEmergency").addEventListener(

        "click",

        async () => {



            const output = $("csEmergencySteps");



            output.replaceChildren();



            try {



                const response = await request(

                    "/api/emergency-guidance",

                    {

                        method: "POST",



                        headers: {

                            "Content-Type": "application/json"

                        },



                        body: JSON.stringify({

                            situation: $("csEmergency").value

                        })

                    }

                );



                const data = await response.json();



                if (!Array.isArray(data.steps)) {



                    throw new Error(

                        "No emergency steps received."

                    );

                }



                data.steps.forEach(step => {



                    addTextItem(output, step);



                });



            } catch (error) {



                addTextItem(

                    output,

                    "Unable to load guidance: " + error.message

                );

            }

        }

    );



    // =====================================================

    // 8. PERSONALIZED TELUGU / ENGLISH VOICE WARNING

    // =====================================================



    $("csSpeak").addEventListener("click", async () => {



        if (!latest) {



            alert("Please scan a message first.");



            return;

        }



        const language = $("csVoiceLang").value;



        // Same personalized text as the main voice button (script.js).
        const text = typeof window.getVoiceWarningText === "function"
            ? window.getVoiceWarningText(latest, language)
            : "Warning! This message may be suspicious. Never share your OTP, PIN or password. Verify through official channels.";



        const button = $("csSpeak");



        button.disabled = true;



        button.textContent = "Generating voice...";



        try {



            const response = await request(

                "/api/speak",

                {

                    method: "POST",



                    headers: {

                        "Content-Type": "application/json"

                    },



                    body: JSON.stringify({

                        text,

                        language

                    })

                }

            );



            const blob = await response.blob();



            const audioUrl = URL.createObjectURL(blob);



            const audio = new Audio(audioUrl);



            audio.onended = () => {

                URL.revokeObjectURL(audioUrl);

            };



            await audio.play();



        } catch (error) {



            alert(

                "Voice generation failed: " + error.message

            );



        } finally {



            button.disabled = false;



            button.textContent =

                "Speak Scan Recommendation";

        }

    });



    // =====================================================

    // INITIALIZATION

    // =====================================================



    refreshHistory();



    // If the page was reloaded after a scan, script.js re-displays that scan.
    // Rebuild the Explainable Detection panel from the same saved scan.
    // This does NOT save history again.
    try {

        const savedScan = JSON.parse(
            sessionStorage.getItem("cybershield:last-scan") || "null"
        );

        if (savedScan && typeof savedScan === "object") {

            latest = savedScan;

            explain(savedScan);
        }

    } catch (error) {

        console.warn(
            "Could not restore last scan:",
            error.message
        );
    }



    console.log(

        "🛡️ CyberShield Six Feature Toolkit initialized successfully."

    );



})();