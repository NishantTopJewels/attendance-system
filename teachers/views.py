from django.views.generic import (
    ListView,
    FormView,
    DetailView,
    UpdateView,
    TemplateView,
)
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
import calendar
from datetime import date, timedelta
from django.contrib import messages
from django.utils import timezone
from django.db.models import (
    Count,
    Q,
    Case,
    When,
    Value,
    FloatField,
    ExpressionWrapper,
    F,
)

from .forms import TeacherCreationForm, TeacherUpdateForm
from .models import Teacher
from attendance.models import Holiday, Attendance
from attendance.utils import get_working_days_in_range, get_date_range, is_working_day
from students.models import Student


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class TeacherListView(AdminRequiredMixin, ListView):
    model = Teacher
    template_name = "teachers/teacher_list.html"
    context_object_name = "teachers"

    def get_queryset(self):
        return Teacher.objects.select_related("user").all()


class TeacherCreateView(AdminRequiredMixin, FormView):
    template_name = "teachers/teacher_form.html"
    form_class = TeacherCreationForm
    success_url = reverse_lazy("teacher_list")

    def form_valid(self, form):
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        email = form.cleaned_data["email"]
        phone = form.cleaned_data["phone"]
        subject = form.cleaned_data["subject"]

        # Use email as username as requested
        username = email

        # Create user
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=False,
        )
        user.set_unusable_password()
        user.save()

        # Create Teacher entry
        Teacher.objects.create(
            user=user,
            firstname=first_name,
            lastname=last_name,
            email=email,
            phone=phone,
            subject=subject,
        )

        # Send invite email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = self.request.build_absolute_uri(f"/set-password/{uid}/{token}/")

        message = (
            f"Hello {first_name} {last_name},\n\n"
            f"An admin has created a teacher account for you.\n"
            f"Please set your password by clicking the link below to activate your account:\n\n"
            f"{reset_link}\n\n"
            f"Thanks,\nAdmin"
        )

        try:
            send_mail(
                subject="Set your password",
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com"),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")

        return super().form_valid(form)


class HolidayManagementView(AdminRequiredMixin, TemplateView):
    template_name = "teachers/holiday_management.html"

    def post(self, request, *args, **kwargs):
        # Handle adding/removing holidays
        h_date = request.POST.get("date")
        reason = request.POST.get("reason")
        action = request.POST.get("action")  # 'add' or 'remove'

        if not h_date:
            return redirect("holiday_management")

        target_date = date.fromisoformat(h_date)

        today = date.today()
        if target_date < today:
            messages.error(request, "Cannot modify holidays in the past.")
            return redirect("holiday_management")

        if action == "add":
            # Check if attendance exists
            if Attendance.objects.filter(date=target_date).exists():
                messages.error(
                    request,
                    f"Cannot mark {h_date} as holiday. Attendance records already exist for this day.",
                )
            else:
                Holiday.objects.update_or_create(
                    date=target_date, defaults={"reason": reason}
                )
                messages.success(request, f"Holiday added for {h_date}.")
        elif action == "remove":
            # Also block removal if it's today and attendance exists
            if target_date == today and Attendance.objects.filter(date=target_date).exists():
                 messages.error(request, "Cannot remove holiday after attendance has been captured for today.")
            else:
                Holiday.objects.filter(date=target_date).delete()
                messages.success(request, f"Holiday removed for {h_date}.")

        return redirect("holiday_management")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        d = date.today()
        year = int(self.request.GET.get("year", d.year))
        month = int(self.request.GET.get("month", d.month))

        cal = calendar.Calendar()
        month_days_raw = cal.monthdatescalendar(year, month)

        holiday_map = {
            h.date: h.reason
            for h in Holiday.objects.filter(date__year=year, date__month=month)
        }

        month_days = []
        for week in month_days_raw:
            new_week = []
            for day in week:
                new_week.append(
                    {
                        "date": day,
                        "is_holiday": day in holiday_map,
                        "reason": holiday_map.get(day),
                    }
                )
            month_days.append(new_week)

        # Navigation
        prev_m = (month - 2) % 12 + 1
        prev_y = year if month > 1 else year - 1
        next_m = month % 12 + 1
        next_y = year if month < 12 else year + 1

        # ✅ FIXED HERE
        num_days = calendar.monthrange(year, month)[1]
        working_days_count = 0
        for m_day in range(1, num_days + 1):
            cur = date(year, month, m_day)
            if cur.weekday() != 6 and cur not in holiday_map:
                working_days_count += 1

        context.update(
            {
                "working_days_count": working_days_count,
                "month_days": month_days,
                "holidays": holiday_map,
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "prev_m": prev_m,
                "prev_y": prev_y,
                "next_m": next_m,
                "next_y": next_y,
                "today": date.today(),
            }
        )
        return context


class TeacherDetailView(AdminRequiredMixin, DetailView):
    model = Teacher
    template_name = "teachers/teacher_detail.html"
    context_object_name = "teacher"


