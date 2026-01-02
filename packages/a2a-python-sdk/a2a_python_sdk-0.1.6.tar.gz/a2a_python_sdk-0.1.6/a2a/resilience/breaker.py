import time

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_time=60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time = None
        self.open = False

    def record_success(self):
        self.failures = 0
        self.open = False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.open = True

    def allow_request(self):
        if not self.open:
            return True

        # cooldown
        if time.time() - self.last_failure_time > self.recovery_time:
            self.open = False
            self.failures = 0
            return True

        return False
