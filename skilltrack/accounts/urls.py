"""Part 1 - Home, login, logout, registration, profile, password and dashboard routes."""
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Login and logout (all roles)
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Registration and profile
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),

    # Role-based dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Change password (logged-in users)
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="form_page.html",
            extra_context={"title": "Change password", "submit_label": "Change password"},
            success_url=reverse_lazy("password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="message.html",
            extra_context={"title": "Password changed", "text": "Your password was changed successfully."},
        ),
        name="password_change_done",
    ),

    # Forgot password: email reset link (printed in the terminal during development)
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="form_page.html",
            extra_context={
                "title": "Reset password",
                "intro": "Enter your account email. A reset link will be sent to you.",
                "submit_label": "Send reset link",
            },
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="message.html",
            extra_context={
                "title": "Check your email",
                "text": "If an account with that email exists, a reset link has been sent.",
            },
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy("password_reset_complete")),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="message.html",
            extra_context={
                "title": "Password reset complete",
                "text": "Your password has been reset. You can log in now.",
            },
        ),
        name="password_reset_complete",
    ),
]
