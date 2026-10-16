"""Part 2 - Forms for module management and feedback."""
from django import forms

from .models import Feedback, Module


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["title", "description", "category", "skill_tags", "level", "points"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }
