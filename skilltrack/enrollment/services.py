"""Part 3 - Business rules: enrollment, progress, assessment, assignment, notifications,
deadlines, milestones, points and badges.

Keeping these rules here (not in the views) makes them easy to explain in the report.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from accounts.models import UserProfile
from modules.models import Module

from .models import Enrollment, Notification, UserBadge

User = get_user_model()

COMPLETED = Enrollment.Status.COMPLETED
PASS_MARK = 60  # assessment score (out of 100) needed to complete a module
TOP_SCORE = 90  # score that unlocks the Top Scorer badge
CONSISTENT_COUNT = 5  # completed modules needed for Consistent Learner
DUE_SOON_DAYS = 3  # warn the employee this many days before the deadline

BADGES = {
    "FIRST_STEP": {"name": "First Step", "description": "Completed your first module.", "bonus": 10},
    "CONSISTENT_LEARNER": {"name": "Consistent Learner", "description": "Completed 5 modules.", "bonus": 25},
    "TOP_SCORER": {"name": "Top Scorer", "description": "Scored 90 or more in an assessment.", "bonus": 20},
    "BEGINNER_MILESTONE": {"name": "Beginner Milestone", "description": "Completed every Beginner module.", "bonus": 50},
    "INTERMEDIATE_MILESTONE": {"name": "Intermediate Milestone", "description": "Completed every Intermediate module.", "bonus": 75},
    "ADVANCED_MILESTONE": {"name": "Advanced Milestone", "description": "Completed every Advanced module.", "bonus": 100},
}

MILESTONE_BADGE = {
    "BEGINNER": "BEGINNER_MILESTONE",
    "INTERMEDIATE": "INTERMEDIATE_MILESTONE",
    "ADVANCED": "ADVANCED_MILESTONE",
}


# ----- Notifications -----

def _notify_once(recipient, kind, enrollment, message):
    """Create a notification and send an email, unless this recipient already got this kind for this enrollment."""
    if Notification.objects.filter(recipient=recipient, kind=kind, enrollment=enrollment).exists():
        return False
    message = message[:255]
    Notification.objects.create(recipient=recipient, kind=kind, enrollment=enrollment, message=message)
    if recipient.email:
        send_mail(
            subject=f"SkillTrack: {next(label for value, label in Notification.Kind.choices if value == kind)}",
            message=message,
            from_email=None,
            recipient_list=[recipient.email],
            fail_silently=True,
        )
    return True


def managers_of(employee):
    """Managers in the same department as the employee."""
    profile, _ = UserProfile.objects.get_or_create(user=employee)
    if not profile.department:
        return []
    return list(
        User.objects.filter(
            is_active=True,
            profile__role=UserProfile.Role.MANAGER,
            profile__department__iexact=profile.department,
        )
    )


# ----- Enrollment and progress (FR-05, FR-06) -----

def enroll(user, module):
    """Enroll the user in a module. Returns (enrollment, created)."""
    return Enrollment.objects.get_or_create(employee=user, module=module)


def record_progress(enrollment, progress, minutes):
    """Save progress % and extra time spent. Completing a module still needs a passing assessment."""
    enrollment.progress = progress
    enrollment.time_spent_minutes += minutes
    enrollment.status = (
        Enrollment.Status.IN_PROGRESS if progress > 0 else Enrollment.Status.ENROLLED
    )
    enrollment.save(update_fields=["progress", "time_spent_minutes", "status"])


@transaction.atomic
def submit_assessment(enrollment, score):
    """Store the score. A passing score completes the module. Returns (passed, new_badge_codes)."""
    enrollment.score = score
    if score < PASS_MARK:
        enrollment.status = Enrollment.Status.IN_PROGRESS
        enrollment.save(update_fields=["score", "status"])
        return False, []

    enrollment.status = COMPLETED
    enrollment.progress = 100
    enrollment.completed_at = timezone.now()
    enrollment.save()
    _notify_once(
        enrollment.employee,
        Notification.Kind.COMPLETED,
        enrollment,
        f"You completed '{enrollment.module.title}' with {score}/100.",
    )
    return True, award_badges(enrollment.employee)


# ----- Assignments (FR-04) -----

def find_employees(department="", job_role=""):
    """Employees (not superusers) matching the department and/or job role. Blank means no filter."""
    employees = User.objects.filter(
        is_active=True,
        is_superuser=False,
        profile__role=UserProfile.Role.EMPLOYEE,
    )
    if department:
        employees = employees.filter(profile__department__iexact=department)
    if job_role:
        employees = employees.filter(profile__job_role__iexact=job_role)
    return list(employees)


def assign_module(module, employees, assigned_by, due_date):
    """Assign a module to employees. Returns (assigned_count, skipped_count).

    Skipped: already assigned to this employee, or already completed. This prevents duplicate assignments.
    """
    assigned = skipped = 0
    for employee in employees:
        enrollment, created = Enrollment.objects.get_or_create(employee=employee, module=module)
        already_assigned = not created and enrollment.assigned_by_id is not None
        if enrollment.status == COMPLETED or already_assigned:
            skipped += 1
            continue

        enrollment.assigned_by = assigned_by
        enrollment.due_date = due_date
        enrollment.save(update_fields=["assigned_by", "due_date"])

        due_text = f" Due: {due_date:%d %b %Y}." if due_date else ""
        _notify_once(
            employee,
            Notification.Kind.ASSIGNED,
            enrollment,
            f"You were assigned '{module.title}'.{due_text}",
        )
        assigned += 1
    return assigned, skipped


# ----- Deadlines and overdue reminders (FR-09) -----

def check_deadlines():
    """Create due-soon and overdue notifications. Employees and their managers are notified about overdue items.

    Run daily with: python manage.py check_deadlines
    Returns a dict with the number of new notifications created.
    """
    today = timezone.localdate()
    soon = today + timedelta(days=DUE_SOON_DAYS)
    counts = {"due_soon": 0, "overdue": 0}

    open_items = (
        Enrollment.objects.filter(due_date__isnull=False)
        .exclude(status=COMPLETED)
        .select_related("employee", "module")
    )
    for item in open_items:
        title = item.module.title
        if item.due_date < today:
            if _notify_once(
                item.employee,
                Notification.Kind.OVERDUE,
                item,
                f"'{title}' was due on {item.due_date:%d %b %Y} and is now overdue.",
            ):
                counts["overdue"] += 1

            employee_name = item.employee.get_full_name() or item.employee.username
            for manager in managers_of(item.employee):
                if _notify_once(
                    manager,
                    Notification.Kind.OVERDUE,
                    item,
                    f"{employee_name} has an overdue module: '{title}'.",
                ):
                    counts["overdue"] += 1

        elif item.due_date <= soon:
            if _notify_once(
                item.employee,
                Notification.Kind.DUE_SOON,
                item,
                f"'{title}' is due on {item.due_date:%d %b %Y}.",
            ):
                counts["due_soon"] += 1
    return counts


# ----- Learning milestones (Beginner -> Intermediate -> Advanced, FR-07) -----

def milestone_progress(user):
    """Progress of the user through each level that has modules in the catalog."""
    milestones = []
    for level, label in Module.Level.choices:
        total = Module.objects.filter(level=level).count()
        done = Enrollment.objects.filter(
            employee=user, status=COMPLETED, module__level=level
        ).count()
        milestones.append({
            "level": level,
            "label": label,
            "total": total,
            "done": done,
            "percent": round(done * 100 / total) if total else 0,
            "complete": total > 0 and done >= total,
        })
    return milestones


def current_milestone(milestones):
    """First milestone that has modules but is not finished yet, or None if all are done."""
    for milestone in milestones:
        if milestone["total"] and not milestone["complete"]:
            return milestone
    return None


def recommended_modules(user, milestone, limit=4):
    """Modules at the user's current level that they have not started yet."""
    if milestone is None:
        return Module.objects.none()
    started = Enrollment.objects.filter(employee=user).values_list("module_id", flat=True)
    return Module.objects.filter(level=milestone["level"]).exclude(pk__in=started)[:limit]


