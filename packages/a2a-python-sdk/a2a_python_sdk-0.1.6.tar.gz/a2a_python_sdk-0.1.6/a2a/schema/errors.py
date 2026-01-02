class A2AError(Exception):
    """Base exception for A2A SDK"""


class SchemaValidationError(A2AError):
    pass


class TransportError(A2AError):
    pass


class SecurityError(A2AError):
    pass


class RetryExhaustedError(A2AError):
    pass
