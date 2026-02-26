import re
import random

class AnswerEvaluator:
    def evaluate(self, question, answer, metrics):
        word_count = len(answer.split())
        
        # Simulate semantic match (0-100)
        semantic_match = min(100, word_count * 2)
        
        # 1. Length adequacy
        length_score = min(100, word_count * 3)
        
        # 2. Clarity / Coherence — use stdlib random (no numpy dependency)
        coherence_score = random.randint(60, 95) if word_count > 5 else 20
        
        # 3. Speech fluency simulation
        fluency_score = random.randint(70, 100) if word_count > 10 else 30
        
        # Speech Integrity Formula
        answer_score = int(
            (semantic_match * 0.40) + 
            (length_score   * 0.20) + 
            (coherence_score * 0.20) + 
            (fluency_score  * 0.20)
        )
        
        # Minimum Floor Logic for Speech
        if word_count > 20:
            answer_score = max(answer_score, 45)
        elif word_count > 5:
            answer_score = max(answer_score, 20)
            
        return {
            "answer_quality":  answer_score,
            "word_count":      word_count,
            "semantic_match":  semantic_match,
            "fluency_score":   fluency_score
        }
