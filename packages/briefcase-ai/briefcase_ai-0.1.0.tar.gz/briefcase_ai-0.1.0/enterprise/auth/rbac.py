"""
Role-Based Access Control (RBAC) Implementation

Provides fine-grained permissions and role management for enterprise deployments.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from enum import Enum


class Permission(Enum):
    """System permissions for RBAC"""

    # Snapshot permissions
    SNAPSHOT_READ = "snapshot:read"
    SNAPSHOT_WRITE = "snapshot:write"
    SNAPSHOT_DELETE = "snapshot:delete"

    # Replay permissions
    REPLAY_READ = "replay:read"
    REPLAY_EXECUTE = "replay:execute"
    REPLAY_DELETE = "replay:delete"

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"

    # Compliance
    AUDIT_READ = "audit:read"
    COMPLIANCE_READ = "compliance:read"


class Role:
    """Represents a role with associated permissions"""

    def __init__(self, name: str, permissions: Set[Permission], description: str = ""):
        self.name = name
        self.permissions = permissions
        self.description = description

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions


# Predefined roles
ROLES = {
    "viewer": Role(
        "viewer",
        {Permission.SNAPSHOT_READ, Permission.REPLAY_READ},
        "Read-only access to snapshots and replays"
    ),
    "developer": Role(
        "developer",
        {
            Permission.SNAPSHOT_READ, Permission.SNAPSHOT_WRITE,
            Permission.REPLAY_READ, Permission.REPLAY_EXECUTE
        },
        "Development access with snapshot and replay capabilities"
    ),
    "admin": Role(
        "admin",
        set(Permission),  # All permissions
        "Full administrative access"
    ),
    "compliance_officer": Role(
        "compliance_officer",
        {Permission.AUDIT_READ, Permission.COMPLIANCE_READ, Permission.SNAPSHOT_READ},
        "Compliance and audit access"
    )
}


class RBACProvider(ABC):
    """
    Abstract base class for RBAC providers.

    This interface allows OSS core to check permissions without depending
    on enterprise implementation details.
    """

    @abstractmethod
    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        pass

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[str]:
        """Get roles assigned to user"""
        pass

    @abstractmethod
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        pass

    @abstractmethod
    async def revoke_role(self, user_id: str, role_name: str) -> bool:
        """Revoke role from user"""
        pass


class DefaultRBACProvider(RBACProvider):
    """
    Default RBAC implementation for enterprise deployments
    """

    def __init__(self):
        # In-memory storage for demo purposes
        # Production implementation would use database
        self.user_roles: Dict[str, Set[str]] = {}
        self.roles = ROLES

    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_roles = self.user_roles.get(user_id, set())

        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and role.has_permission(permission):
                return True

        return False

    async def get_user_roles(self, user_id: str) -> List[str]:
        """Get roles assigned to user"""
        return list(self.user_roles.get(user_id, set()))

    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        if role_name not in self.roles:
            return False

        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()

        self.user_roles[user_id].add(role_name)
        return True

    async def revoke_role(self, user_id: str, role_name: str) -> bool:
        """Revoke role from user"""
        if user_id not in self.user_roles:
            return False

        self.user_roles[user_id].discard(role_name)
        return True

    def get_available_roles(self) -> Dict[str, Role]:
        """Get all available roles"""
        return self.roles.copy()


# Factory function for OSS integration
def create_rbac_provider() -> RBACProvider:
    """
    Factory function to create RBAC provider.

    This function can be called by OSS core to get an RBAC provider
    without importing enterprise-specific classes.
    """
    return DefaultRBACProvider()