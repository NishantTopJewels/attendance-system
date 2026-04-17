from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.StudentDisputeListView.as_view(), name='my_disputes'),
    path('create/<str:date>/', views.StudentDisputeCreateView.as_view(), name='create_dispute'),
    path('manage/', views.TeacherManageDisputeView.as_view(), name='manage_disputes'),
    path('action/<int:pk>/<str:action>/', views.DisputeActionView.as_view(), name='dispute_action'),
]
