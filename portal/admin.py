from django.contrib import admin

from .models import Event, JobPost


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "job_type", "is_active", "posted_by", "created_at")
    list_filter = ("job_type", "is_active")
    search_fields = ("title", "company", "location")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "start_at", "created_by")
    list_filter = ("start_at",)
    search_fields = ("title", "location")
