import time

class CheatingDetector:
    def __init__(self):
        self.events = []
        # Generous cooldowns — prevent rapid-fire false positives
        self.cooldowns = {
            "NO_FACE":        20.0,   # must be absent 6s (threshold) then 20s before next log
            "WINDOW_UNFOCUS": 30.0,   # only log once per 30s of unfocus
            "TAB_SWITCH":     10.0,
            "MULTIPLE_FACES": 5.0,
            "DEV_TOOLS":      10.0
        }
        self.last_event_times = {
            "NO_FACE":        0,
            "WINDOW_UNFOCUS": 0,
            "TAB_SWITCH":     0,
            "MULTIPLE_FACES": 0,
            "DEV_TOOLS":      0
        }
        
    def log_event(self, event_type, severity):
        now = time.time()
        
        # Check cooldown — if still in window, skip
        if event_type in self.cooldowns:
            if now - self.last_event_times[event_type] < self.cooldowns[event_type]:
                return
            self.last_event_times[event_type] = now
                
        self.events.append({
            "timestamp":  now,
            "event_type": event_type,
            "severity":   severity
        })
        
    def get_penalty_score(self):
        points = 0
        for event in self.events:
            t = event['event_type']
            if   t == "MULTIPLE_FACES":  points += 5
            elif t == "DEV_TOOLS":       points += 4
            elif t == "TAB_SWITCH":      points += 2
            elif t == "WINDOW_UNFOCUS":  points += 2
            elif t == "NO_FACE":         points += 2
            else:                        points += 1
        return points
