from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    # Jobs
    path("jobs/", views.JobListView.as_view(), name="job_list"),
    path("jobs/new/", views.JobCreateView.as_view(), name="job_create"),
    path("jobs/<int:pk>/", views.JobDetailView.as_view(), name="job_detail"),
    path("jobs/<int:pk>/edit/", views.JobUpdateView.as_view(), name="job_update"),
    path("jobs/<int:pk>/delete/", views.JobDeleteView.as_view(), name="job_delete"),
    # Events
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("events/new/", views.EventCreateView.as_view(), name="event_create"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_update"),
    path("events/<int:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),
]
