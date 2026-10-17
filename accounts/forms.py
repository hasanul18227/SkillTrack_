"""Part 1 - Registration and profile forms."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile

User = get_user_model()


class RegistrationForm(UserCreationForm):
    """Sign-up form: name, email, username, role, department, job role and password (FR-01)."""

    first_name = forms.CharField(label="First name", max_length=150)
    last_name = forms.CharField(label="Last name", max_length=150, required=False)
    email = forms.EmailField(label="Email")
    role = forms.ChoiceField(
        label="Role", choices=UserProfile.Role.choices, initial=UserProfile.Role.EMPLOYEE
    )
    department = forms.CharField(label="Department", max_length=100)
    job_role = forms.CharField(label="Job role", max_length=100)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=True)
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": self.cleaned_data["role"],
                "department": self.cleaned_data["department"].strip(),
                "job_role": self.cleaned_data["job_role"].strip(),
            },
        )
        return user


class ProfileForm(forms.Form):
    """Edit own name, email, department and job role. The role is not editable here."""

    first_name = forms.CharField(label="First name", max_length=150)
    last_name = forms.CharField(label="Last name", max_length=150, required=False)
    email = forms.EmailField(label="Email")
    department = forms.CharField(label="Department", max_length=100)
    job_role = forms.CharField(label="Job role", max_length=100)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email
