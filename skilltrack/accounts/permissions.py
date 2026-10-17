"""Part 1 - Role checks used by all apps (role-based authorization)."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import UserProfile

ROLE = UserProfile.Role


def get_profile(user):
    """Return the user's profile, creating it if it is missing."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_role(user):
    return get_profile(user).role


def is_hr(user):
    """HR means the HR role, or a Django superuser."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or get_role(user) == ROLE.HR


def can_manage_team(user):
    """Managers and HR can see team progress and assign modules."""
    if not user.is_authenticated:
        return False
    return is_hr(user) or get_role(user) == ROLE.MANAGER


def require(predicate):
    """View decorator: user must be logged in and pass the predicate, otherwise 403."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not predicate(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return login_required(wrapper)

    return decorator
