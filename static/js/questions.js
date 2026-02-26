// ─── questions.js ────────────────────────────────────────────────────────────
// Everything is gated behind the START INTERVIEW button.

document.addEventListener('DOMContentLoaded', () => {

    // ── DOM refs ─────────────────────────────────────────────────────────────
    const startBtn = document.getElementById('start-interview-btn');
    const startScreen = document.getElementById('start-screen');
    const qaModule = document.getElementById('qa-module');
    const endBtn = document.getElementById('end-session-btn');
    const questionText = document.getElementById('current-question-text');
    const qCategory = document.getElementById('q-category');
    const qDifficulty = document.getElementById('q-difficulty');
    const answerBox = document.getElementById('answer-box');
    const submitBtn = document.getElementById('submit-answer-btn');
    const startSpeechB = document.getElementById('start-speech-btn');
    const stopSpeechB = document.getElementById('stop-speech-btn');
    const speechStatus = document.getElementById('speech-status');
    const candidateHash = document.getElementById('candidate-hash').innerText.trim();

    // ── State ─────────────────────────────────────────────────────────────────
    let availableQuestions = [];
    let currentQuestionIndex = 0;
    let recognition = null;
    let finalTranscript = '';
    let speechTimer = null;
    let timerInterval = null;
    let timeLeft = 900; // 15 minutes

    // ── Timer ─────────────────────────────────────────────────────────────────
    function startTimer() {
        timerInterval = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                if (endBtn && !endBtn.disabled) endBtn.click();
            }
        }, 1000);
    }

    // ── Speech init ────────────────────────────────────────────────────────────
    function initSpeech() {
        const SR = window.webkitSpeechRecognition || window.SpeechRecognition;
        if (!SR) {
            answerBox.innerHTML = "<span style='color:#f87171;'>⚠️ Speech not supported. Use Chrome.</span>";
            startSpeechB.disabled = true;
            return;
        }

        recognition = new SR();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onresult = (event) => {
            let interim = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const t = event.results[i][0].transcript;
                if (event.results[i].isFinal) finalTranscript += t + ' ';
                else interim += t;
            }
            answerBox.innerHTML =
                (finalTranscript || '') +
                '<i style="color:#888; font-size:0.95em">' + interim + '</i>';
            submitBtn.disabled = finalTranscript.trim().length === 0;
            clearTimeout(speechTimer);
        };

        recognition.onstart = () => {
            speechStatus.innerText = '🔴 Recording...';
            if (!finalTranscript) {
                answerBox.innerHTML = '<em style="color:#4ade80;">🎙 Speak now — listening...</em>';
            }
        };

        // Auto-restart so Chrome's silence timeout doesn't stop us
        recognition.onend = () => {
            if (window._speechShouldRun) {
                try { recognition.start(); } catch (e) { /* already starting */ }
            } else {
                startSpeechB.disabled = false;
                stopSpeechB.disabled = true;
                speechStatus.innerText = 'Mic off';
            }
        };

        recognition.onerror = (e) => {
            console.error('Speech error:', e.error);
            window._speechShouldRun = false;
            const msgs = {
                'not-allowed': '❌ Mic blocked. Click the 🔒 in the address bar → Allow Microphone → retry.',
                'no-speech': '⚠️ No speech detected. Try again.',
                'network': '❌ Network error.',
                'aborted': '⏹ Stopped.',
                'audio-capture': '❌ No microphone found.'
            };
            answerBox.innerHTML = `<span style="color:#f87171;">${msgs[e.error] || '⚠️ ' + e.error}</span>`;
            speechStatus.innerText = 'Error';
            startSpeechB.disabled = false;
            stopSpeechB.disabled = true;
            clearTimeout(speechTimer);
        };
    }

    // ── Start Speaking button ────────────────────────────────────────────────
    startSpeechB.addEventListener('click', async () => {
        if (!recognition) {
            alert('Please click Start Interview first.');
            return;
        }

        // Explicitly request mic — triggers browser permission dialog
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(t => t.stop()); // we only needed the permission grant
        } catch (err) {
            answerBox.innerHTML = "<span style='color:#f87171;'>❌ Microphone access denied. Click the 🔒 in the browser address bar, allow Microphone, then reload.</span>";
            return;
        }

        finalTranscript = '';
        window._speechShouldRun = true;
        submitBtn.disabled = true;
        startSpeechB.disabled = true;
        stopSpeechB.disabled = false;

        try {
            recognition.start();
        } catch (e) {
            // If already running, stop and restart cleanly
            recognition.stop();
            setTimeout(() => {
                try { recognition.start(); } catch (e2) { console.log(e2); }
            }, 300);
        }

        // Silence hint after 20s
        clearTimeout(speechTimer);
        speechTimer = setTimeout(() => {
            answerBox.innerHTML += '<br><span style="color:#f59e0b; font-size:0.85em;">⏳ No speech for 20s — try speaking closer to the mic.</span>';
        }, 20000);
    });

    // ── Stop Speaking button ─────────────────────────────────────────────────
    stopSpeechB.addEventListener('click', () => {
        window._speechShouldRun = false;
        clearTimeout(speechTimer);
        if (recognition) recognition.stop();
        startSpeechB.disabled = false;
        stopSpeechB.disabled = true;
        speechStatus.innerText = 'Mic off';
    });

    // ── Show a question ───────────────────────────────────────────────────────
    function showQuestion(index) {
        if (index < availableQuestions.length) {
            const q = availableQuestions[index];
            questionText.innerText = q.question || '(No question text)';
            qCategory.innerText = q.category || '—';
            qDifficulty.innerText = q.difficulty || '—';
            finalTranscript = '';
            answerBox.innerHTML = '<em style="color:#666;">Your verbal answer will appear here...</em>';
            submitBtn.innerText = 'Submit Answer →';
            submitBtn.disabled = true;
            startSpeechB.disabled = false;
            stopSpeechB.disabled = true;
        } else {
            qaModule.innerHTML = '<div style="padding:1rem; color:#aaa; font-size:1rem;">✅ All questions answered. Click <strong>Complete Interview Session</strong>.</div>';
        }
    }

    // ── Submit Answer ─────────────────────────────────────────────────────────
    submitBtn.addEventListener('click', () => {
        const answer = finalTranscript.trim();
        if (!answer) { alert('Please speak your answer first.'); return; }

        window._speechShouldRun = false;
        if (recognition) recognition.stop();
        clearTimeout(speechTimer);

        submitBtn.disabled = true;
        submitBtn.innerText = 'Evaluating...';

        const q = availableQuestions[currentQuestionIndex];
        fetch('/submit_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_hash: candidateHash, question: q.question, answer })
        })
            .then(r => r.json())
            .then(() => {
                currentQuestionIndex++;
                showQuestion(currentQuestionIndex);
            })
            .catch(err => {
                console.error(err);
                submitBtn.disabled = false;
                submitBtn.innerText = 'Submit Answer →';
            });
    });

    // ── End Session ───────────────────────────────────────────────────────────
    endBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        window._speechShouldRun = false;
        if (recognition) try { recognition.stop(); } catch (e) { }

        endBtn.innerText = 'Processing...';
        endBtn.disabled = true;

        fetch('/end_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_hash: candidateHash })
        })
            .then(r => r.json())
            .then(() => { window.location.href = `/session_summary/${candidateHash}`; })
            .catch(err => {
                console.error(err);
                alert('Error ending session. Try again.');
                endBtn.disabled = false;
                endBtn.innerText = 'Complete Interview Session';
            });
    });

    // ── START INTERVIEW button (the gate) ─────────────────────────────────────
    startBtn.addEventListener('click', () => {
        // Show UI
        startScreen.style.display = 'none';
        qaModule.style.display = 'flex';
        endBtn.style.display = 'block';

        // Init speech recognizer
        initSpeech();

        // Load questions from backend
        fetch('/load_questions/')
            .then(r => r.json())
            .then(data => {
                if (data && data.length > 0) {
                    availableQuestions = data;
                    showQuestion(0);
                } else {
                    questionText.innerText = '⚠️ No questions found. Check the /questions folder.';
                }
            })
            .catch(() => {
                questionText.innerText = '⚠️ Failed to load questions. Is the server running?';
            });

        // Start backend session
        fetch('/start_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_hash: candidateHash })
        }).catch(console.error);

        // Start timer
        startTimer();

        // Signal webcam.js to start sending frames
        window.interviewStarted = true;
    });

});
