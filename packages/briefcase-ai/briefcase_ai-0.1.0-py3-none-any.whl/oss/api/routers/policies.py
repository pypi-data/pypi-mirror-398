"""
Policies API Router

REST endpoints for managing observability and compliance policies.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator

from ..auth import User, get_current_user
from ..websocket import websocket_manager

router = APIRouter()

class PolicyType(str, Enum):
    """Policy type enumeration."""
    SNAPSHOT_RETENTION = "snapshot_retention"
    REPLAY_FREQUENCY = "replay_frequency"
    DATA_COMPLIANCE = "data_compliance"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    SECURITY_AUDIT = "security_audit"

class PolicyStatus(str, Enum):
    """Policy status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

class PolicyCondition(BaseModel):
    """Policy condition model."""
    field: str = Field(..., description="Field to evaluate")
    operator: str = Field(..., description="Comparison operator (eq, gt, lt, contains, etc.)")
    value: Union[str, int, float, bool] = Field(..., description="Value to compare against")

class PolicyAction(BaseModel):
    """Policy action model."""
    type: str = Field(..., description="Action type (alert, delete, archive, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")

class PolicyCreate(BaseModel):
    """Request model for creating a policy."""
    name: str = Field(..., description="Human-readable policy name")
    description: Optional[str] = Field(None, description="Policy description")
    type: PolicyType = Field(..., description="Policy type")
    conditions: List[PolicyCondition] = Field(..., description="Policy conditions")
    actions: List[PolicyAction] = Field(..., description="Actions to take when policy matches")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    priority: int = Field(1, ge=1, le=10, description="Policy priority (1=lowest, 10=highest)")

