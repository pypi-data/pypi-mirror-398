"""
Enterprise Extension Points and Hooks

This module defines the interfaces and extension points that allow
OSS core to integrate with enterprise features without creating
hard dependencies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ExtensionType(Enum):
    """Types of enterprise extensions"""
    AUTH = "auth"
    COMPLIANCE = "compliance"
    HOSTED = "hosted"
    ANALYTICS = "analytics"
    BILLING = "billing"


@dataclass
class ExtensionInfo:
    """Information about an available extension"""

    extension_type: ExtensionType
    name: str
    version: str
    description: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class ExtensionRegistry:
    """
    Registry for managing enterprise extensions.

    This allows OSS core to discover and use enterprise features
    without importing them directly.
    """

    def __init__(self):
        self._extensions: Dict[ExtensionType, Dict[str, Any]] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    def register_extension(
        self,
        extension_type: ExtensionType,
        name: str,
        implementation: Any,
        version: str = "1.0.0",
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        """Register an enterprise extension"""
        if extension_type not in self._extensions:
            self._extensions[extension_type] = {}

        self._extensions[extension_type][name] = {
            "implementation": implementation,
            "info": ExtensionInfo(
                extension_type=extension_type,
                name=name,
                version=version,
                description=description,
                config=config
            )
        }

    def get_extension(self, extension_type: ExtensionType, name: str) -> Optional[Any]:
        """Get a registered extension implementation"""
        if extension_type in self._extensions:
            extension_data = self._extensions[extension_type].get(name)
            if extension_data and extension_data["info"].enabled:
                return extension_data["implementation"]
        return None

    def list_extensions(self, extension_type: Optional[ExtensionType] = None) -> List[ExtensionInfo]:
        """List available extensions"""
        extensions = []

        for ext_type, ext_dict in self._extensions.items():
            if extension_type is None or ext_type == extension_type:
                for ext_data in ext_dict.values():
                    extensions.append(ext_data["info"])

        return extensions

    def is_extension_available(self, extension_type: ExtensionType, name: str) -> bool:
        """Check if an extension is available and enabled"""
        extension = self.get_extension(extension_type, name)
        return extension is not None

    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def call_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Call all registered hooks for an event"""
        results = []
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # Log error but don't break the chain
                    print(f"Error in hook {hook_name}: {e}")
        return results

    def enable_extension(self, extension_type: ExtensionType, name: str):
        """Enable an extension"""
        if extension_type in self._extensions:
            extension_data = self._extensions[extension_type].get(name)
            if extension_data:
                extension_data["info"].enabled = True

    def disable_extension(self, extension_type: ExtensionType, name: str):
        """Disable an extension"""
        if extension_type in self._extensions:
            extension_data = self._extensions[extension_type].get(name)
            if extension_data:
                extension_data["info"].enabled = False


# Global extension registry
registry = ExtensionRegistry()


# Hook definitions for OSS integration
class OSSSHooks:
    """
    Defines standard hooks that OSS core can call to integrate
    with enterprise features when available.
    """

    # Authentication hooks
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    PERMISSION_CHECK = "permission.check"

    # Data hooks
    SNAPSHOT_CREATED = "snapshot.created"
    SNAPSHOT_ACCESSED = "snapshot.accessed"
    SNAPSHOT_DELETED = "snapshot.deleted"

    # Replay hooks
    REPLAY_STARTED = "replay.started"
    REPLAY_COMPLETED = "replay.completed"
    REPLAY_FAILED = "replay.failed"

    # System hooks
    SYSTEM_ERROR = "system.error"
    CONFIG_CHANGED = "config.changed"

    # Compliance hooks
    AUDIT_EVENT = "audit.event"
    POLICY_VIOLATION = "policy.violation"


