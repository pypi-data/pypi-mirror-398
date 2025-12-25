"""
Multi-tenant Management

Provides secure tenant isolation and management for enterprise hosted deployments.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class TenantTier(Enum):
    """Tenant service tiers"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TenantStatus(Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    DISABLED = "disabled"


@dataclass
class TenantQuotas:
    """Resource quotas for a tenant"""

    max_snapshots: int = 1000
    max_replays_per_day: int = 100
    max_storage_gb: int = 10
    max_users: int = 10
    max_concurrent_replays: int = 5
    retention_days: int = 30
    api_calls_per_minute: int = 100


@dataclass
class TenantUsage:
    """Current resource usage for a tenant"""

    snapshots_count: int = 0
    replays_today: int = 0
    storage_used_gb: float = 0.0
    users_count: int = 0
    concurrent_replays: int = 0
    api_calls_last_minute: int = 0
    last_activity: Optional[datetime] = None


@dataclass
class Tenant:
    """Represents a tenant in the multi-tenant system"""

    tenant_id: str
    name: str
    tier: TenantTier
    status: TenantStatus
    created_at: datetime
    quotas: TenantQuotas = field(default_factory=TenantQuotas)
    usage: TenantUsage = field(default_factory=TenantUsage)
    metadata: Dict[str, Any] = field(default_factory=dict)
    custom_config: Optional[Dict[str, Any]] = None

    def is_quota_exceeded(self, resource: str) -> bool:
        """Check if a specific resource quota is exceeded"""
        quota_map = {
            "snapshots": (self.usage.snapshots_count, self.quotas.max_snapshots),
            "replays": (self.usage.replays_today, self.quotas.max_replays_per_day),
            "storage": (self.usage.storage_used_gb, self.quotas.max_storage_gb),
            "users": (self.usage.users_count, self.quotas.max_users),
            "concurrent_replays": (self.usage.concurrent_replays, self.quotas.max_concurrent_replays),
            "api_calls": (self.usage.api_calls_last_minute, self.quotas.api_calls_per_minute)
        }

        if resource in quota_map:
            current, limit = quota_map[resource]
            return current >= limit

        return False

    def get_quota_utilization(self) -> Dict[str, float]:
        """Get quota utilization percentages"""
        return {
            "snapshots": min(100.0, (self.usage.snapshots_count / self.quotas.max_snapshots) * 100),
            "replays": min(100.0, (self.usage.replays_today / self.quotas.max_replays_per_day) * 100),
            "storage": min(100.0, (self.usage.storage_used_gb / self.quotas.max_storage_gb) * 100),
            "users": min(100.0, (self.usage.users_count / self.quotas.max_users) * 100),
            "concurrent_replays": min(100.0, (self.usage.concurrent_replays / self.quotas.max_concurrent_replays) * 100),
            "api_calls": min(100.0, (self.usage.api_calls_last_minute / self.quotas.api_calls_per_minute) * 100)
        }


class TenantManager(ABC):
    """
    Abstract base class for tenant management.

    This interface allows hosted services to manage multi-tenancy
    without depending on enterprise implementation details.
    """

    @abstractmethod
    async def create_tenant(
        self,
        name: str,
        tier: TenantTier,
        admin_email: str
    ) -> Tenant:
        """Create a new tenant"""
        pass

    @abstractmethod
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        pass

    @abstractmethod
    async def update_tenant(self, tenant: Tenant) -> bool:
        """Update tenant configuration"""
        pass

    @abstractmethod
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all associated data"""
        pass

    @abstractmethod
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        limit: int = 100
    ) -> List[Tenant]:
        """List tenants with optional filters"""
        pass

    @abstractmethod
    async def check_quota(self, tenant_id: str, resource: str) -> bool:
        """Check if tenant has quota available for resource"""
        pass

    @abstractmethod
    async def update_usage(self, tenant_id: str, resource: str, delta: int = 1) -> bool:
        """Update resource usage for tenant"""
        pass

    @abstractmethod
    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive stats for a tenant"""
        pass