class PolicyUpdate(BaseModel):
    """Request model for updating a policy."""
    name: Optional[str] = Field(None, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    conditions: Optional[List[PolicyCondition]] = Field(None, description="Updated conditions")
    actions: Optional[List[PolicyAction]] = Field(None, description="Updated actions")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Updated priority")
    status: Optional[PolicyStatus] = Field(None, description="Updated status")

class Policy(BaseModel):
    """Policy model."""
    id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Description")
    type: PolicyType = Field(..., description="Policy type")
    conditions: List[PolicyCondition] = Field(..., description="Conditions")
    actions: List[PolicyAction] = Field(..., description="Actions")
    tags: List[str] = Field(default_factory=list, description="Tags")
    priority: int = Field(..., description="Priority")
    status: PolicyStatus = Field(..., description="Status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="Creator username")
    last_executed: Optional[datetime] = Field(None, description="Last execution timestamp")
    execution_count: int = Field(0, description="Number of times executed")

class PolicyViolation(BaseModel):
    """Policy violation model."""
    id: str = Field(..., description="Violation ID")
    policy_id: str = Field(..., description="Policy ID that was violated")
    timestamp: datetime = Field(..., description="Violation timestamp")
    resource_type: str = Field(..., description="Type of resource that violated policy")
    resource_id: str = Field(..., description="ID of resource that violated policy")
    details: Dict[str, Any] = Field(..., description="Violation details")
    severity: str = Field(..., description="Violation severity (low, medium, high, critical)")
    resolved: bool = Field(False, description="Whether violation has been resolved")

# In-memory storage (replace with database in production)
policies_db: Dict[str, Policy] = {}
violations_db: Dict[str, PolicyViolation] = {}

@router.get("/", response_model=List[Policy])
async def list_policies(
    skip: int = Query(0, ge=0, description="Number of policies to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of policies to return"),
    type: Optional[PolicyType] = Query(None, description="Filter by policy type"),
    status: Optional[PolicyStatus] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    current_user: User = Depends(get_current_user)
):
    """
    List all policies with optional filtering and pagination.
    """
    policies_list = list(policies_db.values())

    # Filter by type
    if type:
        policies_list = [p for p in policies_list if p.type == type]

    # Filter by status
    if status:
        policies_list = [p for p in policies_list if p.status == status]

    # Filter by tags
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        policies_list = [
            p for p in policies_list
            if any(tag in p.tags for tag in tag_list)
        ]

    # Sort by priority (highest first), then by creation date
    policies_list.sort(key=lambda x: (-x.priority, x.created_at))

    # Apply pagination
    return policies_list[skip:skip + limit]

@router.get("/{policy_id}", response_model=Policy)
async def get_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific policy by ID.
    """
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")

    return policies_db[policy_id]

@router.post("/", response_model=Policy, status_code=201)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new policy.
    """
    policy_id = str(uuid4())

    policy = Policy(
        id=policy_id,
        name=policy_data.name,
        description=policy_data.description,
        type=policy_data.type,
        conditions=policy_data.conditions,
        actions=policy_data.actions,
        tags=policy_data.tags,
        priority=policy_data.priority,
        status=PolicyStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        created_by=current_user.username
    )

    policies_db[policy_id] = policy

    return policy

@router.put("/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: str,
    policy_update: PolicyUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing policy.
    """
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = policies_db[policy_id]

    # Update only provided fields
    if policy_update.name is not None:
        policy.name = policy_update.name
    if policy_update.description is not None:
        policy.description = policy_update.description
    if policy_update.conditions is not None:
        policy.conditions = policy_update.conditions
    if policy_update.actions is not None:
        policy.actions = policy_update.actions
    if policy_update.tags is not None:
        policy.tags = policy_update.tags
    if policy_update.priority is not None:
        policy.priority = policy_update.priority
    if policy_update.status is not None:
        policy.status = policy_update.status

    policy.updated_at = datetime.now()
    policies_db[policy_id] = policy

    return policy

@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a policy.
    """
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")

    del policies_db[policy_id]

@router.post("/{policy_id}/execute")
async def execute_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Manually execute a policy.
    """
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = policies_db[policy_id]

    if policy.status != PolicyStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute policy with status: {policy.status}"
        )

    # Update execution tracking
    policy.last_executed = datetime.now()
    policy.execution_count += 1
    policies_db[policy_id] = policy

    # In real implementation, this would execute the policy logic
    execution_results = {
        "policy_id": policy_id,
        "executed_at": policy.last_executed.isoformat(),
        "conditions_evaluated": len(policy.conditions),
        "actions_triggered": 0,  # Would be actual count
        "violations_found": 0  # Would be actual count
    }

    return execution_results

@router.get("/{policy_id}/violations", response_model=List[PolicyViolation])
async def get_policy_violations(
    policy_id: str,
    skip: int = Query(0, ge=0, description="Number of violations to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of violations to return"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    current_user: User = Depends(get_current_user)
):
    """
    Get violations for a specific policy.
    """
    if policy_id not in policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Filter violations by policy ID
    policy_violations = [
        v for v in violations_db.values()
        if v.policy_id == policy_id
    ]

    # Filter by resolution status
    if resolved is not None:
        policy_violations = [v for v in policy_violations if v.resolved == resolved]

    # Sort by timestamp (newest first)
    policy_violations.sort(key=lambda x: x.timestamp, reverse=True)

    # Apply pagination
    return policy_violations[skip:skip + limit]

@router.get("/violations/", response_model=List[PolicyViolation])
async def list_all_violations(
    skip: int = Query(0, ge=0, description="Number of violations to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of violations to return"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    current_user: User = Depends(get_current_user)
):
    """
    List all policy violations across all policies.
    """
    violations_list = list(violations_db.values())

    # Filter by severity
    if severity:
        violations_list = [v for v in violations_list if v.severity == severity]

    # Filter by resolution status
    if resolved is not None:
        violations_list = [v for v in violations_list if v.resolved == resolved]

    # Sort by timestamp (newest first)
    violations_list.sort(key=lambda x: x.timestamp, reverse=True)

    # Apply pagination
    return violations_list[skip:skip + limit]

@router.post("/violations/{violation_id}/resolve")
async def resolve_violation(
    violation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Mark a policy violation as resolved.
    """
    if violation_id not in violations_db:
        raise HTTPException(status_code=404, detail="Violation not found")

    violation = violations_db[violation_id]
    violation.resolved = True
    violations_db[violation_id] = violation

    return {"message": "Violation marked as resolved", "violation_id": violation_id}

# Utility function to simulate policy violation (for demo)
async def simulate_policy_violation(policy_id: str, resource_type: str, resource_id: str):
    """Simulate a policy violation for demo purposes."""
    violation_id = str(uuid4())

    violation = PolicyViolation(
        id=violation_id,
        policy_id=policy_id,
        timestamp=datetime.now(),
        resource_type=resource_type,
        resource_id=resource_id,
        details={
            "message": f"Policy violation detected for {resource_type} {resource_id}",
            "threshold_exceeded": True
        },
        severity="medium",
        resolved=False
    )

    violations_db[violation_id] = violation

    # Notify via WebSocket
    await websocket_manager.notify_policy_violation(
        policy_id,
        {
            "violation_id": violation_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "severity": violation.severity
        }
    )