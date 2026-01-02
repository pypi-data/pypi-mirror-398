import time
from a2a.schema.errors import RetryExhaustedError

def retry(fn, retries=3, backoff=1):
    for attempt in range(retries):
        try:
            return fn()
        except Exception:
            if attempt == retries - 1:
                raise RetryExhaustedError()
            time.sleep(backoff * (2 ** attempt))