# ----- Points and badges (FR-10) -----

def eligible_badge_codes(user):
    """Every badge code the user currently qualifies for."""
    completed = Enrollment.objects.filter(employee=user, status=COMPLETED)
    count = completed.count()
    codes = set()
    if count >= 1:
        codes.add("FIRST_STEP")
    if count >= CONSISTENT_COUNT:
        codes.add("CONSISTENT_LEARNER")
    if completed.filter(score__gte=TOP_SCORE).exists():
        codes.add("TOP_SCORER")
    for milestone in milestone_progress(user):
        if milestone["complete"]:
            codes.add(MILESTONE_BADGE[milestone["level"]])
    return codes


def award_badges(user):
    """Award only the badges the user does not have yet, so nothing is awarded twice."""
    owned = set(UserBadge.objects.filter(user=user).values_list("code", flat=True))
    new_codes = sorted(eligible_badge_codes(user) - owned)
    UserBadge.objects.bulk_create(
        [UserBadge(user=user, code=code) for code in new_codes],
        ignore_conflicts=True,
    )
    return new_codes


def user_badges(user):
    """Name and description of each badge the user has earned."""
    return [
        {"name": BADGES[b.code]["name"], "description": BADGES[b.code]["description"]}
        for b in UserBadge.objects.filter(user=user)
        if b.code in BADGES
    ]


def total_points(user):
    """Points from completed modules plus the bonus from earned badges."""
    module_points = (
        Enrollment.objects.filter(employee=user, status=COMPLETED)
        .aggregate(total=Sum("module__points"))["total"]
        or 0
    )
    badge_points = sum(
        BADGES[b.code]["bonus"]
        for b in UserBadge.objects.filter(user=user)
        if b.code in BADGES
    )
    return module_points + badge_points
