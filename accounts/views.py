from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import PasswordResetConfirmView, LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import View
from .forms import RoleBasedAuthenticationForm

class HomeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            # Send admin to a home view - for now redirect to teacher dashboard as root
            return redirect('teacher_dashboard')
        return redirect('dashboard_router')

class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect('home')
        if request.user.is_staff:
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')

class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_setup.html"
    success_url = reverse_lazy("root_login")

    def form_valid(self, form):
        messages.success(self.request, "Password was successfully reset. You can now log in.")
        return super().form_valid(form)
class RoleLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = RoleBasedAuthenticationForm
    redirect_authenticated_user = True
