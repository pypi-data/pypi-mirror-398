import time

_seen = {}

WINDOW_SECONDS = 300  # 5 minutes

def check(message_id: str):
    now = time.time()

    if message_id in _seen:
        raise RuntimeError("Replay detected")

    _seen[message_id] = now

    # cleanup
    for k, v in list(_seen.items()):
        if now - v > WINDOW_SECONDS:
            del _seen[k]
