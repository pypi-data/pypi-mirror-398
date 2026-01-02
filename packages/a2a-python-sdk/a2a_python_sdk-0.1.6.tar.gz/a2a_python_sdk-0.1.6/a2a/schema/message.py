"""
A2A Message Schema
-----------------
Canonical Agent-to-Agent message definition.

This file represents the HEART of the A2A protocol.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from a2a.schema.parts import MessagePart   # 🆕 NEW


# -------------------------------------------------------------------
# ENUMS
# -------------------------------------------------------------------

class MessageType(str, Enum):
    DISCOVERY = "DISCOVERY"
    NEGOTIATION = "NEGOTIATION"
    TASK_REQUEST = "TASK_REQUEST"
    TASK_RESPONSE = "TASK_RESPONSE"
    TASK_UPDATE = "TASK_UPDATE"
    STREAM = "STREAM"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    MEMORY_READ = "MEMORY_READ"
    MEMORY_WRITE = "MEMORY_WRITE"
    STATE_SYNC = "STATE_SYNC"
    ERROR = "ERROR"
    HEARTBEAT = "HEARTBEAT"
    CANCEL = "CANCEL"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    GOVERNANCE_EVENT = "GOVERNANCE_EVENT"


class Intent(str, Enum):
    DISCOVER_AGENT = "discover_agent"
    DELEGATE_TASK = "delegate_task"
    COLLABORATE = "collaborate"
    REQUEST_REASONING = "request_reasoning"
    EXECUTE_ACTION = "execute_action"
    VALIDATE_RESULT = "validate_result"
    STORE_MEMORY = "store_memory"
    FETCH_MEMORY = "fetch_memory"
    SYNC_STATE = "sync_state"
    ABORT_TASK = "abort_task"


class Priority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentType(str, Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    TOOL = "tool"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"
    HUMAN = "human"


class MemoryOperation(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# -------------------------------------------------------------------
# AGENT IDENTITY
# -------------------------------------------------------------------

class AgentIdentity(BaseModel):
    agent_id: str
    agent_name: Optional[str] = None
    agent_type: AgentType
    framework: Optional[str] = None
    capabilities: List[str] = []
    endpoint: Optional[str] = None
    instance_id: Optional[str] = None


# -------------------------------------------------------------------
# PAYLOAD MODELS (LEGACY / OPTIONAL)
# -------------------------------------------------------------------

class DiscoveryPayload(BaseModel):
    required_capabilities: List[str]
    domain: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None


class ToolPayload(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class ErrorPayload(BaseModel):
    error_code: str
    message: str
    severity: Priority
    retryable: bool = False
    suggested_action: Optional[str] = None


# -------------------------------------------------------------------
# CONTEXT / STATE / MEMORY
# -------------------------------------------------------------------

class Context(BaseModel):
    user_goal: Optional[str] = None
    domain: Optional[str] = None
    business_unit: Optional[str] = None
    environment: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None


class State(BaseModel):
    workflow_id: Optional[UUID] = None
    step: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    progress_pct: Optional[int] = None
    parent_task_id: Optional[UUID] = None


class Memory(BaseModel):
    operation: MemoryOperation
    memory_type: MemoryType
    scope: str = "agent"
    data: Dict[str, Any]


# -------------------------------------------------------------------
# CONTROL / SECURITY / OBSERVABILITY / GOVERNANCE
# -------------------------------------------------------------------

class Control(BaseModel):
    timeout_ms: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    circuit_breaker: bool = False
    cancel_token: Optional[UUID] = None


class Security(BaseModel):
    auth_type: Optional[str] = None
    token: Optional[str] = None
    signature: Optional[str] = None
    encryption: Optional[str] = None
    trust_level: Optional[str] = None


class Observability(BaseModel):
    trace_id: Optional[UUID] = None
    span_id: Optional[UUID] = None
    parent_span_id: Optional[UUID] = None
    metrics: Optional[Dict[str, Any]] = None
    logs: Optional[List[str]] = None


class Governance(BaseModel):
    policy_id: Optional[str] = None
    approval_required: bool = False
    approved_by: Optional[str] = None
    risk_level: Optional[str] = None
    audit_required: bool = False
    data_retention_days: Optional[int] = None


# -------------------------------------------------------------------
# RESPONSE CONTRACT
# -------------------------------------------------------------------

class ResponseContract(BaseModel):
    expected: bool = True
    response_type: Optional[str] = "ASYNC"
    callback_url: Optional[str] = None


# -------------------------------------------------------------------
# A2A MESSAGE (ROOT)
# -------------------------------------------------------------------

class A2AMessage(BaseModel):
    """
    Canonical A2A Message.
    Messages operate ON tasks, they are not tasks themselves.
    """

    a2a_version: str = "1.0"

    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None

    # 🆕 REQUIRED BY A2A
    task_id: Optional[UUID] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    sender: AgentIdentity
    receiver: AgentIdentity

    message_type: MessageType
    intent: Intent
    priority: Priority = Priority.NORMAL

    # 🆕 A2A PARTS (PRIMARY CONTENT)
    parts: Optional[List[MessagePart]] = None

    # 🆕 ARTIFACT REFERENCES (TASK OUTPUTS)
    artifact_ids: Optional[List[UUID]] = None

    reference_task_ids: Optional[List[UUID]] = None

    # Legacy / optional payload (kept for compatibility)
    payload: Optional[
        DiscoveryPayload
        | ToolPayload
        | ErrorPayload
        | Dict[str, Any]
    ] = None

    context: Optional[Context] = None
    state: Optional[State] = None
    memory: Optional[Memory] = None

    control: Optional[Control] = None
    security: Optional[Security] = None
    observability: Optional[Observability] = None
    governance: Optional[Governance] = None

    response: Optional[ResponseContract] = None

    class Config:
        json_schema_extra = {
            "description": "Canonical A2A message schema (fully spec-compliant)"
        }
