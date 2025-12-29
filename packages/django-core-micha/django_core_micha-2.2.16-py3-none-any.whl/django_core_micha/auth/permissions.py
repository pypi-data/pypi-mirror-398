from django.conf import settings
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django_core_micha.auth.security import get_security_level, is_level_sufficient
from django_core_micha.auth.roles import (
    get_role_level_for_user,
    ROLE_LEVEL_0,
    ROLE_LEVEL_2,
    ROLE_LEVEL_3,
)

# --- Internal Helper ---

def _has_min_level(user, setting_name: str, default_level: int) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True

    min_level = getattr(settings, setting_name, default_level)
    user_level = get_role_level_for_user(user)
    return user_level >= int(min_level)


# --- Public Logic Functions (kept for backward compatibility) ---

def has_invite_admin_rights(user) -> bool:
    return _has_min_level(user, "INVITE_MIN_ROLE_LEVEL", ROLE_LEVEL_2)


def has_access_code_admin_rights(user) -> bool:
    return _has_min_level(user, "ACCESS_CODE_MIN_ROLE_LEVEL", ROLE_LEVEL_2)


def can_manage_support_agents(user) -> bool:
    """
    Central helper: who may manage / assign support agents.
    Configured via SUPPORT_ASSIGN_ROLE_LEVEL.
    """
    return _has_min_level(user, "SUPPORT_ASSIGN_ROLE_LEVEL", ROLE_LEVEL_3)


def can_assign_support_contact(user) -> bool:
    """
    Backwards-compatible alias – old name, same semantics.
    """
    return can_manage_support_agents(user)


# --- DRF Permission Classes ---

class MinRoleLevelPermission(BasePermission):
    """
    Base class for view-specific overrides.
    Usage:
        class IsManager(MinRoleLevelPermission):
            min_level = ROLE_LEVEL_2
    """
    min_level = ROLE_LEVEL_0

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Superuser check is usually implicit, but good to be explicit
        if getattr(user, "is_superuser", False):
            return True
        return get_role_level_for_user(user) >= int(self.min_level)


class IsInviteAdminOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return has_invite_admin_rights(getattr(request, "user", None))


class IsAccessCodeAdminOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return has_access_code_admin_rights(getattr(request, "user", None))


class IsAssignedSupportOrAdmin(BasePermission):
    """
    Checks if the user has rights to manage support agents / recovery.
    """
    def has_object_permission(self, request, view, obj):
        return can_manage_support_agents(request.user)
    
    def has_permission(self, request, view):
        return can_manage_support_agents(request.user)


class IsSupportAgent(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        
        profile = getattr(user, "profile", None)
        return bool(getattr(profile, "is_support_agent", False))


class RequireStrongSecurity(BasePermission):
    """
    Authority on Security Levels.
    """
    required_level = "strong"

    def has_permission(self, request, view):
        # 1. Check current level
        current = get_security_level(request)
        
        # 2. Check sufficiency
        is_sufficient = is_level_sufficient(current, self.required_level)
        
        # 3. Check enforcement setting
        if getattr(settings, "SECURITY_ENFORCE_STRONG_AUTH", False):
            return is_sufficient
            
        # If enforcement is off, we allow access (but maybe logged elsewhere)
        return True