from flask import Flask, render_template, request, jsonify
import uuid
from interview_engine import InterviewEngine
from session_storage import save_session, load_session
import os

app = Flask(__name__)
app.secret_key = "super_secret_interview_key"

# In-memory storage for active sessions
active_sessions = {}

@app.route('/interview/<candidate_hash>')
def interview(candidate_hash):
    return render_template('interview.html', candidate_hash=candidate_hash)

@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.json
    candidate_hash = data.get('candidate_hash', str(uuid.uuid4()))
    
    # Initialize engine for this candidate
    active_sessions[candidate_hash] = InterviewEngine(candidate_hash)
    
    return jsonify({"status": "success", "candidate_hash": candidate_hash})

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    image_b64 = data.get('image')
    
    engine = active_sessions.get(candidate_hash)
    if not engine or not image_b64:
        # If session dropped, ignore or error
        return jsonify({"error": "Invalid session or missing image"}), 400
        
    metrics = engine.process_frame(image_b64)
    return jsonify(metrics)

@app.route('/cheating_event', methods=['POST'])
def cheating_event():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    event_type = data.get('event_type')
    
    engine = active_sessions.get(candidate_hash)
    if not engine or not event_type:
        return jsonify({"error": "Invalid session or missing event"}), 400
        
    engine.log_cheating_event(event_type)
    return jsonify({"status": "logged"})

@app.route('/load_questions/', defaults={'pattern': ''}, methods=['GET'])
@app.route('/load_questions/<pattern>', methods=['GET'])
def load_questions(pattern):
    # Simplified loader: checks questions directory for matching files
    import glob
    import json
    q_dir = os.path.join(app.root_path, 'questions')
    files = glob.glob(os.path.join(q_dir, f"*{pattern}*.json"))
    
    questions = []
    for f in files:
        try:
            with open(f, 'r') as q_file:
                questions.append(json.load(q_file))
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
    # Sort questions by ID to maintain Q1, Q2, Q3 order
    questions.sort(key=lambda item: item.get("id", ""))
            
    return jsonify(questions)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    question = data.get('question')
    answer = data.get('answer')
    
    engine = active_sessions.get(candidate_hash)
    if not engine:
        return jsonify({"error": "Invalid session"}), 400
        
    metrics = engine.get_current_metrics()
    
    from answer_evaluator import AnswerEvaluator
    evaluator = AnswerEvaluator()
    eval_result = evaluator.evaluate(question, answer, metrics)
    
    # Store evaluated answer in session object
    engine.log_evaluated_answer({
        "question": question,
        "answer": answer,
        "evaluation": eval_result
    })
    
    return jsonify(eval_result)

@app.route('/get_metrics', methods=['GET'])
def get_metrics():
    candidate_hash = request.args.get('candidate_hash')
    engine = active_sessions.get(candidate_hash)
    if not engine:
        return jsonify({"error": "Invalid session"}), 400
        
    return jsonify(engine.get_current_metrics())

@app.route('/end_session', methods=['POST'])
def end_session():
    data = request.json
    candidate_hash = data.get('candidate_hash')
    
    engine = active_sessions.get(candidate_hash)
    if not engine:
        return jsonify({"error": "Invalid session"}), 400
        
    summary = engine.finalize_session()
    save_session(candidate_hash, summary)
    
    # Cleanup memory
    del active_sessions[candidate_hash]
    
    # 🔥 FUTURE INTEGRATION PLAN (COMMENT ONLY)
    # Later integration method:
    # Resume system sends candidate_hash
    # Interview system returns session JSON via API
    # Resume report page pulls interview_summary
    # Combine forensic + behavioral scoring
    # But DO NOT implement now.
    
    return jsonify({"status": "success", "summary": summary})

@app.route('/session_summary/<candidate_hash>')
def session_summary(candidate_hash):
    summary = load_session(candidate_hash)
    if not summary:
        return "Session not found", 404
    return render_template('session_complete.html', summary=summary, candidate_hash=candidate_hash)

if __name__ == '__main__':
    # Ensure sessions directory exists
    os.makedirs('sessions', exist_ok=True)
    app.run(port=5000, debug=True)