class DefaultTenantManager(TenantManager):
    """
    Default tenant manager implementation

    In production, this would integrate with:
    - Database for tenant metadata
    - Billing systems
    - Identity providers
    - Resource management systems
    """

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self._initialize_default_quotas()

    def _initialize_default_quotas(self):
        """Initialize default quotas for different tiers"""
        self.tier_quotas = {
            TenantTier.BASIC: TenantQuotas(
                max_snapshots=100,
                max_replays_per_day=10,
                max_storage_gb=1,
                max_users=5,
                max_concurrent_replays=1,
                retention_days=7,
                api_calls_per_minute=50
            ),
            TenantTier.PROFESSIONAL: TenantQuotas(
                max_snapshots=1000,
                max_replays_per_day=100,
                max_storage_gb=10,
                max_users=25,
                max_concurrent_replays=5,
                retention_days=30,
                api_calls_per_minute=200
            ),
            TenantTier.ENTERPRISE: TenantQuotas(
                max_snapshots=10000,
                max_replays_per_day=1000,
                max_storage_gb=100,
                max_users=100,
                max_concurrent_replays=20,
                retention_days=365,
                api_calls_per_minute=1000
            )
        }

    async def create_tenant(
        self,
        name: str,
        tier: TenantTier,
        admin_email: str
    ) -> Tenant:
        """Create a new tenant"""
        tenant_id = str(uuid.uuid4())
        quotas = self.tier_quotas.get(tier, TenantQuotas())

        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            tier=tier,
            status=TenantStatus.TRIAL,
            created_at=datetime.utcnow(),
            quotas=quotas,
            metadata={"admin_email": admin_email}
        )

        self.tenants[tenant_id] = tenant

        # In production, would also:
        # - Create database schemas
        # - Set up billing
        # - Configure monitoring
        # - Send welcome email

        return tenant

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)

    async def update_tenant(self, tenant: Tenant) -> bool:
        """Update tenant configuration"""
        if tenant.tenant_id in self.tenants:
            self.tenants[tenant.tenant_id] = tenant
            return True
        return False

    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all associated data"""
        if tenant_id in self.tenants:
            # In production, would:
            # - Archive/delete all tenant data
            # - Cancel billing
            # - Remove access
            # - Clean up resources

            del self.tenants[tenant_id]
            return True
        return False

    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        limit: int = 100
    ) -> List[Tenant]:
        """List tenants with optional filters"""
        tenants = list(self.tenants.values())

        if status:
            tenants = [t for t in tenants if t.status == status]

        if tier:
            tenants = [t for t in tenants if t.tier == tier]

        # Sort by creation date (newest first)
        tenants.sort(key=lambda x: x.created_at, reverse=True)

        return tenants[:limit]

    async def check_quota(self, tenant_id: str, resource: str) -> bool:
        """Check if tenant has quota available for resource"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.status != TenantStatus.ACTIVE:
            return False

        return not tenant.is_quota_exceeded(resource)

    async def update_usage(self, tenant_id: str, resource: str, delta: int = 1) -> bool:
        """Update resource usage for tenant"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        # Update usage based on resource type
        if resource == "snapshots":
            tenant.usage.snapshots_count += delta
        elif resource == "replays":
            tenant.usage.replays_today += delta
        elif resource == "storage":
            tenant.usage.storage_used_gb += delta
        elif resource == "users":
            tenant.usage.users_count += delta
        elif resource == "concurrent_replays":
            tenant.usage.concurrent_replays += delta
        elif resource == "api_calls":
            tenant.usage.api_calls_last_minute += delta

        tenant.usage.last_activity = datetime.utcnow()
        return True

    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive stats for a tenant"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {}

        return {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "tier": tenant.tier.value,
            "status": tenant.status.value,
            "created_at": tenant.created_at.isoformat(),
            "quotas": {
                "max_snapshots": tenant.quotas.max_snapshots,
                "max_replays_per_day": tenant.quotas.max_replays_per_day,
                "max_storage_gb": tenant.quotas.max_storage_gb,
                "max_users": tenant.quotas.max_users,
                "max_concurrent_replays": tenant.quotas.max_concurrent_replays,
                "retention_days": tenant.quotas.retention_days,
                "api_calls_per_minute": tenant.quotas.api_calls_per_minute
            },
            "usage": {
                "snapshots_count": tenant.usage.snapshots_count,
                "replays_today": tenant.usage.replays_today,
                "storage_used_gb": tenant.usage.storage_used_gb,
                "users_count": tenant.usage.users_count,
                "concurrent_replays": tenant.usage.concurrent_replays,
                "api_calls_last_minute": tenant.usage.api_calls_last_minute,
                "last_activity": tenant.usage.last_activity.isoformat() if tenant.usage.last_activity else None
            },
            "quota_utilization": tenant.get_quota_utilization(),
            "quota_warnings": [
                resource for resource, utilization in tenant.get_quota_utilization().items()
                if utilization > 80.0
            ]
        }

    async def upgrade_tenant(self, tenant_id: str, new_tier: TenantTier) -> bool:
        """Upgrade tenant to a new tier"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        # Update tier and quotas
        tenant.tier = new_tier
        tenant.quotas = self.tier_quotas.get(new_tier, TenantQuotas())

        # In production, would also:
        # - Update billing
        # - Notify tenant
        # - Log the change

        return True

    async def suspend_tenant(self, tenant_id: str, reason: str) -> bool:
        """Suspend a tenant"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.SUSPENDED
        tenant.metadata["suspension_reason"] = reason
        tenant.metadata["suspended_at"] = datetime.utcnow().isoformat()

        # In production, would also:
        # - Disable access
        # - Stop billing
        # - Notify tenant

        return True

    async def reactivate_tenant(self, tenant_id: str) -> bool:
        """Reactivate a suspended tenant"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.ACTIVE
        if "suspension_reason" in tenant.metadata:
            del tenant.metadata["suspension_reason"]
        if "suspended_at" in tenant.metadata:
            del tenant.metadata["suspended_at"]

        tenant.metadata["reactivated_at"] = datetime.utcnow().isoformat()

        return True

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide tenant statistics"""
        total_tenants = len(self.tenants)
        active_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.ACTIVE])
        trial_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.TRIAL])

        tier_distribution = {}
        for tier in TenantTier:
            tier_distribution[tier.value] = len([
                t for t in self.tenants.values() if t.tier == tier
            ])

        total_usage = {
            "snapshots": sum(t.usage.snapshots_count for t in self.tenants.values()),
            "replays_today": sum(t.usage.replays_today for t in self.tenants.values()),
            "storage_gb": sum(t.usage.storage_used_gb for t in self.tenants.values()),
            "users": sum(t.usage.users_count for t in self.tenants.values())
        }

        return {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "trial_tenants": trial_tenants,
            "tier_distribution": tier_distribution,
            "total_usage": total_usage,
            "average_utilization": {
                resource: (usage / total_tenants) if total_tenants > 0 else 0
                for resource, usage in total_usage.items()
            }
        }


# Factory function for OSS integration
def create_tenant_manager(config: Optional[Dict[str, Any]] = None) -> TenantManager:
    """
    Factory function to create tenant manager.

    This function can be called by hosted services to get a tenant manager
    without importing enterprise-specific classes.
    """
    return DefaultTenantManager()