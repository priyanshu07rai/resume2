// ─── interview.js (Strictly Gated, Deep UI, Production-Grade) ───────────────

let interviewStarted = false;
let recognition = null;
let webcamStream = null;
let captureInterval = null;
let availableQuestions = [];
let currentIndex = 0;
let finalTranscript = "";

// Ensure NOTHING runs automatically.
window.onload = function () {
    // Intentionally left empty to ensure strictly gated execution.
};

document.addEventListener("DOMContentLoaded", () => {
    // ── Safe DOM Element Retrieval ───────────────────────────────────────────
    const getEl = id => document.getElementById(id);

    // Identifiers
    const candidateHashEl = getEl("candidate-hash");
    const candidateHash = candidateHashEl ? candidateHashEl.innerText.trim() : "unknown_candidate";

    // Screens
    const startScreen = getEl("startScreen");
    const interviewScreen = getEl("interviewScreen");

    // Buttons
    const startBtn = getEl("startBtn");
    const startSpeechBtn = getEl("startSpeechBtn");
    const stopSpeechBtn = getEl("stopSpeechBtn");
    const submitAnswerBtn = getEl("submitAnswerBtn");
    const endSessionBtn = getEl("endSessionBtn");

    // Display Elements
    const qCategory = getEl("qCategory");
    const qDifficulty = getEl("qDifficulty");
    const questionText = getEl("questionText");
    const speechOutput = getEl("speechOutput");
    const confidenceScore = getEl("confidenceScore");
    const cheatingEvents = getEl("cheatingEvents");
    const cheatingList = getEl("cheatingList");

    // Media
    const video = getEl("webcam-video");
    const canvas = getEl("capture-canvas");

    // ── Helper: Safe InnerHTML/Text Updates ──────────────────────────────────
    const safeSetText = (el, text) => { if (el) el.innerText = text; };
    const safeSetHTML = (el, html) => { if (el) el.innerHTML = html; };

    // ── 1. Initialization Gate ───────────────────────────────────────────────
    if (startBtn) {
        startBtn.addEventListener("click", function () {
            if (interviewStarted) return;
            startBtn.disabled = true; // Prevent rapid double-clicks
            interviewStarted = true;

            // Transition UI to Active State
            if (startScreen) startScreen.style.display = "none";

            if (interviewScreen) {
                interviewScreen.style.display = "grid";
                interviewScreen.classList.add("main-content");
            }

            // Start services strictly downstream of this click
            initializeSpeech();
            loadQuestions();
            startWebcamMonitoring();

            // Register session with backend
            fetch('/start_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidate_hash: candidateHash })
            }).catch(err => {
                console.error("Failed to start session:", err);
            });
        });
    }

    // ── 2. 🎤 Speech Logic ───────────────────────────────────────────────────
    function initializeSpeech() {
        const SR = window.webkitSpeechRecognition || window.SpeechRecognition;
        if (!SR) {
            safeSetHTML(speechOutput, "<span style='color:var(--danger-color)'>Speech recognition requires Google Chrome or Edge. Please switch browsers.</span>");
            if (startSpeechBtn) startSpeechBtn.disabled = true;
            return;
        }

        try {
            recognition = new SR();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onresult = function (event) {
                let interim = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    let t = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += t + " ";
                    } else {
                        interim += t;
                    }
                }

                safeSetHTML(speechOutput, finalTranscript + `<i style="color:var(--text-secondary)">${interim}</i>`);
                if (submitAnswerBtn) submitAnswerBtn.disabled = finalTranscript.trim().length === 0;
            };

            recognition.onerror = function (event) {
                console.error("Speech Recognition Error:", event.error);
                let errorMsg = "Microphone error detected.";
                if (event.error === 'not-allowed') errorMsg = "Microphone access denied. Please allow mic permissions in your browser.";
                if (event.error === 'no-speech') errorMsg = "No speech detected. Please try again.";

                safeSetHTML(speechOutput, `<span style="color:var(--danger-color)">${errorMsg}</span>`);
                if (startSpeechBtn) startSpeechBtn.disabled = false;
                if (stopSpeechBtn) stopSpeechBtn.disabled = true;
            };

            // Handle unexpected stops
            recognition.onend = function () {
                if (startSpeechBtn && startSpeechBtn.disabled && interviewStarted && currentIndex < availableQuestions.length) {
                    try { recognition.start(); } catch (e) { console.warn("Could not auto-restart recognition", e); }
                }
            };
        } catch (e) {
            console.error("Failed to initialize speech recognition:", e);
            safeSetHTML(speechOutput, "<span style='color:var(--danger-color)'>Error initializing microphone.</span>");
        }

        if (startSpeechBtn) {
            startSpeechBtn.onclick = () => {
                try {
                    recognition.start();
                    startSpeechBtn.disabled = true;
                    if (stopSpeechBtn) stopSpeechBtn.disabled = false;
                    finalTranscript = "";
                    safeSetHTML(speechOutput, "<em style='color:var(--accent-color)'>Listening live...</em>");
                    if (submitAnswerBtn) submitAnswerBtn.disabled = true;
                } catch (e) {
                    // Start was called while already started or failed
                    console.warn("Speech recognition start failed:", e);
                }
            };
        }

        if (stopSpeechBtn) {
            stopSpeechBtn.onclick = () => {
                if (recognition) {
                    try { recognition.stop(); } catch (e) { }
                }
                if (startSpeechBtn) startSpeechBtn.disabled = false;
                stopSpeechBtn.disabled = true;
                safeSetHTML(speechOutput, finalTranscript + "<br><em style='color:var(--text-secondary)'>Paused.</em>");
            };
        }
    }

    // ── 3. 📜 Question Engine ────────────────────────────────────────────────
    function loadQuestions() {
        safeSetText(questionText, "Loading questions from database...");

        fetch("/load_questions/")
            .then(res => {
                if (!res.ok) throw new Error("Network response was not ok");
                return res.json();
            })
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    availableQuestions = data;
                    displayQuestion(0);
                } else {
                    safeSetText(questionText, "No questions found in the database. Please contact support.");
                }
            })
            .catch(err => {
                console.error("Failed to load questions:", err);
                safeSetText(questionText, "System error loading questions. Please refresh the page.");
            });
    }

    function displayQuestion(index) {
        if (index < availableQuestions.length) {
            const q = availableQuestions[index] || {};
            safeSetText(questionText, q.question || "Unable to display question text.");
            safeSetText(qCategory, q.category || "General");
            safeSetText(qDifficulty, q.difficulty || "Standard");

            safeSetHTML(speechOutput, "<em style='color:var(--text-secondary)'>Your verbal response will be transcribed here in real-time...</em>");
            finalTranscript = "";

            if (submitAnswerBtn) {
                submitAnswerBtn.disabled = true;
                submitAnswerBtn.innerHTML = "Submit Answer →";
            }
            if (startSpeechBtn) startSpeechBtn.disabled = false;
            if (stopSpeechBtn) stopSpeechBtn.disabled = true;
        } else {
            safeSetText(questionText, "All forensic questions completed. Please force complete the session.");
            if (qCategory) qCategory.style.display = "none";
            if (qDifficulty) qDifficulty.style.display = "none";
            if (startSpeechBtn) startSpeechBtn.disabled = true;
            if (stopSpeechBtn) stopSpeechBtn.disabled = true;
            if (submitAnswerBtn) submitAnswerBtn.disabled = true;
            safeSetHTML(speechOutput, "<em style='color:var(--success-color)'>Evaluation stage fully cleared.</em>");
        }
    }

    if (submitAnswerBtn) {
        submitAnswerBtn.onclick = () => {
            const answer = finalTranscript.trim();
            if (!answer) return;

            if (startSpeechBtn) startSpeechBtn.disabled = false;
            if (stopSpeechBtn) stopSpeechBtn.disabled = true;
            submitAnswerBtn.disabled = true;

            if (recognition) {
                try { recognition.stop(); } catch (e) { }
            }

            submitAnswerBtn.innerHTML = "Processing Analysis... <span class='spinner'>⏳</span>";

            fetch('/submit_answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_hash: candidateHash,
                    question: availableQuestions[currentIndex]?.question || "Unknown",
                    answer: answer
                })
            })
                .then(res => {
                    if (!res.ok) throw new Error("Submission failed");
                    return res.json();
                })
                .then(() => {
                    currentIndex++;
                    displayQuestion(currentIndex);
                })
                .catch(err => {
                    console.error("Error submitting answer:", err);
                    submitAnswerBtn.disabled = false;
                    submitAnswerBtn.innerHTML = "Submission Failed. Try Again.";
                });
        };
    }

    // ── 3.5 📊 UI Live Updates ───────────────────────────────────────────────
    function updateConfidence(data) {
        if (!data) return;

        // Update Score Text
        if (confidenceScore) {
            confidenceScore.innerText = `${data.confidence_score}%`;
            if (data.confidence_score > 75) confidenceScore.style.color = 'var(--success-color)';
            else if (data.confidence_score > 50) confidenceScore.style.color = 'var(--warning-color)';
            else confidenceScore.style.color = 'var(--danger-color)';
        }

        // Update Bar Width
        const confidenceBar = getEl("confidenceBar");
        if (confidenceBar) {
            confidenceBar.style.width = `${data.confidence_score}%`;
            if (data.confidence_score > 75) confidenceBar.style.background = 'var(--success-color)';
            else if (data.confidence_score > 50) confidenceBar.style.background = 'var(--warning-color)';
            else confidenceBar.style.background = 'var(--danger-color)';
        }

        // Meeting Termination Logic with Warnings
        const anomalyPoints = data.anomaly_points || 0;

        if (anomalyPoints > 8 && !window.firstWarningShown) {
            window.firstWarningShown = true;
            alert("⚠️ WARNING: Unusual activity detected. Please stay focused on the interview.");
        }

        if (anomalyPoints >= 18 && !window.sessionTerminated) {
            window.sessionTerminated = true;

            // Disable UI
            if (getEl('interviewScreen')) getEl('interviewScreen').style.pointerEvents = 'none';
            if (getEl('interviewScreen')) getEl('interviewScreen').style.opacity = '0.5';

            alert("🚨 INTEGRITY CONCERN DETECTED: Meeting threshold limits exceeded. Terminating Session.");

            // Force end session
            if (endSessionBtn) endSessionBtn.click();
        }

        // Dynamically rebuild cheating logs perfectly synchronized with backend state
        if (data.cheating_events && cheatingList) {
            if (cheatingEvents) cheatingEvents.style.display = "block"; // show card
            cheatingList.innerHTML = '';
            if (data.cheating_events.length === 0) {
                cheatingList.innerHTML = '<li style="color:var(--text-secondary); font-size:0.9rem;">No anomalies detected.</li>';
            } else {
                // Reverse so newest is on top
                const reversedEvents = [...data.cheating_events].reverse();
                reversedEvents.forEach(evt => {
                    const li = document.createElement('li');
                    li.innerText = `[${evt.time}] ALERT: ${evt.type}`;
                    li.style.padding = "0.5rem 0";
                    li.style.borderBottom = "1px solid var(--border-color)";
                    li.style.fontSize = "0.9rem";
                    if (evt.type === "TAB_SWITCH" || evt.type === "MULTIPLE_FACES" || evt.type === "NO_FACE") {
                        li.style.color = "var(--danger-color)";
                    } else {
                        li.style.color = "var(--warning-color)";
                    }
                    cheatingList.appendChild(li);
                });
            }
        }
    }

    // ── 4. 🎥 Forensic Webcam Monitoring ─────────────────────────────────────
    async function startWebcamMonitoring() {
        if (!video || !canvas) return;

        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }
            });
            video.srcObject = webcamStream;
        } catch (err) {
            console.error("Webcam blocked or unavailable:", err);
            safeSetHTML(speechOutput, "<span style='color:var(--danger-color)'>Camera access denied. Video forensic monitoring is required to proceed. Please allow camera access and refresh.</span>");
            return;
        }

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;

            // Poll strictly after start, checking if video is actually playing
            captureInterval = setInterval(() => {
                if (!interviewStarted || video.paused || video.ended) return;

                try {
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const dataURL = canvas.toDataURL('image/jpeg', 0.6); // 60% quality to optimize payload size

                    fetch('/process_frame', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ candidate_hash: candidateHash, image: dataURL })
                    })
                        .then(res => {
                            if (res.ok) return res.json();
                            return null; // Silent failure on minor frame drops
                        })
                        .then(data => {
                            if (data && !data.error) updateConfidence(data);
                        })
                        .catch(() => {
                            // Suppress network errors from polluting console during polling skips
                        });
                } catch (e) {
                    console.warn("Frame capture error:", e);
                }

            }, 2000); // Stable 2-second heartbeat
        };
    }

    // ── 5. 🧠 Live Updating ──────────────────────────────────────────────────
    function updateConfidence(data) {
        if (confidenceScore && data.confidence_score !== undefined) {
            const score = parseInt(data.confidence_score, 10);
            if (!isNaN(score)) {
                confidenceScore.innerText = `${score}%`;

                const bar = getEl("confidenceBar");

                confidenceScore.style.color = ""; // reset
                let color = "var(--danger-color)";
                if (score > 75) {
                    color = "var(--success-color)";
                } else if (score > 50) {
                    color = "var(--warning-color)";
                }

                confidenceScore.style.color = color;

                if (bar) {
                    bar.style.width = `${score}%`;
                    bar.style.backgroundColor = color;
                }
            }
        }

        // Dynamic Anomaly Logs
        if (data.cheating_events && Array.isArray(data.cheating_events) && data.cheating_events.length > 0) {
            if (cheatingEvents) {
                cheatingEvents.style.display = "flex";
                cheatingEvents.style.flexDirection = "column";
            }

            if (cheatingList) {
                cheatingList.innerHTML = "";
                // Render newest events first
                [...data.cheating_events].reverse().forEach(evt => {
                    if (!evt.type || !evt.time) return;

                    const li = document.createElement("li");
                    li.innerHTML = `<span style="font-family:monospace; color:var(--text-secondary)">[${evt.time}]</span> ${evt.type}`;

                    if (evt.type === "NO_FACE" || evt.type === "MULTIPLE_FACES" || evt.type.includes("SPOOF")) {
                        li.className = "high";
                    } else {
                        li.className = "medium";
                    }

                    cheatingList.appendChild(li);
                });
            }
        } else {
            if (cheatingList) {
                cheatingList.innerHTML = `<li class="empty-state">Secure Environment Confirmed.</li>`;
            }
        }
    }

    // ── 6. 🛑 Session Termination ────────────────────────────────────────────
    if (endSessionBtn) {
        endSessionBtn.onclick = () => {
            endSessionBtn.disabled = true;
            endSessionBtn.innerHTML = "Finalizing Profile... <span class='spinner'>⏳</span>";

            // Cleanup local hardware streams immediately
            if (captureInterval) clearInterval(captureInterval);
            if (webcamStream) {
                webcamStream.getTracks().forEach(t => t.stop());
            }
            if (recognition) {
                try { recognition.stop(); } catch (e) { }
            }

            // Inform backend
            fetch('/end_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidate_hash: candidateHash })
            })
                .then(res => {
                    if (!res.ok) throw new Error("End session failed");
                    return res.json();
                })
                .then((data) => {
                    // Send data back to Resume System
                    return fetch("/save_interview_results", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            candidate_hash: candidateHash,
                            interview_results: data.summary
                        })
                    });
                })
                .then(res => res.json())
                .then(() => {
                    // Redirect on success
                    window.location.href = `/report/${candidateHash}`;
                })
                .catch(err => {
                    console.error("End session error:", err);
                    endSessionBtn.disabled = false;
                    endSessionBtn.innerHTML = "System Error. Click to retry.";
                    // Let user force direct navigation if server hangs:
                    setTimeout(() => {
                        window.location.href = `/report/${candidateHash}`;
                    }, 3000);
                });
        };
    }
});
