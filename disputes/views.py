from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from .models import Dispute
from .forms import DisputeForm
from attendance.models import Attendance
from students.models import Student
from datetime import date

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.is_staff and not self.request.user.is_superuser

class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class StudentDisputeCreateView(LoginRequiredMixin, StudentRequiredMixin, CreateView):
    model = Dispute
    form_class = DisputeForm
    template_name = 'disputes/dispute_form.html'
    success_url = reverse_lazy('my_disputes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_str = self.kwargs.get('date')
        try:
            target_date = date.fromisoformat(date_str)
            student = Student.objects.get(user=self.request.user)
            attendance = Attendance.objects.get(student=student, date=target_date)
            context['attendance'] = attendance
        except (ValueError, Student.DoesNotExist, Attendance.DoesNotExist):
            context['error'] = "Valid attendance record not found for this date."
        return context

    def form_valid(self, form):
        date_str = self.kwargs.get('date')
        try:
            target_date = date.fromisoformat(date_str)
            student = Student.objects.get(user=self.request.user)
            attendance = Attendance.objects.get(student=student, date=target_date)
            
            if attendance.status:
                messages.error(self.request, "Attendance is already marked as Present. No dispute needed.")
                return redirect('student_dashboard')
            
            if Dispute.objects.filter(student=student, date=target_date).exists():
                messages.error(self.request, "A dispute has already been raised for this date.")
                return redirect('my_disputes')

            dispute = form.save(commit=False)
            dispute.student = student
            dispute.attendance = attendance
            dispute.date = target_date
            dispute.status = 'pending'
            dispute.save()
            
            messages.success(self.request, "Dispute raised successfully. Waiting for teacher review.")
            return super().form_valid(form)
            
        except (ValueError, Student.DoesNotExist, Attendance.DoesNotExist):
            messages.error(self.request, "Invalid request.")
            return redirect('student_dashboard')

class StudentDisputeListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = Dispute
    template_name = 'disputes/my_disputes.html'
    context_object_name = 'disputes'

    def get_queryset(self):
        student = Student.objects.get(user=self.request.user)
        return Dispute.objects.filter(student=student).order_by('-created_at')

class TeacherManageDisputeView(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    model = Dispute
    template_name = 'disputes/manage_disputes.html'
    context_object_name = 'disputes'

    def get_queryset(self):
        status_filter = self.request.GET.get('status', 'pending')
        return Dispute.objects.filter(status=status_filter).select_related('student', 'attendance')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('status', 'pending')
        return context

class DisputeActionView(LoginRequiredMixin, TeacherRequiredMixin, View):
    def post(self, request, pk, action):
        dispute = get_object_or_404(Dispute, pk=pk)
        
        if dispute.status != 'pending':
            messages.error(request, "This dispute has already been resolved.")
            return redirect('manage_disputes')

        with transaction.atomic():
            if action == 'approve':
                dispute.status = 'approved'
                # Update attendance record
                attendance = dispute.attendance
                attendance.status = True
                attendance.save()
                messages.success(request, f"Dispute for {dispute.student.first_name} approved. Attendance updated to Present.")
            elif action == 'reject':
                dispute.status = 'rejected'
                messages.warning(request, f"Dispute for {dispute.student.first_name} rejected.")
            
            dispute.save()

        return redirect('manage_disputes')
