# Live AI Interview System

A standalone micro-application for live behavioral intelligence and identity forensics during remote interviews. This system runs independently and securely captures webcam-based behavioral metrics, computes a confidence score, detects potential cheating flags, and stores structured session data as JSON.

## 🎯 Core Features

- **Live Webcam Capture**: Real-time video processing using device cameras.
- **Behavioral Tracking**: Uses MediaPipe Face Mesh to track gaze stability, head movements, and focus consistency.
- **Cheating Detection**: Monitors browser tab switching, window focus loss, missing faces, and multiple people in the frame.
- **Aggregate Confidence Scoring**: Computes an ongoing "Confidence Score" (0-100) based on positive behavioral signals and penalized by cheating anomalies.
- **Session Data Storage**: Automatically saves session outcomes and anomaly logs as structured JSON for future forensic analysis.

## 🏗️ Project Architecture

```text
web cam/
│
├── app.py                  # Main Flask application and API routing
├── interview_engine.py     # Core logic combining behavior & cheating metrics
├── behavioral_metrics.py   # MediaPipe face mesh and tracking algorithms
├── cheating_detector.py    # Event log tracking and penalty calculation
├── session_storage.py      # JSON file I/O operations
│
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── templates/
│   ├── interview.html          # Live interview webcam UI
│   ├── session_complete.html   # Final summary report UI
│
├── static/
│   ├── css/
│   │   ├── interview.css       # Styling & animations
│   ├── js/
│   │   ├── webcam.js           # Video stream and frame capturing
│   │   ├── cheating.js         # Frontend event listeners (tab switch, etc.)
│   │   ├── confidence_meter.js # UI updates for metrics and logs
│
└── sessions/               # (Auto-generated) Saved JSON session records
```

## 🚀 Getting Started

### Prerequisites

You need Python 3 installed. It's recommended to use a virtual environment.

### Installation

1. Navigate to the project folder:
   ```bash
   cd "web cam"
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to a test candidate session:
   [http://localhost:5000/interview/test123](http://localhost:5000/interview/test123)

   *(Replace `test123` with any unique identifier or candidate hash)*

3. Grant webcam permissions when prompted by the browser.

4. Click **Complete Interview Session** when finished to generate the forensic report and save the JSON data.

## 🔒 Privacy & Processing Notes

- **Local Execution:** All rendering, tracking, and metric generation happens locally.
- **No Video Recording:** Frames are processed in memory and immediately discarded. Only structured metric data and text logs are saved into the final JSON. 
- **Deterministic:** The metrics rely on geometric calculation (via MediaPipe) rather than opaque AI "black boxes."

## 🔮 Future Integration

This module is designed strictly as a standalone system. A future roadmap involves integrating via APIs where the main parent Resume System sends a `candidate_hash`, and this module returns the structured `interview_summary`, combining static resume forensics with dynamic behavioral intelligence.
