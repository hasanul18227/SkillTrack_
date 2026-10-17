"""Part 2 - Training module management: modules and feedback."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg


class Module(models.Model):
    """A training module created and managed by HR (FR-13)."""

    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    skill_tags = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated, e.g. python, sql"
    )
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    points = models.PositiveIntegerField(default=100, help_text="Points earned on completion")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.skill_tags.split(",") if tag.strip()]

    @property
    def average_rating(self):
        return self.feedback.aggregate(avg=Avg("rating"))["avg"]


class Feedback(models.Model):
    """A rating and comment from an employee who completed the module (FR-12)."""

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="feedback")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "author"], name="one_feedback_per_user_per_module"
            ),
        ]

    def __str__(self):
        return f"{self.rating} stars on {self.module} by {self.author}"
