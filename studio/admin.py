from django.contrib import admin

from .models import (
    ContactMessage,
    IntensiveApplication,
    SentimentalValueApplication,
    WaitlistEntry,
    WeekendInterest,
)


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)
    date_hierarchy = "created_at"


@admin.register(WeekendInterest)
class WeekendInterestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "city", "created_at")
    list_filter = ("city",)
    search_fields = ("name", "email")


@admin.register(SentimentalValueApplication)
class SentimentalValueApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "object_description")
    date_hierarchy = "created_at"


@admin.register(IntensiveApplication)
class IntensiveApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "payment_plan_needed",
        "sponsored_seat_consideration",
        "application_fee_status",
        "created_at",
    )
    list_filter = (
        "payment_plan_needed",
        "sponsored_seat_consideration",
        "application_fee_status",
        "interview_format",
    )
    search_fields = ("first_name", "last_name", "email")
    date_hierarchy = "created_at"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("kind", "name", "email", "created_at")
    list_filter = ("kind",)
    search_fields = ("name", "email", "message")
    date_hierarchy = "created_at"
