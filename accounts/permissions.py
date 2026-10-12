"""DRF permission classes mirroring the role rules used by the web views."""
from rest_framework import permissions


class IsStaffRoleOrReadOnly(permissions.BasePermission):
    """Anyone authenticated can read; only Staff/Admin can write."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method in permissions.SAFE_METHODS or request.user.can_manage_content


class IsOwnerOrStaffOrReadOnly(permissions.BasePermission):
    """Read for everyone; write for the owner, Staff or Admin."""

    owner_field = "posted_by"

    def has_permission(self, request, view):
        # Must be logged in for anything, including reads (otherwise anonymous users slip through).
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.can_manage_content or getattr(obj, self.owner_field + "_id") == request.user.id
