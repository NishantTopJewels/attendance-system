from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from datetime import date
from students.models import Student
from .models import Attendance, Holiday
from .utils import is_working_day

def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_staff_or_superuser)
def mark_attendance(request):
    today_date = timezone.now().date().isoformat()
    # Safely extract requested date. Prevent future dates intrinsically.
    date_str = request.GET.get('date') or request.POST.get('date') or today_date
    if date_str > today_date:
        date_str = today_date
        
    try:
        date_obj = date.fromisoformat(date_str)
    except ValueError:
        date_obj = timezone.now().date()
        date_str = date_obj.isoformat()
        
    edit_mode = request.GET.get('edit') == 'true'
    working_day = is_working_day(date_obj)
    holiday_dates = list(Holiday.objects.values_list('date', flat=True))

    if not working_day:
        holiday_record = Holiday.objects.filter(date=date_obj).first()
        reason = holiday_record.reason if holiday_record else "Sunday"
        error_msg = f"Attendance cannot be marked on holidays or Sundays. Reason: {reason}"
        
        return render(request, 'attendance/mark_attendance.html', {
            'error_msg': error_msg,
            'selected_date': date_str,
            'today_date': today_date,
            'holiday_dates': holiday_dates,
        })

    # Processing logic for valid working days
    if request.method == 'POST':
        students = Student.objects.all()
        for student in students:
            # Checkbox will only be in POST if checked
            status = f"student_{student.id}" in request.POST
            Attendance.objects.update_or_create(
                student=student,
                date=date_str,
                defaults={
                    'status': status,
                    'marked_by': request.user
                }
            )
        
        # Trigger email notifications for absences and streaks
        from .notifications import send_attendance_notifications
        send_attendance_notifications(date_obj)
        
        # Explicit Redirect mapping strictly back to visual read-only representation.
        url = reverse('mark_attendance') + f"?date={date_str}"
        return redirect(url)
        
    # GET request evaluates the visual protection paradigm natively
    students = Student.objects.all().order_by('roll_number')
    records_exist = Attendance.objects.filter(date=date_str).exists()
    
    is_read_only = records_exist and not edit_mode
    
    present_student_ids = set()
    absent_student_ids = set()

    if records_exist:
        present_student_ids = set(
            Attendance.objects.filter(date=date_str, status=True).values_list('student_id', flat=True)
        )
        absent_student_ids = set(
            Attendance.objects.filter(date=date_str, status=False).values_list('student_id', flat=True)
        )
    
    return render(request, 'attendance/mark_attendance.html', {
        'students': students,
        'selected_date': date_str,
        'today_date': today_date,
        'records_exist': records_exist,
        'is_read_only': is_read_only,
        'edit_mode': edit_mode,
        'present_student_ids': present_student_ids,
        'absent_student_ids': absent_student_ids,
        'holiday_dates': holiday_dates,
    })
