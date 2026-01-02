"""
A2A Agent Card Schema
--------------------
Agent discovery, identity, capabilities, policies, and endpoints.

Exposed via:
GET /.well-known/agent-card.json
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field
from a2a.protocol.notifications import WebhookConfig
from a2a.extensions.models import AgentExtension

# -------------------------------------------------------------------
# ENUMS
# -------------------------------------------------------------------

class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class InteractionMode(str, Enum):
    SYNC = "SYNC"
    ASYNC = "ASYNC"
    STREAM = "STREAM"


class TrustLevel(str, Enum):
    INTERNAL = "internal"
    PARTNER = "partner"
    EXTERNAL = "external"


# -------------------------------------------------------------------
# CAPABILITY MODELS
# -------------------------------------------------------------------

class Capability(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    tools_used: Optional[List[str]] = None
    requires_approval: bool = False
    risk_level: Optional[str] = None


class ToolSupport(BaseModel):
    tool_name: str
    version: Optional[str] = None
    description: Optional[str] = None


# -------------------------------------------------------------------
# AUTH
# -------------------------------------------------------------------

class AuthScheme(BaseModel):
    type: str  # e.g. oauth2, mtls, api_key
    description: Optional[str] = None


class TrustDeclaration(BaseModel):
    issuer: Optional[str] = None
    level: Optional[str] = None
    signed: bool = False

# -------------------------------------------------------------------
# SECURITY & POLICY
# -------------------------------------------------------------------

class SecurityProfile(BaseModel):
    supported_auth: List[str] = ["mTLS", "JWT"]
    encryption: List[str] = ["AES-256"]
    signing: List[str] = ["HMAC", "RSA"]
    trust_level: TrustLevel = TrustLevel.INTERNAL


class GovernanceProfile(BaseModel):
    policies: List[str] = []
    approval_required_for: List[str] = []
    audit_enabled: bool = True
    retention_days: int = 90


# -------------------------------------------------------------------
# PERFORMANCE & LIMITS
# -------------------------------------------------------------------

class RateLimits(BaseModel):
    requests_per_minute: Optional[int] = None
    concurrent_tasks: Optional[int] = None


class SLAProfile(BaseModel):
    avg_latency_ms: Optional[int] = None
    max_latency_ms: Optional[int] = None
    availability_pct: Optional[float] = None


class MCPResource(BaseModel):
    name: str
    description: Optional[str]
    schema: Dict[str, Any]  # tool method signature

# -------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------

class AgentEndpoints(BaseModel):
    a2a: str = Field(..., description="Primary A2A message endpoint")
    callback: Optional[str] = None
    health: Optional[str] = None
    metrics: Optional[str] = None


# -------------------------------------------------------------------
# AGENT CARD ROOT
# -------------------------------------------------------------------

class AgentCard(BaseModel):
    # ---------------- Identity ----------------
    agent_id: str
    agent_name: str
    agent_version: str = "1.0.0"

    agent_type: str
    framework: Optional[str] = None

    description: Optional[str] = None
    owner: Optional[str] = None

    # ---------------- Status ----------------
    status: AgentStatus = AgentStatus.ACTIVE
    started_at: datetime = Field(default_factory=datetime.utcnow)

    # ---------------- Capabilities ----------------
    capabilities: List[Capability]

    # ---------------- Interaction ----------------
    supported_message_types: List[str]
    interaction_modes: List[InteractionMode] = [InteractionMode.ASYNC]

    # ---------------- Tooling ----------------
    tools: Optional[List[ToolSupport]] = None

    # ---------------- Security & Governance ----------------
    security: SecurityProfile = Field(default_factory=SecurityProfile)
    governance: GovernanceProfile = Field(default_factory=GovernanceProfile)

    # ---------------- Performance ----------------
    rate_limits: Optional[RateLimits] = None
    sla: Optional[SLAProfile] = None

    # ---------------- Networking ----------------
    endpoints: AgentEndpoints

    # ---------------- Metadata ----------------
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    # ---------------- Push notifications (A2A spec) -------------------
    webhooks: list[WebhookConfig] | None = None
    
    # ---------------- Auth -------------------
    auth_schemes: Optional[List[AuthScheme]] = None
    trust: Optional[TrustDeclaration] = None

    # -------------- Extensions ---------------------- 
    extensions: Optional[List[AgentExtension]] = None


    class Config:
        json_schema_extra = {
            "description": "A2A Agent Card for discovery and negotiation"
        }
