// ─── cheating.js ─────────────────────────────────────────────────────────────
// All cheating events are gated: nothing is logged until interview has started.
// WINDOW_UNFOCUS only fires if the window was blurred for more than 3 seconds.

document.addEventListener('DOMContentLoaded', () => {
    const candidateHash = document.getElementById('candidate-hash').innerText.trim();

    function logCheatingEvent(eventType) {
        // Gate: do not send events until interview is running
        if (!window.interviewStarted) return;

        fetch('/cheating_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_hash: candidateHash, event_type: eventType })
        }).catch(console.error);
    }

    // ── Tab switch (page hidden) ──────────────────────────────────────────────
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            logCheatingEvent('TAB_SWITCH');
        }
    });

    // ── Window unfocus — only fire if blurred for more than 3 seconds ─────────
    let blurTimer = null;

    window.addEventListener('blur', () => {
        blurTimer = setTimeout(() => {
            logCheatingEvent('WINDOW_UNFOCUS');
        }, 3000); // 3‑second grace before logging
    });

    window.addEventListener('focus', () => {
        // Cancelled: user came back within 3s — not suspicious
        if (blurTimer) {
            clearTimeout(blurTimer);
            blurTimer = null;
        }
    });
});
