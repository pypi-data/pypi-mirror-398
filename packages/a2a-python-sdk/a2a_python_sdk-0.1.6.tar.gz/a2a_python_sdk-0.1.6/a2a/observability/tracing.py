def attach_trace(message, trace_id):
    message.observability = message.observability or {}
    message.observability["trace_id"] = trace_id
