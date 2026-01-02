class FallbackExecutor:
    def __init__(self, primary_llm, fallback_llm, breaker):
        self.primary = primary_llm
        self.fallback = fallback_llm
        self.breaker = breaker

    def invoke(self, messages):
        if not self.breaker.allow_request():
            return self.fallback.invoke(messages)

        try:
            result = self.primary.invoke(messages)
            self.breaker.record_success()
            return result
        except Exception:
            self.breaker.record_failure()
            return self.fallback.invoke(messages)
