"""Part 1 - Authentication and role-based authorization."""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Role, department and job role of a user. Created automatically for every user."""

    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Employee"
        MANAGER = "MANAGER", "Manager"
        HR = "HR", "HR / Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    department = models.CharField(max_length=100, blank=True)
    job_role = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user} ({self.get_role_display()})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, **kwargs):
    """Every user gets a profile automatically, including users created in the admin."""
    role = UserProfile.Role.HR if instance.is_superuser else UserProfile.Role.EMPLOYEE
    UserProfile.objects.get_or_create(user=instance, defaults={"role": role})
