"""
Audit Event Schemas for Agentic Fabric
======================================

Comprehensive audit logging event models that map to the audit_events database schema.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Event Type Enums
# ============================================================================

class EventType(str, Enum):
    """High-level event categories"""
    AUTH = "AUTH"
    TOOL = "TOOL"
    APP = "APP"
    AGENT = "AGENT"
    HTTP = "HTTP"
    CONNECTION = "CONNECTION"
    SECRET = "SECRET"
    CLI = "CLI"
    SDK = "SDK"
    SYSTEM = "SYSTEM"


class EventAction(str, Enum):
    """Event actions"""
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    INVOKED = "INVOKED"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    AUTHENTICATED = "AUTHENTICATED"
    AUTHORIZED = "AUTHORIZED"
    FAILED = "FAILED"
    LISTED = "LISTED"
    VIEWED = "VIEWED"
    EXECUTED = "EXECUTED"


class EventStatus(str, Enum):
    """Event status"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"


class ServiceName(str, Enum):
    """Service names"""
    GATEWAY = "gateway"
    REGISTRY = "registry"
    CLI = "cli"
    SDK = "sdk"
    WORKER = "worker"
    UI = "ui"
    AUDIT_SERVICE = "audit_service"


# ============================================================================
# Base Audit Event
# ============================================================================

class AuditEvent(BaseModel):
    """Base audit event that maps to audit_events table"""
    
    # Primary identification
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:16]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Event classification
    event_type: EventType
    action: EventAction
    status: EventStatus
    service: ServiceName
    
    # Identity (who)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Source information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    source: Optional[str] = None  # cli, sdk, ui, api
    
    # Resource (what)
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    parent_resource_id: Optional[str] = None
    
    # HTTP context
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    http_status_code: Optional[int] = None
    
    # Performance
    duration_ms: Optional[int] = None
    
    # Error information
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Correlation
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


# ============================================================================
# Specialized Event Types
# ============================================================================

class ToolInvocationEvent(BaseModel):
    """Tool invocation event - maps to tool_invocations table"""
    
    event_id: str = Field(default_factory=lambda: f"tool_{uuid4().hex[:16]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Who invoked
    user_id: str
    tenant_id: str
    
    # What tool
    tool_name: str
    tool_version: Optional[str] = None
    tool_type: Optional[str] = None
    
    # How invoked
    connection_id: Optional[str] = None
    method: Optional[str] = None  # oauth, oauth3, api
    
    # Action details
    action_name: Optional[str] = None  # send_message, list_files, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Result
    status: EventStatus
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    
    # Performance
    duration_ms: Optional[int] = None
    
    # Context
    agent_id: Optional[str] = None
    request_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class OAuthConnectionEvent(BaseModel):
    """OAuth connection event - maps to oauth_connections table"""
    
    event_id: str = Field(default_factory=lambda: f"oauth_{uuid4().hex[:16]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Who connected
    user_id: str
    tenant_id: str
    
    # What tool
    tool_name: str
    connection_id: Optional[str] = None
    
    # OAuth details
    oauth_method: Optional[str] = None  # oauth, oauth3
    oauth_flow: Optional[str] = None    # authorization_code
    
    # Result
    status: EventStatus
    error_message: Optional[str] = None
    
    # Connection metadata
    workspace_name: Optional[str] = None
    workspace_id: Optional[str] = None
    scopes: list = Field(default_factory=list)
    
    # Context
    request_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


# ============================================================================
# Event Builder Functions
# ============================================================================

def create_tool_invocation_event(
    user_id: str,
    tenant_id: str,
    tool_name: str,
    status: EventStatus,
    action_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    connection_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ToolInvocationEvent:
    """Create a tool invocation event"""
    return ToolInvocationEvent(
        user_id=user_id,
        tenant_id=tenant_id,
        tool_name=tool_name,
        status=status,
        action_name=action_name,
        parameters=parameters or {},
        duration_ms=duration_ms,
        error_message=error_message,
        connection_id=connection_id,
        agent_id=agent_id,
        request_id=request_id,
    )


def create_oauth_connection_event(
    user_id: str,
    tenant_id: str,
    tool_name: str,
    status: EventStatus,
    connection_id: Optional[str] = None,
    oauth_method: Optional[str] = None,
    error_message: Optional[str] = None,
    workspace_name: Optional[str] = None,
    scopes: Optional[list] = None,
) -> OAuthConnectionEvent:
    """Create an OAuth connection event"""
    return OAuthConnectionEvent(
        user_id=user_id,
        tenant_id=tenant_id,
        tool_name=tool_name,
        status=status,
        connection_id=connection_id,
        oauth_method=oauth_method,
        error_message=error_message,
        workspace_name=workspace_name,
        scopes=scopes or [],
    )


def create_http_audit_event(
    event_type: EventType,
    action: EventAction,
    status: EventStatus,
    service: ServiceName,
    http_method: str,
    http_path: str,
    http_status_code: int,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Create an HTTP audit event"""
    return AuditEvent(
        event_type=event_type,
        action=action,
        status=status,
        service=service,
        http_method=http_method,
        http_path=http_path,
        http_status_code=http_status_code,
        user_id=user_id,
        tenant_id=tenant_id,
        duration_ms=duration_ms,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        error_message=error_message,
        metadata=metadata or {},
    )


def create_cli_audit_event(
    action: EventAction,
    status: EventStatus,
    user_id: str,
    tenant_id: str,
    command: str,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Create a CLI command audit event"""
    return AuditEvent(
        event_type=EventType.CLI,
        action=action,
        status=status,
        service=ServiceName.CLI,
        user_id=user_id,
        tenant_id=tenant_id,
        source="cli",
        duration_ms=duration_ms,
        error_message=error_message,
        metadata={"command": command, **(metadata or {})},
    )

