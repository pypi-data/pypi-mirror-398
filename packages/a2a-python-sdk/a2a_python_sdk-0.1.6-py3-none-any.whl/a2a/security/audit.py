from datetime import datetime

def audit(event: str, details: dict):
    log = {
        "event": event,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    print(log)  # replace with DB / SIEM later
