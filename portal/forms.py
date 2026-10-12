from django import forms

from accounts.forms import TailwindFormMixin

from .models import Event, JobPost

DATETIME_LOCAL = "%Y-%m-%dT%H:%M"  # format produced by <input type="datetime-local">


class JobPostForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ("title", "company", "location", "job_type", "description", "apply_url", "contact_email", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 7})}


class EventForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = ("title", "description", "location", "start_at", "end_at", "cover_image")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_LOCAL),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_LOCAL),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("start_at", "end_at"):
            self.fields[name].input_formats = [DATETIME_LOCAL]
