"""Part 1 - Home page, registration, profile and the role-based dashboard router."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from enrollment.views import employee_dashboard, manager_dashboard
from modules.models import Module
from modules.views import hr_dashboard

from .forms import ProfileForm, RegistrationForm
from .models import UserProfile
from .permissions import get_profile, get_role, is_hr


def home(request):
    return render(request, "home.html", {"module_count": Module.objects.count()})


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account is ready.")
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "form_page.html", {
        "form": form,
        "title": "Create an account",
        "submit_label": "Register",
        "intro": "Choose your role carefully. Manager and HR roles can see team data and assign modules.",
    })


@login_required
def profile(request):
    user = request.user
    prof = get_profile(user)
    if request.method == "POST":
        form = ProfileForm(request.POST, user=user)
        if form.is_valid():
            data = form.cleaned_data
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.email = data["email"]
            user.save()
            prof.department = data["department"].strip()
            prof.job_role = data["job_role"].strip()
            prof.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = ProfileForm(user=user, initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "department": prof.department,
            "job_role": prof.job_role,
        })
    return render(request, "form_page.html", {
        "form": form,
        "title": "My profile",
        "submit_label": "Save profile",
        "intro": f"Role: {prof.get_role_display()}. Only HR can change the role.",
    })


@login_required
def dashboard(request):
    """One URL, three pages: HR, Manager and Employee each see their own dashboard.

    The three page functions live in the owner apps (modules = HR, enrollment = Manager and Employee).
    """
    user = request.user
    if is_hr(user):
        return hr_dashboard(request)
    if get_role(user) == UserProfile.Role.MANAGER:
        return manager_dashboard(request)
    return employee_dashboard(request)
