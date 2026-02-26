// ─── webcam.js ────────────────────────────────────────────────────────────────
// Webcam starts immediately to show live feed, but backend frame processing
// only begins after the interview has started (window.interviewStarted = true).

document.addEventListener('DOMContentLoaded', async () => {
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('capture-canvas');
    const candidateHash = document.getElementById('candidate-hash').innerText.trim();

    let stream = null;
    let captureInterval = null;

    // Start webcam feed immediately (so user can see themselves)
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        video.srcObject = stream;
    } catch (err) {
        console.error('Webcam error:', err);
        alert('Please enable webcam access to proceed with the interview.');
        return;
    }

    // Begin sending frames to backend ONLY after interview starts
    video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        captureInterval = setInterval(() => {
            // Gate: do not send frames until Start is clicked
            if (!window.interviewStarted) return;

            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataURL = canvas.toDataURL('image/jpeg', 0.6);

            fetch('/process_frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidate_hash: candidateHash, image: dataURL })
            })
                .then(r => r.json())
                .then(data => {
                    if (data && !data.error && typeof window.updateMetrics === 'function') {
                        window.updateMetrics(data);
                    }
                })
                .catch(console.error);

        }, 750); // ~1.3 frames per second — stable, not hammering
    };

    // Stop webcam stream when page unloads
    window.addEventListener('beforeunload', () => {
        if (captureInterval) clearInterval(captureInterval);
        if (stream) stream.getTracks().forEach(t => t.stop());
    });
});
