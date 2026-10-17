"""Part 3 - Forms for assignment, progress and assessment."""
from django import forms

from modules.models import Module


class AssignForm(forms.Form):
    """Manager or HR assigns a module to employees by department and optional job role (FR-04)."""

    module = forms.ModelChoiceField(queryset=Module.objects.all())
    department = forms.CharField(
        label="Department",
        max_length=100,
        required=False,
        help_text="HR: leave blank for all departments. Managers: your own department is used.",
    )
    job_role = forms.CharField(
        label="Job role",
        max_length=100,
        required=False,
        help_text="Optional: only employees with this job role.",
    )
    due_date = forms.DateField(
        label="Due date",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )


class ProgressForm(forms.Form):
    progress = forms.IntegerField(min_value=0, max_value=100, label="Progress (%)")
    minutes = forms.IntegerField(
        min_value=0, max_value=600, initial=0, required=False, label="Minutes spent now"
    )


class AssessmentForm(forms.Form):
    score = forms.IntegerField(min_value=0, max_value=100, label="Assessment score (out of 100)")
