"""Part 3 - Employee dashboard, my courses, enrollment, progress, assessment, certificate,
notifications, team progress and assignment."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import UserProfile
from accounts.permissions import can_manage_team, get_profile, is_hr, require
from modules.models import Module

from . import services
from .certificates import build_certificate_pdf
from .forms import AssessmentForm, AssignForm, ProgressForm
from .models import Enrollment

COMPLETED = Enrollment.Status.COMPLETED


# ----- Dashboards (called from accounts.views.dashboard, which already checks login) -----

def employee_dashboard(request):
    """Summary for employees: points, milestones, deadlines, badges and recommendations."""
    user = request.user
    milestones = services.milestone_progress(user)
    current = services.current_milestone(milestones)
    if current:
        stage = current["label"]
    elif any(m["total"] for m in milestones):
        stage = "All milestones completed"
    else:
        stage = "No modules yet"

    upcoming = (
        Enrollment.objects.filter(employee=user, due_date__isnull=False)
        .exclude(status=COMPLETED)
        .select_related("module")
        .order_by("due_date")[:5]
    )
    context = {
        "upcoming": upcoming,
        "milestones": milestones,
        "stage": stage,
        "current": current,
        "recommended": services.recommended_modules(user, current),
        "points": services.total_points(user),
        "badges": services.user_badges(user),
    }
    return render(request, "enrollment/dashboard.html", context)


def _team_rows(user):
    """Enrollments the user may see: their own department for managers, everyone for HR."""
    rows = Enrollment.objects.select_related("employee__profile", "module")
    if not is_hr(user):
        department = get_profile(user).department
        if not department:
            return []
        rows = rows.filter(employee__profile__department__iexact=department)
    return list(rows.order_by("employee__first_name", "employee__username", "module__title"))


def manager_dashboard(request):
    department = get_profile(request.user).department
    rows = _team_rows(request.user)
    team_size = (
        UserProfile.objects.filter(role=UserProfile.Role.EMPLOYEE, department__iexact=department).count()
        if department else 0
    )
    context = {
        "department": department,
        "team_size": team_size,
        "recent_rows": rows[:8],
        "total": len(rows),
        "done": sum(1 for row in rows if row.status == COMPLETED),
        "overdue": sum(1 for row in rows if row.is_overdue),
    }
    return render(request, "enrollment/dashboard_manager.html", context)


# ----- Employee enrollment and learning (FR-05, FR-06, FR-07) -----

@login_required
def my_courses(request):
    """All modules the employee is enrolled in, with progress and assessment actions."""
    enrollments = (
        Enrollment.objects.filter(employee=request.user)
        .select_related("module", "assigned_by")
    )
    return render(request, "enrollment/my_courses.html", {
        "enrollments": enrollments,
        "pass_mark": services.PASS_MARK,
    })


@login_required
@require_POST
def enroll(request, pk):
    """Enroll in a module. Enrolling twice in the same module is not allowed (duplicate check)."""
    module = get_object_or_404(Module, pk=pk)
    _, created = services.enroll(request.user, module)
    if created:
        messages.success(request, f"You are enrolled in '{module.title}'.")
    else:
        messages.info(request, f"You are already enrolled in '{module.title}'.")
    return redirect("my_courses")


@login_required
@require_POST
def update_progress(request, pk):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("module"), pk=pk, employee=request.user
    )
    if enrollment.status == COMPLETED:
        messages.info(request, "This module is already completed.")
        return redirect("my_courses")

    form = ProgressForm(request.POST)
    if form.is_valid():
        services.record_progress(
            enrollment, form.cleaned_data["progress"], form.cleaned_data["minutes"] or 0
        )
        messages.success(request, f"Progress saved for '{enrollment.module.title}'.")
    else:
        messages.error(request, "Progress must be a number from 0 to 100.")
    return redirect("my_courses")


@login_required
@require_POST
def submit_assessment(request, pk):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("module"), pk=pk, employee=request.user
    )
    if enrollment.status == COMPLETED:
        messages.info(request, "This module is already completed.")
        return redirect("my_courses")

    form = AssessmentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a score from 0 to 100.")
        return redirect("my_courses")

    score = form.cleaned_data["score"]
    passed, new_badges = services.submit_assessment(enrollment, score)
    if passed:
        messages.success(
            request,
            f"Passed with {score}/100. '{enrollment.module.title}' is complete "
            f"and you earned {enrollment.module.points} points.",
        )
        for code in new_badges:
            messages.success(request, f"New badge unlocked: {services.BADGES[code]['name']}!")
    else:
        messages.warning(
            request,
            f"Score {score}/100. You need {services.PASS_MARK} to pass. Review the module and try again.",
        )
    return redirect("my_courses")


@login_required
def certificate(request, pk):
    """Download a PDF certificate for a completed module (FR-11)."""
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("module"), pk=pk, employee=request.user
    )
    if enrollment.status != COMPLETED:
        messages.warning(request, "The certificate is available after you pass the assessment.")
        return redirect("my_courses")

    try:
        pdf = build_certificate_pdf(
            learner_name=request.user.get_full_name() or request.user.username,
            module_title=enrollment.module.title,
            completed_on=timezone.localtime(enrollment.completed_at),
            score=enrollment.score,
            certificate_id=f"ST-{request.user.pk:04d}-{enrollment.pk:05d}",
        )
    except ImportError:
        messages.error(
            request,
            "PDF library (reportlab) is not installed. Run: pip install -r requirements.txt",
        )
        return redirect("my_courses")

    return FileResponse(
        pdf,
        as_attachment=True,
        filename=f"certificate-{enrollment.module.pk}.pdf",
        content_type="application/pdf",
    )


# ----- Notifications (FR-08) -----

@login_required
def notifications_page(request):
    items = request.user.notifications.select_related("enrollment__module")
    return render(request, "enrollment/notifications.html", {"items": items})


@login_required
@require_POST
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications")


# ----- Team progress and assignment: manager and HR (FR-04, FR-06) -----

@require(can_manage_team)
def team(request):
    """Progress of employees. Managers see their department, HR sees everyone."""
    rows = _team_rows(request.user)
    context = {
        "rows": rows,
        "total": len(rows),
        "done": sum(1 for row in rows if row.status == COMPLETED),
        "overdue": sum(1 for row in rows if row.is_overdue),
    }
    return render(request, "enrollment/team.html", context)


@require(can_manage_team)
def assign_module(request):
    """Assign a module to employees by department and job role."""
    user = request.user
    own_department = get_profile(user).department
    if request.method == "POST":
        form = AssignForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            department = data["department"].strip()
            if not is_hr(user):
                department = own_department
            if not department and not is_hr(user):
                messages.error(request, "Your profile has no department, so you cannot assign modules.")
                return redirect("team")

            employees = services.find_employees(department, data["job_role"].strip())
            if not employees:
                messages.warning(request, "No employees match that department and job role.")
                return redirect("assign_module")

            assigned, skipped = services.assign_module(
                data["module"], employees, user, data["due_date"]
            )
            messages.success(
                request,
                f"Assigned to {assigned} employee(s). Skipped {skipped} "
                "(already assigned or completed).",
            )
            return redirect("team")
    else:
        form = AssignForm()

    if is_hr(user):
        intro = "HR can assign to any department (leave it blank for everyone)."
    else:
        intro = f"You can assign modules to employees in your department: {own_department or 'not set'}."
    return render(request, "form_page.html", {
        "form": form,
        "title": "Assign a module",
        "submit_label": "Assign",
        "intro": intro,
    })
