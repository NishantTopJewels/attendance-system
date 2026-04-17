from django.core.mail import send_mail
from django.conf import settings
from .models import Attendance
from .utils import is_working_day
from datetime import timedelta

def get_consecutive_absences(student, target_date):
    """
    Count consecutive working days where the student was absent, moving backwards from target_date.
    """
    count = 0
    current_date = target_date
    
    while True:
        try:
            att = Attendance.objects.get(student=student, date=current_date)
            if att.status == False: # Absent
                count += 1
            else:
                break
        except Attendance.DoesNotExist:
            break
            
        # Move to previous day
        current_date -= timedelta(days=1)
        
        # Skip non-working days (Sundays and Holidays)
        while not is_working_day(current_date):
            current_date -= timedelta(days=1)
            
    return count

def send_attendance_notifications(attendance_date):
    """
    Sends absence notifications and warning emails for a specific date.
    """
    absent_records = Attendance.objects.filter(
        date=attendance_date, 
        status=False, 
        email_sent=False
    ).select_related('student')
    
    for record in absent_records:
        student = record.student
        recipient_email = student.email
        
        if not recipient_email:
            continue
            
        consecutive_count = get_consecutive_absences(student, attendance_date)
        
        # Determine subject and message
        if consecutive_count >= 3:
            subject = "Attendance Warning"
            msg = f"Hello {student.first_name},\n\nYou have been absent for {consecutive_count} consecutive days (including today, {attendance_date.strftime('%d %B %Y')}). Please provide a valid reason to the faculty as soon as possible."
        else:
            subject = "Absent Notification"
            msg = f"Hello {student.first_name},\n\nYou were marked absent on {attendance_date.strftime('%d %B %Y')}."

        try:
            send_mail(
                subject=subject,
                message=msg,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@edutrack.com'),
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            # Mark as sent to avoid duplicates
            record.email_sent = True
            record.save()
        except Exception as e:
            # In a production app, we'd log this.
            print(f"Failed to send email to {recipient_email}: {e}")
