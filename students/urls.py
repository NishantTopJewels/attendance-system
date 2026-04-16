from django.urls import path
from .views import StudentListView, StudentCreateView, StudentDashboardView, StudentDetailView, StudentUpdateView

urlpatterns = [
    path("", StudentListView.as_view(), name="student_list"),
    path("create/", StudentCreateView.as_view(), name="student_create"),
    path("dashboard/", StudentDashboardView.as_view(), name="student_dashboard"),
    path("<int:pk>/", StudentDetailView.as_view(), name="student_detail"),
    path("<int:pk>/edit/", StudentUpdateView.as_view(), name="student_update"),
]
