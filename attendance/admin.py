from django.contrib import admin

from .models import Attendance, Holiday


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "date",
        "status",
        "marked_by",
        "email_sent",
        "created_at",
        "updated_at",
    )
    list_display_links = ("student", "date")
    list_filter = ("status", "email_sent", "date", "created_at", "updated_at")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__roll_number",
        "marked_by__username",
        "marked_by__email",
    )
    ordering = ("-date", "student__roll_number")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("student", "marked_by")
    date_hierarchy = "date"
    fieldsets = (
        (
            "Attendance Record",
            {
                "fields": ("id", "student", "date", "status"),
            },
        ),
        (
            "Tracking",
            {
                "fields": ("marked_by", "email_sent"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "reason", "created_at", "updated_at")
    list_display_links = ("date", "reason")
    list_filter = ("date", "created_at", "updated_at")
    search_fields = ("date", "reason")
    ordering = ("-date",)
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "date"
    fieldsets = (
        (
            "Holiday",
            {
                "fields": ("id", "date", "reason"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
