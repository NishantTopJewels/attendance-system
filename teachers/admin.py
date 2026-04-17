from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "firstname",
        "lastname",
        "subject",
        "email",
        "phone",
        "user",
    )
    list_display_links = ("firstname", "lastname")
    list_filter = ("subject",)
    search_fields = (
        "firstname",
        "lastname",
        "subject",
        "email",
        "phone",
        "user__username",
        "user__email",
    )
    ordering = ("firstname", "lastname", "subject")
    readonly_fields = ("id",)
    autocomplete_fields = ("user",)
    fieldsets = (
        (
            "Account",
            {
                "fields": ("id", "user"),
            },
        ),
        (
            "Teacher Details",
            {
                "fields": ("firstname", "lastname", "subject"),
            },
        ),
        (
            "Contact",
            {
                "fields": ("email", "phone"),
            },
        ),
    )