class EnterpriseIntegration:
    """
    Helper class to facilitate OSS-Enterprise integration.

    This provides convenience methods for OSS core to interact
    with enterprise features when available.
    """

    def __init__(self, extension_registry: ExtensionRegistry = None):
        self.registry = extension_registry or registry

    def get_auth_provider(self):
        """Get RBAC provider if available"""
        return self.registry.get_extension(ExtensionType.AUTH, "rbac")

    def get_sso_provider(self):
        """Get SSO provider if available"""
        return self.registry.get_extension(ExtensionType.AUTH, "sso")

    def get_audit_logger(self):
        """Get audit logger if available"""
        return self.registry.get_extension(ExtensionType.COMPLIANCE, "audit")

    def get_compliance_reporter(self):
        """Get compliance reporter if available"""
        return self.registry.get_extension(ExtensionType.COMPLIANCE, "reporting")

    def get_retention_manager(self):
        """Get retention manager if available"""
        return self.registry.get_extension(ExtensionType.COMPLIANCE, "retention")

    def get_hosted_replay_service(self):
        """Get hosted replay service if available"""
        return self.registry.get_extension(ExtensionType.HOSTED, "replay")

    def get_tenant_manager(self):
        """Get tenant manager if available"""
        return self.registry.get_extension(ExtensionType.HOSTED, "tenant")

    def get_auto_scaler(self):
        """Get auto scaler if available"""
        return self.registry.get_extension(ExtensionType.HOSTED, "scaling")

    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check user permission using enterprise RBAC if available"""
        auth_provider = self.get_auth_provider()
        if auth_provider:
            try:
                # Import here to avoid circular dependencies
                from .auth.rbac import Permission
                # Convert string to Permission enum
                perm_enum = Permission(permission)
                return await auth_provider.check_permission(user_id, perm_enum)
            except (ImportError, ValueError, AttributeError):
                pass

        # Fallback to OSS permission checking
        return True  # Default allow for OSS

    async def log_audit_event(self, event_type: str, user_id: str = None, **kwargs):
        """Log audit event if audit logger is available"""
        audit_logger = self.get_audit_logger()
        if audit_logger:
            try:
                # Import here to avoid circular dependencies
                from .compliance.audit import AuditEvent, AuditEventType
                from datetime import datetime

                event = AuditEvent(
                    event_type=AuditEventType(event_type),
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    **kwargs
                )
                await audit_logger.log_event(event)
            except (ImportError, ValueError, AttributeError) as e:
                print(f"Error logging audit event: {e}")

        # Also call audit hooks
        self.registry.call_hooks(OSSSHooks.AUDIT_EVENT, event_type, user_id, **kwargs)

    async def authenticate_sso(self, token: str):
        """Authenticate user with SSO if available"""
        sso_provider = self.get_sso_provider()
        if sso_provider:
            try:
                return await sso_provider.authenticate(token)
            except Exception as e:
                print(f"SSO authentication error: {e}")
        return None

    async def check_tenant_quota(self, tenant_id: str, resource: str) -> bool:
        """Check tenant quota if multi-tenancy is available"""
        tenant_manager = self.get_tenant_manager()
        if tenant_manager:
            try:
                return await tenant_manager.check_quota(tenant_id, resource)
            except Exception as e:
                print(f"Quota check error: {e}")
        return True  # Allow if no tenant management

    def is_enterprise_feature_available(self, feature: str) -> bool:
        """Check if a specific enterprise feature is available"""
        feature_map = {
            "rbac": (ExtensionType.AUTH, "rbac"),
            "sso": (ExtensionType.AUTH, "sso"),
            "audit": (ExtensionType.COMPLIANCE, "audit"),
            "compliance": (ExtensionType.COMPLIANCE, "reporting"),
            "hosted_replay": (ExtensionType.HOSTED, "replay"),
            "multi_tenant": (ExtensionType.HOSTED, "tenant"),
            "auto_scaling": (ExtensionType.HOSTED, "scaling")
        }

        if feature in feature_map:
            ext_type, ext_name = feature_map[feature]
            return self.registry.is_extension_available(ext_type, ext_name)

        return False

    def get_enterprise_features(self) -> Dict[str, bool]:
        """Get status of all enterprise features"""
        return {
            "rbac": self.is_enterprise_feature_available("rbac"),
            "sso": self.is_enterprise_feature_available("sso"),
            "audit": self.is_enterprise_feature_available("audit"),
            "compliance": self.is_enterprise_feature_available("compliance"),
            "hosted_replay": self.is_enterprise_feature_available("hosted_replay"),
            "multi_tenant": self.is_enterprise_feature_available("multi_tenant"),
            "auto_scaling": self.is_enterprise_feature_available("auto_scaling")
        }


# Global integration instance
integration = EnterpriseIntegration()


# Decorator for OSS methods to add enterprise hooks
def with_enterprise_hooks(hook_name: str):
    """
    Decorator to add enterprise hooks to OSS methods.

    Usage:
    @with_enterprise_hooks("snapshot.created")
    def create_snapshot(self, ...):
        # OSS implementation
        pass
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Call pre-hooks
            registry.call_hooks(f"{hook_name}.pre", *args, **kwargs)

            try:
                # Call original function
                result = await func(*args, **kwargs)

                # Call post-hooks with result
                registry.call_hooks(f"{hook_name}.post", result, *args, **kwargs)

                return result
            except Exception as e:
                # Call error hooks
                registry.call_hooks(f"{hook_name}.error", e, *args, **kwargs)
                raise

        def sync_wrapper(*args, **kwargs):
            # Call pre-hooks
            registry.call_hooks(f"{hook_name}.pre", *args, **kwargs)

            try:
                # Call original function
                result = func(*args, **kwargs)

                # Call post-hooks with result
                registry.call_hooks(f"{hook_name}.post", result, *args, **kwargs)

                return result
            except Exception as e:
                # Call error hooks
                registry.call_hooks(f"{hook_name}.error", e, *args, **kwargs)
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Configuration helper
def configure_enterprise_extensions(config: Dict[str, Any]):
    """
    Configure enterprise extensions based on configuration.

    This function should be called during application startup
    to set up available enterprise features.
    """

    # Configure authentication
    if config.get("enterprise", {}).get("auth", {}).get("rbac", {}).get("enabled", False):
        try:
            from .auth.rbac import create_rbac_provider
            rbac_provider = create_rbac_provider()
            registry.register_extension(
                ExtensionType.AUTH,
                "rbac",
                rbac_provider,
                description="Role-Based Access Control"
            )
        except ImportError:
            pass

    if config.get("enterprise", {}).get("auth", {}).get("sso", {}).get("enabled", False):
        try:
            from .auth.sso import create_sso_provider, SSOConfig, SSOProtocol
            sso_config = SSOConfig(
                protocol=SSOProtocol.SAML2,
                provider_url=config["enterprise"]["auth"]["sso"]["provider_url"],
                entity_id=config["enterprise"]["auth"]["sso"]["entity_id"]
            )
            sso_provider = create_sso_provider(sso_config)
            registry.register_extension(
                ExtensionType.AUTH,
                "sso",
                sso_provider,
                description="Single Sign-On with SAML"
            )
        except (ImportError, KeyError):
            pass

    # Configure compliance
    if config.get("enterprise", {}).get("compliance", {}).get("audit", {}).get("enabled", False):
        try:
            from .compliance.audit import create_audit_logger
            audit_logger = create_audit_logger(config["enterprise"]["compliance"]["audit"])
            registry.register_extension(
                ExtensionType.COMPLIANCE,
                "audit",
                audit_logger,
                description="Audit Logging"
            )
        except (ImportError, KeyError):
            pass

    if config.get("enterprise", {}).get("compliance", {}).get("reporting", {}).get("enabled", False):
        try:
            from .compliance.reporting import create_compliance_reporter
            compliance_reporter = create_compliance_reporter()
            registry.register_extension(
                ExtensionType.COMPLIANCE,
                "reporting",
                compliance_reporter,
                description="Compliance Reporting"
            )
        except ImportError:
            pass

    # Configure hosted services
    if config.get("enterprise", {}).get("hosted", {}).get("replay", {}).get("enabled", False):
        try:
            from .hosted.replay_service import create_hosted_replay_service
            replay_service = create_hosted_replay_service(config["enterprise"]["hosted"]["replay"])
            registry.register_extension(
                ExtensionType.HOSTED,
                "replay",
                replay_service,
                description="Hosted Replay Service"
            )
        except (ImportError, KeyError):
            pass

    if config.get("enterprise", {}).get("hosted", {}).get("tenant", {}).get("enabled", False):
        try:
            from .hosted.tenant import create_tenant_manager
            tenant_manager = create_tenant_manager()
            registry.register_extension(
                ExtensionType.HOSTED,
                "tenant",
                tenant_manager,
                description="Multi-tenant Management"
            )
        except ImportError:
            pass


# Export the main integration interface
__all__ = [
    "ExtensionRegistry",
    "EnterpriseIntegration",
    "OSSSHooks",
    "registry",
    "integration",
    "with_enterprise_hooks",
    "configure_enterprise_extensions"
]