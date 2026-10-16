"""Part 2 - Catalog, module details, feedback and module management routes."""
from django.urls import path

from . import views

urlpatterns = [
    path("modules/", views.module_list, name="module_list"),
    path("modules/<int:pk>/", views.module_detail, name="module_detail"),
    path("modules/<int:pk>/feedback/", views.submit_feedback, name="submit_feedback"),
    path("feedback/<int:pk>/delete/", views.delete_feedback, name="delete_feedback"),
    path("manage/modules/", views.ModuleManageList.as_view(), name="manage_modules"),
    path("manage/modules/new/", views.ModuleCreate.as_view(), name="module_create"),
    path("manage/modules/<int:pk>/edit/", views.ModuleUpdate.as_view(), name="module_update"),
    path("manage/modules/<int:pk>/delete/", views.module_delete, name="module_delete"),
]
