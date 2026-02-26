import sqlite3
import json
import os
import logging

log = logging.getLogger("HonestRecruiter.DB")

DB_PATH = os.path.join(os.path.dirname(__file__), "candidates.db")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database with the new single-source-of-truth schema."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    conn = _get_connection()
    c = conn.cursor()
    # New lean schema — forensic_json holds the entire serialized payload
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            domain TEXT,
            hash TEXT UNIQUE,
            final_score REAL,
            forensic_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    conn.close()
    log.info("Initialized candidates database (v3 schema).")

def clear_all():
    import glob
    conn = _get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM candidates')
    conn.commit()
    conn.close()
    for f in glob.glob(os.path.join(REPORTS_DIR, "*.json")):
        try:
            os.remove(f)
        except Exception as e:
            log.warning("Could not remove %s: %s", f, e)
    log.info("Cleared all candidates and reports.")

def is_duplicate(file_hash: str) -> bool:
    """Checks if a resume hash already exists in the database."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM candidates WHERE hash = ?', (file_hash,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def save_candidate(name: str, domain: str, file_hash: str, final_score: float, forensic_payload: dict):
    """
    Saves a processed candidate to the database.
    forensic_payload must be a complete dict — it is serialized to forensic_json.
    Also writes a JSON backup to reports/<hash>.json for resilience.
    """
    serialized = json.dumps(forensic_payload, ensure_ascii=False)

    # File backup (judges love forensic evidence trails)
    try:
        report_path = os.path.join(REPORTS_DIR, f"{file_hash}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(serialized)
        log.info("  Forensic backup written: %s", report_path)
    except Exception as e:
        log.warning("  Could not write file backup: %s", e)

    conn = _get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO candidates (name, domain, hash, final_score, forensic_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, domain, file_hash, final_score, serialized))
        conn.commit()
        log.info("Saved candidate '%s' to DB (hash: %s…)", name, file_hash[:8])
    except sqlite3.IntegrityError:
        # Hash already exists — update the record with latest payload
        log.warning("  Hash %s… already exists. Updating forensic_json.", file_hash[:8])
        c.execute(
            'UPDATE candidates SET name=?, domain=?, final_score=?, forensic_json=? WHERE hash=?',
            (name, domain, final_score, serialized, file_hash)
        )
        conn.commit()
    finally:
        conn.close()

def get_all_candidates():
    """Returns all candidates sorted by final_score descending."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM candidates ORDER BY final_score DESC')
    rows = c.fetchall()
    conn.close()

    candidates = []
    for row in rows:
        cand = dict(row)
        try:
            payload = json.loads(cand.get("forensic_json") or "{}")
        except Exception:
            payload = {}

        scores = payload.get("scores", {})
        reliability = scores.get("reliability", 50.0)
        fraud_score = scores.get("fraud_score", 50.0)

        cand['reliability'] = reliability
        cand['fraud_score'] = fraud_score
        cand['risk'] = (
            'Low' if fraud_score < 20
            else 'Moderate' if fraud_score < 50
            else 'High'
        )
        cand['insights'] = payload.get("deterministic_insights", [])
        candidates.append(cand)
    return candidates

def get_candidate_by_id(candidate_id: int):
    """Returns a single candidate by DB id."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
    row = c.fetchone()
    conn.close()
    return _hydrate(row)

def get_candidate_by_hash(file_hash: str):
    """Returns a single candidate by SHA-256 hash (immutable key)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM candidates WHERE hash = ?', (file_hash,))
    row = c.fetchone()
    conn.close()

    # Try file backup if DB row not found
    if not row:
        report_path = os.path.join(REPORTS_DIR, f"{file_hash}.json")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return {"forensic_payload": payload, "hash": file_hash}
    return _hydrate(row)

def _hydrate(row):
    """Parses a DB row into a candidate dict with forensic_payload AND flat convenience fields."""
    if not row:
        return None
    cand = dict(row)
    try:
        payload = json.loads(cand.get("forensic_json") or "{}")
    except Exception:
        payload = {}

    cand["forensic_payload"] = payload

    # ── Flatten scores so compare route / compare_engine can read them directly ──
    scores = payload.get("scores", {})
    cand["reliability"]  = scores.get("reliability", 50.0)
    cand["fraud_score"]  = scores.get("fraud_score", 50.0)
    cand["risk"]         = scores.get("risk_level", "Unknown")
    cand["final_score"]  = scores.get("final_score", cand.get("final_score", 0.0))

    # ── Flatten candidate profile ───────────────────────────────────────────────
    candidate_info = payload.get("candidate", {})
    cand["skills"]            = candidate_info.get("skills", []) or payload.get("candidate", {}).get("skills", [])
    cand["experience_years"]  = candidate_info.get("experience_years", 0)
    cand["insights"]          = payload.get("deterministic_insights", [])

    return cand

# Initialize on import
init_db()
