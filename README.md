# 🕵️ The Honest Recruiter: Forensic Resume Auditor

**The Honest Recruiter** is an industrial-grade resume verification and intelligence platform. Unlike standard parsers that simply "read" a resume, this system **cross-references** claims against real-world digital footprints using a multi-layered verification pipeline.

Built for high-trust hiring, it identifies buzzword stuffing, timeline gaps, identity mismatches, and career-stage anomalies by fusing document data with live platform signals.

---

## 🚀 Core Intelligence Pipeline

1.  **Ingestion & Extraction**: Standardized extraction using PyMuPDF and OCR-fallback for image-based PDFs.
2.  **Multi-AI Consensus Engine**: Simultaneous audit via **Groq (Llama 3.3 70B)** and **Google Gemini 1.5 Flash**. The system identifies disagreements between models to calculate an "Epistemic Confidence" score.
3.  **Digital Footprint Verification**:
    *   **GitHub**: Verifies technical engagement, account maturity, and language distribution.
    *   **Email Integrity**: Uses **Hunter.io** and **IPQS** to detect disposable emails and professional reputation.
    *   **StackOverflow**: Checks for domain-specific community engagement.
4.  **Forensic Engines**:
    *   **Career Stage Engine**: Calibrates expectations based on whether the candidate is a Fresher or Executive.
    *   **Proportionality Engine**: Flags "high-intensity claims" (e.g., "AI Expert") that lack supporting project evidence.
    *   **Anomaly Engine**: Detects date overlaps, rapid title escalation, and AI-generated language patterns.
5.  **Live Interaction Engine (Webcam Forensics)**:
    *   **Real-time Behavioral Tracking**: Monitors gaze, head stability, and eye focus using computer vision to track suspicious behavior.
    *   **Continuous Fraud Detection**: Flags cheating events like tab switching, window losing focus, multiple faces, or no face detected.
    *   **Semantic Speech Audio Evaluation**: Synthesizes speech response coherence and matching directly into the final reliability score.

---

## 🛠️ Technology Stack

*   **Backend**: Python / Flask
*   **Primary AI**: Groq (Llama-3.3-70b-versatile) & Google Gemini 1.5 Flash
*   **Verification APIs**: Hunter.io, IPQS, GitHub, StackExchange
*   **Web3 (Foundational)**: SHA-256 Report Integrity hashing for tamper-proof auditing.

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd resume
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory (refer to `.env.example`):

```bash
# Core AI Keys
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# External Verification Keys
GITHUB_TOKEN=your_github_token
HUNTER_API_KEY=your_hunter_key
IPQS_API_KEY=your_ipqs_key
```

### 4. Run the Application
```bash
python app.py
```
The server will start at `http://localhost:5000`.

---

## 📊 API Summary

*   `POST /scan`: Standardized orchestrator. Upload a PDF to trigger the full forensic audit.
*   `GET /scan/demo`: **Hackathon Demo Mode**. Returns a complete pre-verified forensic response (no API keys required).
*   `GET /report/<hash>`: Forensic audit report view for the parsed candidate.
*   `GET /interview/<hash>`: Immersive live AI interview interface capturing webcam behavior and spoken answers.
*   `POST /save_interview_results`: Syncs deep-integrity behavioral logs into the main resume database for a hybrid final score calculation.

---

## 🛡️ Project Philosophy
> "Trust, but verify."

In the age of AI-generated resumes, standard recruitment is broken. **The Honest Recruiter** restores trust by treating every resume as a forensic subject, ensuring that the candidate's digital maturity matches their professional claims.
