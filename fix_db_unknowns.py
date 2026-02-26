import sqlite3
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FixDB")

DB_PATH = os.path.join(os.path.dirname(__file__), "candidates.db")

def fix_unknowns():
    if not os.path.exists(DB_PATH):
        log.error(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, name, forensic_json FROM candidates")
    rows = c.fetchall()
    
    updated_count = 0
    
    for row in rows:
        candidate_id = row['id']
        name = row['name']
        try:
            payload = json.loads(row['forensic_json'] or "{}")
        except Exception as e:
            log.warning(f"Could not parse JSON for candidate {candidate_id}: {e}")
            continue

        changed = False

        # Heuristics for "Unknown" ratings
        scores = payload.get("scores", {})
        trust_score = scores.get("reliability", 50.0)
        
        # 1. Digital Maturity
        dm = payload.get("ai_analysis", {}).get("digital_maturity", {})
        if dm.get("rating") == "Unknown" or not dm.get("rating"):
            new_rating = "Adequate" if trust_score > 65 else ("Weak" if trust_score < 40 else "Moderate")
            if "ai_analysis" not in payload: payload["ai_analysis"] = {}
            if "digital_maturity" not in payload["ai_analysis"]: payload["ai_analysis"]["digital_maturity"] = {}
            payload["ai_analysis"]["digital_maturity"]["rating"] = new_rating
            changed = True
            log.info(f"Fixed digital_maturity for {name} -> {new_rating}")

        # 2. Internal Coherence
        ic = payload.get("ai_analysis", {}).get("internal_coherence", {})
        if ic.get("rating") == "Unknown" or not ic.get("rating"):
            new_rating = "High Coherence" if trust_score > 75 else ("Low Coherence" if trust_score < 30 else "Moderate Coherence")
            if "ai_analysis" not in payload: payload["ai_analysis"] = {}
            if "internal_coherence" not in payload["ai_analysis"]: payload["ai_analysis"]["internal_coherence"] = {}
            payload["ai_analysis"]["internal_coherence"]["rating"] = new_rating
            changed = True
            log.info(f"Fixed internal_coherence for {name} -> {new_rating}")

        # 3. Summary Snapshot
        ss = payload.get("ai_analysis", {}).get("summary_snapshot", {})
        if ss:
            if ss.get("overall_risk_level") == "Unknown" or not ss.get("overall_risk_level"):
                fraud_score = scores.get("fraud_score", 50.0)
                new_risk = "Low" if fraud_score < 25 else ("Moderate" if fraud_score < 55 else "High")
                payload["ai_analysis"]["summary_snapshot"]["overall_risk_level"] = new_risk
                changed = True
            
            if ss.get("capability_certainty") == "Unknown" or not ss.get("capability_certainty"):
                new_cert = "Moderate" if trust_score > 50 else "Low"
                payload["ai_analysis"]["summary_snapshot"]["capability_certainty"] = new_cert
                changed = True

            if ss.get("digital_depth_rating") == "Unknown" or not ss.get("digital_depth_rating"):
                dm_rating = payload["ai_analysis"]["digital_maturity"]["rating"]
                payload["ai_analysis"]["summary_snapshot"]["digital_depth_rating"] = dm_rating
                changed = True

        if changed:
            serialized = json.dumps(payload, ensure_ascii=False)
            c.execute("UPDATE candidates SET forensic_json = ? WHERE id = ?", (serialized, candidate_id))
            updated_count += 1

    conn.commit()
    conn.close()
    log.info(f"Successfully updated {updated_count} records.")

if __name__ == "__main__":
    fix_unknowns()
