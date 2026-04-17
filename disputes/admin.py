from django.contrib import admin

from .models import Dispute


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "attendance",
        "date",
        "status",
        "proof",
        "created_at",
    )
    list_display_links = ("student", "date")
    list_filter = ("status", "date", "created_at")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__roll_number",
        "attendance__student__first_name",
        "attendance__student__last_name",
        "reason",
    )
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at")
    autocomplete_fields = ("student", "attendance")
    date_hierarchy = "date"
    fieldsets = (
        (
            "Student And Attendance",
            {
                "fields": ("id", "student", "attendance", "date"),
            },
        ),
        (
            "Dispute Details",
            {
                "fields": ("reason", "proof", "status"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )
