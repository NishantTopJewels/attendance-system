from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "roll_number",
        "first_name",
        "last_name",
        "age",
        "email",
        "phone",
        "user",
        "created_at",
        "updated_at",
    )
    list_display_links = ("roll_number", "first_name", "last_name")
    list_filter = ("created_at", "updated_at")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "roll_number",
        "user__username",
        "user__email",
    )
    ordering = ("roll_number", "first_name", "last_name")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    fieldsets = (
        (
            "Account",
            {
                "fields": ("id", "user"),
            },
        ),
        (
            "Student Details",
            {
                "fields": ("roll_number", "first_name", "last_name", "age"),
            },
        ),
        (
            "Contact",
            {
                "fields": ("email", "phone"),
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
