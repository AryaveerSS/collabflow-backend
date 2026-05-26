"""
app/core/permissions.py

Role-Based Access Control (RBAC) system for CollabFlow.

Roles (highest to lowest):
    OWNER   → full control, can delete workspace, transfer ownership
    ADMIN   → manage members, projects, tasks
    MEMBER  → create and manage own tasks, comment
    VIEWER  → read-only access

Usage in routes:
    from app.core.permissions import require_role, RoleChecker

    # Allow only admins and owners:
    @router.delete("/{id}", dependencies=[Depends(require_role(["owner", "admin"]))])

    # Or use in service layer:
    check_permission(current_user_role, required_role="admin")
"""

from enum import Enum
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_handler import verify_access_token


# ================================
# Role Definitions
# ================================

class Role(str, Enum):
    """
    All possible roles in the system.
    Inherits from str so it works seamlessly with Pydantic and JSON.
    """
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# Role hierarchy — higher index = more permissions
ROLE_HIERARCHY = [
    Role.VIEWER,
    Role.MEMBER,
    Role.ADMIN,
    Role.OWNER,
]


# ================================
# Role Comparison Utilities
# ================================

def get_role_level(role: str) -> int:
    """
    Returns the numeric level of a role.
    Higher number = more permissions.

    Example:
        get_role_level("owner")  → 3
        get_role_level("viewer") → 0
    """
    try:
        return ROLE_HIERARCHY.index(Role(role))
    except ValueError:
        return -1


def has_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user_role meets or exceeds required_role level.

    Example:
        has_permission("admin", "member")  → True  (admin > member)
        has_permission("viewer", "admin")  → False (viewer < admin)
        has_permission("owner", "owner")   → True  (same level)
    """
    return get_role_level(user_role) >= get_role_level(required_role)


def check_permission(user_role: str, required_role: str) -> None:
    """
    Raises HTTPException 403 if user doesn't have required permission.
    Use this in service layer checks.

    Example:
        check_permission(current_user.role, "admin")
    """
    if not has_permission(user_role, required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: '{required_role}', your role: '{user_role}'.",
        )


# ================================
# Current User Extraction
# ================================

# Bearer token security scheme
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency to extract and validate the current user from JWT.

    Returns the decoded token payload as a dict:
    {
        "sub": "user_id",
        "email": "user@example.com",
        "role": "member",
        "jti": "...",
        ...
    }

    Usage in routes:
        @router.get("/me")
        async def get_me(current_user: dict = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_id(
    current_user: dict = Depends(get_current_user),
) -> str:
    """
    Shortcut dependency — returns only the user_id string.

    Usage:
        @router.get("/tasks")
        async def get_tasks(user_id: str = Depends(get_current_user_id)):
            ...
    """
    return current_user["sub"]


# ================================
# Role-Based Route Guards
# ================================

class RoleChecker:
    """
    FastAPI dependency class for role-based route protection.

    Usage:
        # Protect a route — only owner or admin can access:
        @router.delete(
            "/{workspace_id}",
            dependencies=[Depends(RoleChecker(["owner", "admin"]))]
        )
        async def delete_workspace(...):
            ...
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [role.lower() for role in allowed_roles]

    async def __call__(
        self,
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_role = current_user.get("role", "viewer")

        if user_role not in self.allowed_roles:
            # Also allow higher roles
            if not any(has_permission(user_role, r) for r in self.allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Allowed roles: {self.allowed_roles}.",
                )

        return current_user


def require_role(allowed_roles: List[str]):
    """
    Shortcut function for RoleChecker.
    Use as a route dependency.

    Usage:
        @router.post("/invite", dependencies=[Depends(require_role(["owner", "admin"]))])
    """
    return RoleChecker(allowed_roles)


# ================================
# Permission Constants
# ================================

# Predefined permission sets for common operations
class Permissions:
    """
    Centralized permission definitions.
    Use these instead of hardcoding role strings everywhere.
    """

    # Workspace permissions
    WORKSPACE_DELETE    = ["owner"]
    WORKSPACE_SETTINGS  = ["owner", "admin"]
    WORKSPACE_INVITE    = ["owner", "admin"]
    WORKSPACE_VIEW      = ["owner", "admin", "member", "viewer"]

    # Project permissions
    PROJECT_CREATE      = ["owner", "admin", "member"]
    PROJECT_UPDATE      = ["owner", "admin"]
    PROJECT_DELETE      = ["owner", "admin"]
    PROJECT_VIEW        = ["owner", "admin", "member", "viewer"]
    PROJECT_ARCHIVE     = ["owner", "admin"]

    # Task permissions
    TASK_CREATE         = ["owner", "admin", "member"]
    TASK_UPDATE         = ["owner", "admin", "member"]
    TASK_DELETE         = ["owner", "admin"]
    TASK_VIEW           = ["owner", "admin", "member", "viewer"]
    TASK_ASSIGN         = ["owner", "admin"]

    # Comment permissions
    COMMENT_CREATE      = ["owner", "admin", "member"]
    COMMENT_DELETE_OWN  = ["owner", "admin", "member"]
    COMMENT_DELETE_ANY  = ["owner", "admin"]

    # Member management
    MEMBER_MANAGE       = ["owner", "admin"]
    MEMBER_REMOVE       = ["owner"]
    ROLE_ASSIGN         = ["owner"]