class TeacherUpdateView(AdminRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherUpdateForm
    template_name = "teachers/teacher_form.html"
    success_url = reverse_lazy("teacher_list")

    def form_valid(self, form):
        teacher = form.save(commit=False)
        user = teacher.user
        user.first_name = teacher.firstname
        user.last_name = teacher.lastname
        user.email = teacher.email
        user.username = teacher.email
        user.save()
        teacher.save()
        messages.success(self.request, "Teacher details updated successfully.")
        return super().form_valid(form)


class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = "teachers/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # 1. Filters
        filter_type = self.request.GET.get("filter", "this_month")
        c_start = self.request.GET.get("start_date")
        c_end = self.request.GET.get("end_date")
        start_date, end_date = get_date_range(filter_type, c_start, c_end)

        # 2. Working Day & Captured Logic
        # Fetch all dates specifically in range where ANY attendance was marked
        captured_dates = set(
            Attendance.objects.filter(date__range=(start_date, end_date)).values_list(
                "date", flat=True
            )
        )

        # Intersection of working days and captured dates
        working_days = [
            d
            for d in get_working_days_in_range(start_date, end_date)
            if d in captured_dates
        ]
        working_days_count = len(working_days)

        # 3. Today Snapshot
        is_today_working = is_working_day(today)
        total_students_count = Student.objects.count()
        present_today = 0
        absent_today = 0
        attendance_percentage_today = 0

        if is_today_working:
            present_today = Attendance.objects.filter(date=today, status=True).count()
            absent_today = total_students_count - present_today
            if total_students_count > 0:
                attendance_percentage_today = (
                    present_today / total_students_count
                ) * 100

        # 4. Range Analytics & Student-wise Analytics (Optimized)
        # Using a single query with annotation to get student-wise data for the range
        if working_days_count > 0:
            percentage_expr = ExpressionWrapper(
                F("present_count") * 100.0 / Value(working_days_count),
                output_field=FloatField(),
            )
        else:
            percentage_expr = Value(0.0, output_field=FloatField())

        students_with_stats = (
            Student.objects.annotate(
                present_count=Count(
                    "attendance",
                    filter=Q(
                        attendance__date__in=working_days, attendance__status=True
                    ),
                ),
                marked_count=Count(
                    "attendance", filter=Q(attendance__date__in=working_days)
                ),
            )
            .annotate(
                absent_count=Value(working_days_count) - F("present_count"),
                percentage=percentage_expr,
            )
            .order_by("roll_number")
        )

        # 5. Threshold Lists
        students_below_75 = [s for s in students_with_stats if s.percentage < 75]
        students_below_50 = [s for s in students_with_stats if s.percentage < 50]

        # 6. Distribution Buckets
        distribution = {
            "excellent": 0,  # 90-100
            "good": 0,  # 75-90
            "warning": 0,  # 50-75
            "critical": 0,  # <50
        }
        for s in students_with_stats:
            p = s.percentage
            if p >= 90:
                distribution["excellent"] += 1
            elif p >= 75:
                distribution["good"] += 1
            elif p >= 50:
                distribution["warning"] += 1
            else:
                distribution["critical"] += 1

        # 7. Trends: Consecutive Absentees (3+ continuous working days)
        # We need to fetch attendance records for the range to check continuity in Python
        consecutive_absentees = []
        if working_days_count >= 3:
            # Sort working days to ensure correct continuity check
            sorted_working_days = sorted(working_days)

            # Fetch all absences in range once
            absences = Attendance.objects.filter(
                date__in=sorted_working_days, status=False
            ).values("student_id", "date")

            # Group absences by student
            student_absences = {}
            for a in absences:
                sid = a["student_id"]
                if sid not in student_absences:
                    student_absences[sid] = set()
                student_absences[sid].add(a["date"])

            for student in students_with_stats:
                if student.id in student_absences:
                    absent_dates = student_absences[student.id]
                    count = 0
                    max_consecutive = 0
                    for d in sorted_working_days:
                        if d in absent_dates:
                            count += 1
                            max_consecutive = max(max_consecutive, count)
                        else:
                            count = 0
                    if max_consecutive >= 3:
                        consecutive_absentees.append(student)

        # Frequently absent
        frequently_absent = sorted(
            students_with_stats, key=lambda x: x.absent_count, reverse=True
        )[:5]

        # Range Totals
        total_attendance_records = Attendance.objects.filter(
            date__in=working_days
        ).count()
        avg_percentage = 0
        if total_students_count > 0:
            avg_percentage = (
                sum(s.percentage for s in students_with_stats) / total_students_count
            )

        context.update(
            {
                "total_students_count": total_students_count,
                "present_today": present_today,
                "absent_today": absent_today,
                "attendance_percentage_today": attendance_percentage_today,
                "is_today_working": is_today_working,
                "working_days_count": working_days_count,
                "total_attendance_records": total_attendance_records,
                "avg_percentage": avg_percentage,
                "students_stats": students_with_stats,
                "students_below_75": students_below_75,
                "students_below_50": students_below_50,
                "distribution": distribution,
                "consecutive_absentees": consecutive_absentees,
                "frequently_absent": frequently_absent,
                "filter_type": filter_type,
                "start_date": start_date,
                "end_date": end_date,
                "filter_options": [
                    ("today", "Today"),
                    ("this_week", "Week"),
                    ("this_month", "Month"),
                    ("this_year", "Year"),
                    ("custom", "Custom"),
                ],
            }
        )
        return context
