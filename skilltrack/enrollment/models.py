"""Part 3 - Employee enrollment: enrollments, notifications and badges."""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Enrollment(models.Model):
    """An employee's enrollment in a module: progress, assessment score and optional deadline (FR-05, FR-06)."""

    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Enrolled"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    # The Module model belongs to the modules app (Part 2)
    module = models.ForeignKey("modules.Module", on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    progress = models.PositiveSmallIntegerField(default=0)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_made",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-enrolled_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "module"], name="unique_enrollment_per_module"
            ),
        ]

    def __str__(self):
        return f"{self.employee} - {self.module}"

    @property
    def is_overdue(self):
        return (
            bool(self.due_date)
            and self.status != Enrollment.Status.COMPLETED
            and self.due_date < timezone.localdate()
        )


class Notification(models.Model):
    """In-app notification (and email) for assignments, deadlines and completion (FR-08, FR-09)."""

    class Kind(models.TextChoices):
        ASSIGNED = "ASSIGNED", "New assignment"
        DUE_SOON = "DUE_SOON", "Due soon"
        OVERDUE = "OVERDUE", "Overdue"
        COMPLETED = "COMPLETED", "Completed"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    message = models.CharField(max_length=255)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} for {self.recipient}"


class UserBadge(models.Model):
    """A badge an employee has earned. Each badge is stored only once per user (FR-10)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges"
    )
    code = models.CharField(max_length=50)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["awarded_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "code"], name="unique_badge_per_user"),
        ]

    def __str__(self):
        return f"{self.code} for {self.user}"
