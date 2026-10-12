from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import validate_image_size


class JobPost(models.Model):
    """A job or internship opening shared by an alumnus. Owned by whoever posted it."""

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    title = models.CharField(max_length=150)
    company = models.CharField(max_length=120)
    location = models.CharField(max_length=120)
    job_type = models.CharField(max_length=12, choices=JobType.choices, default=JobType.FULL_TIME)
    description = models.TextField()
    apply_url = models.URLField("Application link", blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField("Accepting applications", default=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "-created_at"])]

    def clean(self):
        if not self.apply_url and not self.contact_email:
            raise ValidationError("Provide an application link or a contact email so people can apply.")

    def get_absolute_url(self):
        return reverse("portal:job_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.title} at {self.company}"


class Event(models.Model):
    """Reunions, webinars, meetups. Created and managed by Staff/Admin only."""

    title = models.CharField(max_length=150)
    description = models.TextField()
    location = models.CharField(max_length=150)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    cover_image = models.ImageField(upload_to="events/%Y/%m/", blank=True, validators=[validate_image_size])
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="events_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]

    def clean(self):
        if self.end_at and self.start_at and self.end_at < self.start_at:
            raise ValidationError({"end_at": "The end time must be after the start time."})

    @property
    def is_upcoming(self) -> bool:
        return self.start_at >= timezone.now()

    def get_absolute_url(self):
        return reverse("portal:event_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return self.title
