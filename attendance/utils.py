from datetime import timedelta, date
from django.utils import timezone
from .models import Holiday

def is_working_day(date_obj):
    if date_obj.weekday() == 6:  # Sunday
        return False
    if Holiday.objects.filter(date=date_obj).exists():
        return False
    return True

def get_working_days_in_range(start_date, end_date):
    """
    Returns a list of working days between start_date and end_date (inclusive).
    """
    working_days = []
    # Fetch all holidays in range once to avoid N queries
    holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() != 6 and current_date not in holidays:
            working_days.append(current_date)
        current_date += timedelta(days=1)
    return working_days

def get_date_range(filter_type, custom_start=None, custom_end=None):
    today = timezone.now().date()
    if filter_type == 'today':
        return today, today
    elif filter_type == 'this_week':
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week, today
    elif filter_type == 'this_month':
        start_of_month = today.replace(day=1)
        return start_of_month, today
    elif filter_type == 'this_year':
        start_of_year = today.replace(month=1, day=1)
        return start_of_year, today
    elif filter_type == 'custom' and custom_start and custom_end:
        try:
            if isinstance(custom_start, str):
                custom_start = date.fromisoformat(custom_start)
            if isinstance(custom_end, str):
                custom_end = date.fromisoformat(custom_end)
            return custom_start, custom_end
        except (ValueError, TypeError):
            pass
    return today, today
