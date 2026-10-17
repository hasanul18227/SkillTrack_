"""Part 2 - Module catalog, module details, module management (HR), feedback and HR dashboard."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from accounts.models import UserProfile
from accounts.permissions import is_hr, require
from enrollment.models import Enrollment

from .forms import FeedbackForm, ModuleForm
from .models import Feedback, Module

COMPLETED = Enrollment.Status.COMPLETED


# ----- Dashboard for HR / Admin (called from accounts.views.dashboard) -----

def hr_dashboard(request):
    today = timezone.localdate()
    context = {
        "total_modules": Module.objects.count(),
        "by_level": [
            {"label": label, "count": Module.objects.filter(level=value).count()}
            for value, label in Module.Level.choices
        ],
        "total_employees": UserProfile.objects.filter(role=UserProfile.Role.EMPLOYEE).count(),
        "total_enrollments": Enrollment.objects.count(),
        "completed": Enrollment.objects.filter(status=COMPLETED).count(),
        "overdue": Enrollment.objects.filter(due_date__lt=today).exclude(status=COMPLETED).count(),
        "recent_modules": Module.objects.order_by("-created_at")[:5],
    }
    return render(request, "modules/dashboard_hr.html", context)


# ----- Catalog and details (all logged-in users) -----

@login_required
def module_list(request):
    """Available training modules with search. Shows each module's enrollment status for this user."""
    q = request.GET.get("q", "").strip()
    modules = Module.objects.all()
    if q:
        modules = modules.filter(
            Q(title__icontains=q) | Q(category__icontains=q) | Q(skill_tags__icontains=q)
        )
    status_by_module = dict(
        Enrollment.objects.filter(employee=request.user).values_list("module_id", "status")
    )
    items = [(module, status_by_module.get(module.pk)) for module in modules]
    return render(request, "modules/catalog.html", {"items": items, "q": q})


@login_required
def module_detail(request, pk):
    module = get_object_or_404(Module, pk=pk)
    enrollment = Enrollment.objects.filter(employee=request.user, module=module).first()
    can_review = bool(enrollment) and enrollment.status == COMPLETED
    my_feedback = module.feedback.filter(author=request.user).first()
    context = {
        "module": module,
        "enrollment": enrollment,
        "can_review": can_review,
        "my_feedback": my_feedback,
        "form": FeedbackForm(instance=my_feedback) if can_review else None,
        "feedback_items": module.feedback.select_related("author"),
    }
    return render(request, "modules/module_detail.html", context)


# ----- Feedback (FR-12) -----

@login_required
@require_POST
def submit_feedback(request, pk):
    module = get_object_or_404(Module, pk=pk)
    is_completed = Enrollment.objects.filter(
        employee=request.user, module=module, status=COMPLETED
    ).exists()
    if not is_completed:
        messages.error(request, "You can rate a module after completing it.")
        return redirect("module_detail", pk=module.pk)

    form = FeedbackForm(request.POST)
    if form.is_valid():
        Feedback.objects.update_or_create(
            module=module,
            author=request.user,
            defaults={
                "rating": form.cleaned_data["rating"],
                "comment": form.cleaned_data["comment"],
            },
        )
        messages.success(request, "Thanks! Your feedback has been saved.")
    else:
        messages.error(request, "Rating must be 1 to 5 and the comment under 500 characters.")
    return redirect("module_detail", pk=module.pk)


@require(is_hr)
@require_POST
def delete_feedback(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    module_pk = feedback.module_id
    feedback.delete()
    messages.success(request, "Feedback removed.")
    return redirect("module_detail", pk=module_pk)


# ----- Module management: HR only (FR-13) -----

class HROnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return is_hr(self.request.user)


class ModuleManageList(HROnlyMixin, ListView):
    model = Module
    template_name = "modules/manage_modules.html"
    context_object_name = "modules"


class ModuleCreate(HROnlyMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = "form_page.html"
    success_url = reverse_lazy("manage_modules")
    extra_context = {"title": "Add training module", "submit_label": "Save module"}

    def form_valid(self, form):
        messages.success(self.request, "Module created.")
        return super().form_valid(form)


class ModuleUpdate(HROnlyMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = "form_page.html"
    success_url = reverse_lazy("manage_modules")
    extra_context = {"title": "Edit training module", "submit_label": "Save changes"}

    def form_valid(self, form):
        messages.success(self.request, "Module updated.")
        return super().form_valid(form)


@require(is_hr)
@require_POST
def module_delete(request, pk):
    module = get_object_or_404(Module, pk=pk)
    title = module.title
    module.delete()
    messages.success(request, f"'{title}' was deleted.")
    return redirect("manage_modules")
