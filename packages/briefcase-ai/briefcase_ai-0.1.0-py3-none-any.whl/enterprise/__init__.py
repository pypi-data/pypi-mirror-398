"""
Briefcase Enterprise Extensions

This package contains enterprise-only features that extend the OSS core.
Enterprise features are optional and the OSS core must remain fully functional
without any enterprise dependencies.

Key Enterprise Features:
- RBAC (Role-Based Access Control)
- SSO (Single Sign-On) with SAML
- Compliance reporting
- Hosted replay infrastructure
- Advanced analytics

The enterprise package follows the extension pattern where:
1. OSS defines interfaces and extension points
2. Enterprise implements concrete extensions
3. Clean boundary maintained via dependency injection
"""

__version__ = "0.1.0"

# Enterprise feature flags - can be used by OSS to check availability
ENTERPRISE_FEATURES = {
    "rbac": True,
    "sso": True,
    "compliance": True,
    "hosted_replay": True,
    "advanced_analytics": True,
    "multi_tenant": True,
    "auto_scaling": True,
}


def get_enterprise_features():
    """
    Return available enterprise features.
    Used by OSS core to discover enterprise capabilities.
    """
    return ENTERPRISE_FEATURES


def is_enterprise_available():
    """
    Check if enterprise extensions are available.
    Used by OSS core to determine if enterprise features can be enabled.
    """
    return True