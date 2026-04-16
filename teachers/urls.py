from django.urls import path
from .views import (
    TeacherListView,
    TeacherCreateView,
    TeacherDashboardView,
    TeacherDetailView,
    TeacherUpdateView,
    HolidayManagementView,
)

urlpatterns = [
    path("", TeacherListView.as_view(), name="teacher_list"),
    path("create/", TeacherCreateView.as_view(), name="teacher_create"),
    path("dashboard/", TeacherDashboardView.as_view(), name="teacher_dashboard"),
    path("<int:pk>/", TeacherDetailView.as_view(), name="teacher_detail"),
    path("<int:pk>/edit/", TeacherUpdateView.as_view(), name="teacher_update"),
    path("holidays/", HolidayManagementView.as_view(), name="holiday_management"),
]
