from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Student
from .forms import StudentCreationForm, StudentUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin
from attendance.models import Attendance, Holiday
from attendance.utils import get_date_range, get_working_days_in_range
from datetime import timedelta, date
from django.utils import timezone

# You can adjust this to import from wherever you placed TeacherRequiredMixin.
from teachers.views import TeacherRequiredMixin


class StudentListView(TeacherRequiredMixin, ListView):
    model = Student
    template_name = "students/student_list.html"
    context_object_name = "students"


class StudentDetailView(TeacherRequiredMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()

        filter_type = self.request.GET.get("filter", "this_month")
        c_start = self.request.GET.get("start_date")
        c_end = self.request.GET.get("end_date")
        start_date, end_date = get_date_range(filter_type, c_start, c_end)

        # Only consider dates where attendance is captured
        captured_dates = set(
            Attendance.objects.filter(date__range=(start_date, end_date)).values_list(
                "date", flat=True
            )
        )
        working_days = sorted(
            [
                d
                for d in get_working_days_in_range(start_date, end_date)
                if d in captured_dates
            ]
        )

        attendance_records = Attendance.objects.filter(
            student=student, date__in=working_days
        ).order_by("date")
        present_count = attendance_records.filter(status=True).count()
        absent_records = attendance_records.filter(status=False)
        total_days = len(working_days)
        percentage = (present_count * 100 / total_days) if total_days > 0 else 0

        # Handle 3+ days holiday/absence logic
        all_holidays = Holiday.objects.filter(
            date__range=(start_date, end_date)
        ).order_by("date")
        consecutive_holidays = []
        temp_h = []
        for h in all_holidays:
            if not temp_h or h.date == temp_h[-1].date + timedelta(days=1):
                temp_h.append(h)
            else:
                if len(temp_h) >= 3:
                    consecutive_holidays.append(temp_h)
                temp_h = [h]
        if len(temp_h) >= 3:
            consecutive_holidays.append(temp_h)

        consecutive_absences = []
        temp_a = []
        absent_dates = [r.date for r in absent_records]
        for d in working_days:
            if d in absent_dates:
                temp_a.append(d)
            else:
                if len(temp_a) >= 3:
                    consecutive_absences.append(temp_a)
                temp_a = []
        if len(temp_a) >= 3:
            consecutive_absences.append(temp_a)

        context.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "filter_type": filter_type,
                "percentage": percentage,
                "total_days": total_days,
                "present_count": present_count,
                "attendance_records": attendance_records,
                "consecutive_holidays": consecutive_holidays,
                "consecutive_absences": consecutive_absences,
                "filter_options": [
                    ("this_week", "Week"),
                    ("this_month", "Month"),
                    ("custom", "Custom"),
                ],
            }
        )
        return context


class StudentUpdateView(TeacherRequiredMixin, UpdateView):
    model = Student
    form_class = StudentUpdateForm
    template_name = "students/student_form.html"

    def get_success_url(self):
        return reverse("student_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Student details updated successfully.")
        return super().form_valid(form)


class StudentCreateView(TeacherRequiredMixin, CreateView):
    model = Student
    form_class = StudentCreationForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("student_create")

    def form_valid(self, form):
        first_name = form.cleaned_data.get("first_name")
        last_name = form.cleaned_data.get("last_name")
        email = form.cleaned_data.get("email")
        roll_number = form.cleaned_data.get("roll_number")

        # Create basic User account for the student
        user = User.objects.create(
            username=str(roll_number),
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()

        # Link User to Student
        student = form.save(commit=False)
        student.user = user
        student.save()

        # Prepare reset link and email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = f"/set-password/{uid}/{token}/"
        full_reset_link = self.request.build_absolute_uri(reset_url)

        message = (
            f"Hello {student.first_name},\n\n"
            f"Your student account has been created. "
            f"Please set your password and activate your account by clicking the link below:\n"
            f"{full_reset_link}\n\n"
            f"Thanks,\nSystem Administrator"
        )

        try:
            send_mail(
                subject="Setup your Student Account",
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com"),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            # You might want to log this in a real application
            print(f"Error sending email: {e}")

        self.object = student
        messages.success(self.request, "Student was successfully created.")
        return HttpResponseRedirect(self.get_success_url())


from django.contrib.auth.mixins import UserPassesTestMixin
import calendar

class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "students/dashboard.html"

    def test_func(self):
        # Only allow students (not staff or superuser)
        return not self.request.user.is_staff and not self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            student = Student.objects.get(user=user)
        except Student.DoesNotExist:
            context['error'] = "Student record not found."
            return context

        today = timezone.now().date()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))

        # Handle month overflow/underflow
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        # Month range
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        # Navigation context
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
            
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1

        # 1. Fetch data
        attendance_qs = Attendance.objects.filter(student=student, date__range=(start_date, end_date))
        attendance_map = {a.date: a.status for a in attendance_qs}
        holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))
        captured_dates = set(
            Attendance.objects.filter(date__range=(start_date, end_date)).values_list(
                "date", flat=True
            )
        )
        captured_working_days = set(
            d for d in get_working_days_in_range(start_date, end_date) if d in captured_dates
        )

        # 2. Calendar Heatmap Data
        heatmap_data = []
        curr = start_date
        total_working_days = len(captured_working_days)
        total_present = 0
        total_absent = 0

        while curr <= end_date:
            is_sunday = curr.weekday() == 6
            is_holiday = curr in holidays
            
            if is_sunday or is_holiday:
                status = "holiday"
            elif curr in captured_working_days:
                if attendance_map.get(curr):
                    status = "present"
                    total_present += 1
                else:
                    status = "absent"
                    total_absent += 1
            else:
                status = "not_marked"
            
            heatmap_data.append({'date': curr, 'status': status})
            curr += timedelta(days=1)

        # 3. Stats Calculation
        percentage = (total_present * 100 / total_working_days) if total_working_days > 0 else 0

        # 4. Streak Calculation
        # Holidays and Sundays do not break streaks; they are skipped.
        current_streak = 0

        def check_working(d):
            if d.weekday() == 6: return False
            if Holiday.objects.filter(date=d).exists(): return False
            return True

        curr_s = today
        while True:
            if not check_working(curr_s):
                curr_s -= timedelta(days=1)
                continue
            rec = attendance_map.get(curr_s)
            if rec is None:
                rec = Attendance.objects.filter(student=student, date=curr_s).values_list("status", flat=True).first()
            if rec:
                current_streak += 1
                curr_s -= timedelta(days=1)
            else:
                break

        # Longest Streak in this range
        longest_streak = 0
        temp_streak = 0
        for day in heatmap_data:
            if day['status'] == 'present':
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            elif day['status'] in ('absent', 'not_marked'):
                temp_streak = 0

        # Holiday mapping for reasons
        holiday_map = {h.date: h.reason for h in Holiday.objects.filter(date__range=(start_date, end_date))}

        context.update({
            'student': student,
            'heatmap_data': heatmap_data,
            'total_working_days': total_working_days,
            'total_present': total_present,
            'total_absent': total_absent,
            'percentage': percentage,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'timeline': attendance_qs.order_by('-date'),
            'month_name': start_date.strftime("%B %Y"),
            'start_weekday': start_date.weekday(), # 0=Mon, 6=Sun
            'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'holiday_map': holiday_map,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'year': year,
            'month': month,
        })
        return context
