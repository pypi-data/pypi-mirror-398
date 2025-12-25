"""
Enterprise Hosted Infrastructure

This module provides managed service hooks and infrastructure for
cloud-hosted Briefcase deployments.
"""

from .replay_service import HostedReplayService, ReplayInfrastructure
from .scaling import AutoScaler, ScalingPolicy
from .tenant import TenantManager, Tenant

__all__ = [
    "HostedReplayService",
    "ReplayInfrastructure",
    "AutoScaler",
    "ScalingPolicy",
    "TenantManager",
    "Tenant"
]