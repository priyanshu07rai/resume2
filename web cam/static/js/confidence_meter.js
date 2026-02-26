function updateMetrics(data) {
    if (!data) return;

    // Update Scores
    document.getElementById('confidence-score').innerText = data.confidence_score;

    // Confidence Color shift
    const confScore = document.getElementById('confidence-score');
    if (data.confidence_score > 75) confScore.style.color = 'var(--success-color)';
    else if (data.confidence_score > 50) confScore.style.color = 'var(--warning-color)';
    else confScore.style.color = 'var(--danger-color)';

    // Meeting Termination Logic with Warnings
    const anomalyPoints = data.anomaly_points || 0;

    if (anomalyPoints > 8 && !window.firstWarningShown) {
        window.firstWarningShown = true;
        alert("⚠️ WARNING: Unusual activity detected. Please stay focused on the interview.");
    }

    if (anomalyPoints >= 18 && !window.sessionTerminated) {
        window.sessionTerminated = true;

        // Disable UI
        document.getElementById('qa-module').style.pointerEvents = 'none';
        document.getElementById('qa-module').style.opacity = '0.5';

        alert("🚨 INTEGRITY CONCERN DETECTED: Meeting threshold limits exceeded. Terminating Session.");

        // Force end session
        const endBtn = document.getElementById('end-session-btn');
        if (endBtn) endBtn.click();
    }

    // Dynamically rebuild cheating logs perfectly synchronized with backend state & cooldowns
    if (data.cheating_events) {
        const list = document.getElementById('cheating-log-list');
        list.innerHTML = '';
        if (data.cheating_events.length === 0) {
            list.innerHTML = '<li class="empty-state">No anomalies detected.</li>';
        } else {
            // Reverse so newest is on top
            const reversedEvents = [...data.cheating_events].reverse();
            reversedEvents.forEach(evt => {
                const li = document.createElement('li');
                li.innerText = `[${evt.time}] ALERT: ${evt.type}`;
                if (evt.type === "TAB_SWITCH" || evt.type === "MULTIPLE_FACES" || evt.type === "NO_FACE") {
                    li.className = "high";
                } else {
                    li.className = "medium";
                }
                list.appendChild(li);
            });
        }
    }
}
