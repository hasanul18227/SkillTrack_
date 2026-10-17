"""Part 1 - Values used by the navigation bar on every page."""
from .permissions import can_manage_team, is_hr


def skilltrack(request):
    user = request.user
    if not user.is_authenticated:
        return {"unread_count": 0, "is_hr": False, "can_manage_team": False}
    return {
        # Notifications are defined in the enrollment app (Part 3)
        "unread_count": user.notifications.filter(is_read=False).count(),
        "is_hr": is_hr(user),
        "can_manage_team": can_manage_team(user),
    }
