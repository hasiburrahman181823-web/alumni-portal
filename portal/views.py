from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import OwnerOrStaffMixin, StaffRequiredMixin
from accounts.models import User

from .forms import EventForm, JobPostForm
from .models import Event, JobPost


def home(request):
    """Landing page: public hero + live numbers; latest items only for signed-in users."""
    now = timezone.now()
    ctx = {
        "alumni_count": User.objects.filter(is_active=True).count(),
        "job_count": JobPost.objects.filter(is_active=True).count(),
        "event_count": Event.objects.filter(start_at__gte=now).count(),
    }
    if request.user.is_authenticated:
        ctx["latest_jobs"] = JobPost.objects.filter(is_active=True).select_related("posted_by")[:5]
        ctx["upcoming_events"] = Event.objects.filter(start_at__gte=now)[:4]
    return render(request, "home.html", ctx)


# ----------------------------------------------------------------------------
# Jobs: any signed-in user can post; only the owner / Staff / Admin can edit or delete
# ----------------------------------------------------------------------------
class JobListView(LoginRequiredMixin, ListView):
    template_name = "portal/job_list.html"
    context_object_name = "jobs"
    paginate_by = 9

    def get_queryset(self):
        qs = JobPost.objects.select_related("posted_by")
        params = self.request.GET
        if params.get("mine") == "1":
            qs = qs.filter(posted_by=self.request.user)  # includes the user's closed posts
        else:
            qs = qs.filter(is_active=True)
        if q := params.get("q", "").strip():
            qs = qs.filter(Q(title__icontains=q) | Q(company__icontains=q) | Q(description__icontains=q))
        if job_type := params.get("type"):
            if job_type in JobPost.JobType.values:
                qs = qs.filter(job_type=job_type)
        if location := params.get("location", "").strip():
            qs = qs.filter(location__icontains=location)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            job_types=JobPost.JobType.choices,
            q=self.request.GET.get("q", ""),
            selected_type=self.request.GET.get("type", ""),
            location=self.request.GET.get("location", ""),
            mine=self.request.GET.get("mine") == "1",
        )
        return ctx


class JobDetailView(LoginRequiredMixin, DetailView):
    model = JobPost
    template_name = "portal/job_detail.html"
    context_object_name = "job"

    def get_object(self, queryset=None):
        job = super().get_object(queryset)
        user = self.request.user
        # Closed posts are visible only to their owner and to Staff/Admin.
        if not job.is_active and not (user.can_manage_content or job.posted_by_id == user.id):
            raise Http404("This job is no longer available.")
        return job


class JobCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JobPost
    form_class = JobPostForm
    template_name = "form.html"
    success_message = "Your job post is live."
    extra_context = {"title": "Post a job", "submit_label": "Publish job", "cancel_url": reverse_lazy("portal:job_list")}

    def form_valid(self, form):
        form.instance.posted_by = self.request.user  # never trust the client for ownership
        return super().form_valid(form)


class JobUpdateView(OwnerOrStaffMixin, SuccessMessageMixin, UpdateView):
    model = JobPost
    form_class = JobPostForm
    template_name = "form.html"
    success_message = "Job post updated."
    extra_context = {"title": "Edit job post", "submit_label": "Save changes", "cancel_url": reverse_lazy("portal:job_list")}


class JobDeleteView(OwnerOrStaffMixin, SuccessMessageMixin, DeleteView):
    model = JobPost
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("portal:job_list")
    success_message = "Job post deleted."


# ----------------------------------------------------------------------------
# Events: everyone signed-in can read; only Staff/Admin can create, edit, delete
# ----------------------------------------------------------------------------
class EventListView(LoginRequiredMixin, ListView):
    template_name = "portal/event_list.html"
    context_object_name = "events"
    paginate_by = 9

    def get_queryset(self):
        qs = Event.objects.all()
        now = timezone.now()
        when = self.request.GET.get("when", "upcoming")
        if when == "past":
            qs = qs.filter(start_at__lt=now).order_by("-start_at")
        elif when == "upcoming":
            qs = qs.filter(start_at__gte=now)
        if q := self.request.GET.get("q", "").strip():
            qs = qs.filter(Q(title__icontains=q) | Q(location__icontains=q) | Q(description__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["when"] = self.request.GET.get("when", "upcoming")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "portal/event_detail.html"
    context_object_name = "event"


class EventCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "form.html"
    success_message = "Event created."
    extra_context = {"title": "Create an event", "submit_label": "Create event", "cancel_url": reverse_lazy("portal:event_list")}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EventUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "form.html"
    success_message = "Event updated."
    extra_context = {"title": "Edit event", "submit_label": "Save changes", "cancel_url": reverse_lazy("portal:event_list")}


class EventDeleteView(StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Event
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("portal:event_list")
    success_message = "Event deleted."
