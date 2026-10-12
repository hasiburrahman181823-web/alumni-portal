"""Reusable access-control helpers (class-based mixins and a function decorator)."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from .models import User


class _DenyWithMessageMixin:
    """Logged-in users who fail the check get a friendly message, anonymous users go to login."""

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to do that.")
            return redirect("home")
        return super().handle_no_permission()


class RoleRequiredMixin(_DenyWithMessageMixin, LoginRequiredMixin, UserPassesTestMixin):
    """Set `allowed_roles` on the view to restrict it to those roles."""

    allowed_roles: tuple = ()

    def test_func(self):
        return self.request.user.role in self.allowed_roles


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = (User.Role.ADMIN, User.Role.STAFF)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = (User.Role.ADMIN,)


class OwnerOrStaffMixin(_DenyWithMessageMixin, LoginRequiredMixin, UserPassesTestMixin):
    """Object owner, Staff and Admins may proceed. `owner_field` names the FK to User."""

    owner_field = "posted_by"

    def test_func(self):
        obj = self.get_object()  # cheap; Django caches nothing, but this is one primary-key lookup
        user = self.request.user
        return user.can_manage_content or getattr(obj, self.owner_field + "_id") == user.id


def role_required(*roles):
    """Decorator for function-based views: @role_required(User.Role.ADMIN)."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to do that.")
                return redirect("home")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
