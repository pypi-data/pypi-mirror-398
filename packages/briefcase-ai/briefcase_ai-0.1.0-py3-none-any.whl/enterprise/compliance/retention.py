"""
Data Retention Management

Implements configurable data retention policies for compliance requirements.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


class RetentionAction(Enum):
    """Actions to take when retention period expires"""
    DELETE = "delete"
    ARCHIVE = "archive"
    NOTIFY = "notify"
    MARK_FOR_REVIEW = "mark_for_review"


class DataType(Enum):
    """Types of data subject to retention policies"""
    SNAPSHOT = "snapshot"
    REPLAY = "replay"
    AUDIT_LOG = "audit_log"
    USER_DATA = "user_data"
    SESSION_DATA = "session_data"
    TEMP_DATA = "temp_data"


@dataclass
class DataRetentionPolicy:
    """Defines a data retention policy"""

    name: str
    data_type: DataType
    retention_days: int
    action: RetentionAction
    description: str = ""
    exceptions: Optional[Dict[str, Any]] = None
    active: bool = True

    def is_expired(self, created_date: datetime) -> bool:
        """Check if data is past retention period"""
        expiry_date = created_date + timedelta(days=self.retention_days)
        return datetime.utcnow() > expiry_date

    def get_expiry_date(self, created_date: datetime) -> datetime:
        """Get expiry date for data"""
        return created_date + timedelta(days=self.retention_days)


@dataclass
class RetentionJob:
    """Represents a retention enforcement job"""

    job_id: str
    policy: DataRetentionPolicy
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    items_processed: int = 0
    items_deleted: int = 0
    items_archived: int = 0
    error_message: Optional[str] = None


class RetentionManager(ABC):
    """
    Abstract base class for data retention management.

    This interface allows OSS core to enforce retention policies
    without depending on enterprise implementation details.
    """

    @abstractmethod
    async def add_policy(self, policy: DataRetentionPolicy) -> bool:
        """Add a new retention policy"""
        pass

    @abstractmethod
    async def update_policy(self, policy_name: str, policy: DataRetentionPolicy) -> bool:
        """Update an existing retention policy"""
        pass

    @abstractmethod
    async def remove_policy(self, policy_name: str) -> bool:
        """Remove a retention policy"""
        pass

    @abstractmethod
    async def get_policies(self) -> List[DataRetentionPolicy]:
        """Get all active retention policies"""
        pass

    @abstractmethod
    async def check_expired_data(self, data_type: DataType) -> List[Dict[str, Any]]:
        """Find data that has expired according to retention policies"""
        pass

    @abstractmethod
    async def enforce_retention(self, policy_name: Optional[str] = None) -> RetentionJob:
        """Enforce retention policies (all or specific policy)"""
        pass

    @abstractmethod
    async def get_retention_jobs(self, limit: int = 100) -> List[RetentionJob]:
        """Get retention job history"""
        pass


class DefaultRetentionManager(RetentionManager):
    """
    Default retention manager implementation
    """

    def __init__(self, data_store=None):
        self.policies: Dict[str, DataRetentionPolicy] = {}
        self.jobs: List[RetentionJob] = []
        self.data_store = data_store
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default retention policies"""
        default_policies = [
            DataRetentionPolicy(
                name="snapshot_retention",
                data_type=DataType.SNAPSHOT,
                retention_days=365,
                action=RetentionAction.ARCHIVE,
                description="Retain snapshots for 1 year, then archive"
            ),
            DataRetentionPolicy(
                name="replay_retention",
                data_type=DataType.REPLAY,
                retention_days=90,
                action=RetentionAction.DELETE,
                description="Delete replay data after 90 days"
            ),
            DataRetentionPolicy(
                name="audit_retention",
                data_type=DataType.AUDIT_LOG,
                retention_days=2555,  # 7 years
                action=RetentionAction.ARCHIVE,
                description="Retain audit logs for 7 years for compliance"
            ),
            DataRetentionPolicy(
                name="session_retention",
                data_type=DataType.SESSION_DATA,
                retention_days=30,
                action=RetentionAction.DELETE,
                description="Delete session data after 30 days"
            ),
            DataRetentionPolicy(
                name="temp_retention",
                data_type=DataType.TEMP_DATA,
                retention_days=7,
                action=RetentionAction.DELETE,
                description="Delete temporary data after 7 days"
            )
        ]

        for policy in default_policies:
            self.policies[policy.name] = policy

    async def add_policy(self, policy: DataRetentionPolicy) -> bool:
        """Add a new retention policy"""
        if policy.name in self.policies:
            return False

        self.policies[policy.name] = policy
        return True

    async def update_policy(self, policy_name: str, policy: DataRetentionPolicy) -> bool:
        """Update an existing retention policy"""
        if policy_name not in self.policies:
            return False

        self.policies[policy_name] = policy
        return True

    async def remove_policy(self, policy_name: str) -> bool:
        """Remove a retention policy"""
        if policy_name not in self.policies:
            return False

        del self.policies[policy_name]
        return True

    async def get_policies(self) -> List[DataRetentionPolicy]:
        """Get all active retention policies"""
        return [p for p in self.policies.values() if p.active]

    async def check_expired_data(self, data_type: DataType) -> List[Dict[str, Any]]:
        """Find data that has expired according to retention policies"""
        expired_items = []

        # Find policies for this data type
        relevant_policies = [p for p in self.policies.values()
                           if p.data_type == data_type and p.active]

        if not relevant_policies:
            return expired_items

        # In production, this would query the actual data store
        # For now, return mock expired data
        if data_type == DataType.SNAPSHOT:
            expired_items = [
                {
                    "id": "snap_001",
                    "created_at": datetime.utcnow() - timedelta(days=400),
                    "size_bytes": 1024000,
                    "policy": relevant_policies[0].name
                }
            ]
        elif data_type == DataType.REPLAY:
            expired_items = [
                {
                    "id": "replay_001",
                    "created_at": datetime.utcnow() - timedelta(days=100),
                    "size_bytes": 2048000,
                    "policy": relevant_policies[0].name
                }
            ]

        return expired_items

    async def enforce_retention(self, policy_name: Optional[str] = None) -> RetentionJob:
        """Enforce retention policies (all or specific policy)"""
        job_id = f"retention_job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        policies_to_enforce = []
        if policy_name:
            if policy_name in self.policies:
                policies_to_enforce = [self.policies[policy_name]]
        else:
            policies_to_enforce = [p for p in self.policies.values() if p.active]

        # Create job (for now, just track the first policy)
        job = RetentionJob(
            job_id=job_id,
            policy=policies_to_enforce[0] if policies_to_enforce else None,
            scheduled_at=datetime.utcnow()
        )

        if not policies_to_enforce:
            job.status = "failed"
            job.error_message = "No policies found to enforce"
            self.jobs.append(job)
            return job

        # Execute retention enforcement
        job.status = "running"
        job.executed_at = datetime.utcnow()

        total_processed = 0
        total_deleted = 0
        total_archived = 0

        for policy in policies_to_enforce:
            expired_items = await self.check_expired_data(policy.data_type)

            for item in expired_items:
                total_processed += 1

                if policy.action == RetentionAction.DELETE:
                    # In production, would actually delete the data
                    total_deleted += 1
                elif policy.action == RetentionAction.ARCHIVE:
                    # In production, would archive the data
                    total_archived += 1
                elif policy.action == RetentionAction.NOTIFY:
                    # Send notification about expiring data
                    await self._send_retention_notification(item, policy)

        job.items_processed = total_processed
        job.items_deleted = total_deleted
        job.items_archived = total_archived
        job.status = "completed"

        self.jobs.append(job)
        return job

    async def get_retention_jobs(self, limit: int = 100) -> List[RetentionJob]:
        """Get retention job history"""
        # Sort by scheduled time (newest first) and apply limit
        sorted_jobs = sorted(self.jobs, key=lambda x: x.scheduled_at, reverse=True)
        return sorted_jobs[:limit]

    async def _send_retention_notification(self, item: Dict[str, Any], policy: DataRetentionPolicy):
        """Send notification about data subject to retention"""
        # In production, would send actual notifications
        # via email, Slack, or other channels
        pass

    def get_retention_statistics(self) -> Dict[str, Any]:
        """Get retention statistics for reporting"""
        stats = {
            "active_policies": len([p for p in self.policies.values() if p.active]),
            "total_jobs_run": len(self.jobs),
            "last_job_date": max([j.executed_at for j in self.jobs if j.executed_at], default=None),
            "policy_breakdown": {}
        }

        for policy in self.policies.values():
            if policy.active:
                stats["policy_breakdown"][policy.name] = {
                    "data_type": policy.data_type.value,
                    "retention_days": policy.retention_days,
                    "action": policy.action.value
                }

        return stats


# Predefined policies for common compliance requirements
GDPR_POLICIES = [
    DataRetentionPolicy(
        name="gdpr_user_data",
        data_type=DataType.USER_DATA,
        retention_days=2555,  # 7 years max under GDPR
        action=RetentionAction.DELETE,
        description="GDPR compliant user data retention"
    )
]

SOX_POLICIES = [
    DataRetentionPolicy(
        name="sox_audit_logs",
        data_type=DataType.AUDIT_LOG,
        retention_days=2555,  # 7 years for SOX
        action=RetentionAction.ARCHIVE,
        description="SOX compliant audit log retention"
    )
]


# Factory function for OSS integration
def create_retention_manager(config: Optional[Dict[str, Any]] = None) -> RetentionManager:
    """
    Factory function to create retention manager.

    This function can be called by OSS core to get a retention manager
    without importing enterprise-specific classes.
    """
    return DefaultRetentionManager()