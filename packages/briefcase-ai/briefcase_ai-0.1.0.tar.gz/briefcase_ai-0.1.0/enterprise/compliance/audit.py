"""
Audit Logging for Compliance

Provides comprehensive audit trails for all system activities
to support compliance requirements (SOC2, GDPR, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class AuditEventType(Enum):
    """Types of auditable events"""

    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password_change"

    # Data access events
    SNAPSHOT_READ = "data.snapshot.read"
    SNAPSHOT_WRITE = "data.snapshot.write"
    SNAPSHOT_DELETE = "data.snapshot.delete"

    # Replay events
    REPLAY_START = "replay.start"
    REPLAY_COMPLETE = "replay.complete"
    REPLAY_FAILURE = "replay.failure"

    # Administrative events
    USER_CREATE = "admin.user.create"
    USER_UPDATE = "admin.user.update"
    USER_DELETE = "admin.user.delete"
    ROLE_ASSIGN = "admin.role.assign"
    ROLE_REVOKE = "admin.role.revoke"

    # Configuration changes
    CONFIG_UPDATE = "config.update"
    POLICY_UPDATE = "policy.update"

    # Security events
    UNAUTHORIZED_ACCESS = "security.unauthorized_access"
    PERMISSION_DENIED = "security.permission_denied"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"


@dataclass
class AuditEvent:
    """Represents an auditable event"""

    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    details: Optional[Dict[str, Any]] = None
    risk_level: str = "low"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create event from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['event_type'] = AuditEventType(data['event_type'])
        return cls(**data)


class AuditLogger(ABC):
    """
    Abstract base class for audit logging.

    This interface allows OSS core to log audit events without depending
    on enterprise implementation details.
    """

    @abstractmethod
    async def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event"""
        pass

    @abstractmethod
    async def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        pass

    @abstractmethod
    async def get_event_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> int:
        """Get count of events matching criteria"""
        pass


class DefaultAuditLogger(AuditLogger):
    """
    Default audit logger implementation

    In production, this would integrate with:
    - Secure audit database
    - SIEM systems
    - Compliance platforms
    """

    def __init__(self, storage_backend: Optional[str] = None):
        # In-memory storage for demo purposes
        # Production implementation would use secure database
        self.events: List[AuditEvent] = []
        self.storage_backend = storage_backend or "memory"

    async def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event"""
        try:
            # Add event to storage
            self.events.append(event)

            # In production, would also:
            # - Write to secure audit database
            # - Send to SIEM system
            # - Trigger alerts for high-risk events
            if event.risk_level in ["high", "critical"]:
                await self._trigger_security_alert(event)

            return True
        except Exception:
            # Audit logging failures should not break the system
            # but should be reported through separate channels
            return False

    async def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        filtered_events = self.events

        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]

        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]

        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]

        # Sort by timestamp (newest first) and apply limit
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_events[:limit]

    async def get_event_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> int:
        """Get count of events matching criteria"""
        events = await self.query_events(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types,
            limit=float('inf')  # No limit for counting
        )
        return len(events)

    async def _trigger_security_alert(self, event: AuditEvent):
        """Trigger security alert for high-risk events"""
        # In production, would:
        # - Send to security team
        # - Integrate with incident response
        # - Log to security systems
        pass

    def export_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"
    ) -> str:
        """Export events for compliance reporting"""
        events = [e for e in self.events]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        if format == "json":
            return json.dumps([e.to_dict() for e in events], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Helper functions for common audit events
async def log_user_login(logger: AuditLogger, user_id: str, session_id: str,
                        source_ip: str, success: bool = True):
    """Log user login event"""
    event = AuditEvent(
        event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        session_id=session_id,
        source_ip=source_ip,
        success=success,
        risk_level="medium" if not success else "low"
    )
    await logger.log_event(event)


async def log_data_access(logger: AuditLogger, user_id: str, resource_type: str,
                         resource_id: str, operation: str):
    """Log data access event"""
    event_type_map = {
        "read": AuditEventType.SNAPSHOT_READ,
        "write": AuditEventType.SNAPSHOT_WRITE,
        "delete": AuditEventType.SNAPSHOT_DELETE
    }

    event = AuditEvent(
        event_type=event_type_map.get(operation, AuditEventType.SNAPSHOT_READ),
        timestamp=datetime.utcnow(),
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        risk_level="high" if operation == "delete" else "low"
    )
    await logger.log_event(event)


# Factory function for OSS integration
def create_audit_logger(config: Optional[Dict[str, Any]] = None) -> AuditLogger:
    """
    Factory function to create audit logger.

    This function can be called by OSS core to get an audit logger
    without importing enterprise-specific classes.
    """
    return DefaultAuditLogger(
        storage_backend=config.get('storage_backend') if config else None
    )