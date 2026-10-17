"""Part 3 - Enrollment, my courses, progress, assessment, certificate, notifications, team and assign routes."""
from django.urls import path

from . import views

urlpatterns = [
    path("my-courses/", views.my_courses, name="my_courses"),
    path("modules/<int:pk>/enroll/", views.enroll, name="enroll"),
    path("learning/<int:pk>/progress/", views.update_progress, name="update_progress"),
    path("learning/<int:pk>/assessment/", views.submit_assessment, name="submit_assessment"),
    path("learning/<int:pk>/certificate/", views.certificate, name="certificate"),
    path("notifications/", views.notifications_page, name="notifications"),
    path("notifications/read/", views.mark_notifications_read, name="mark_notifications_read"),
    path("team/", views.team, name="team"),
    path("assign/", views.assign_module, name="assign_module"),
]
