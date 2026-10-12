from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets

from accounts.permissions import IsOwnerOrStaffOrReadOnly, IsStaffRoleOrReadOnly

from .models import Event, JobPost
from .serializers import EventSerializer, JobPostSerializer


class JobPostViewSet(viewsets.ModelViewSet):
    """
    /api/jobs/   ?search= ?job_type= ?location= ?ordering=-created_at
    Any authenticated user may create; only owner/Staff/Admin may modify or delete.
    """

    serializer_class = JobPostSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    filterset_fields = ["job_type", "location", "is_active"]
    search_fields = ["title", "company", "location", "description"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        qs = JobPost.objects.select_related("posted_by")
        user = self.request.user
        if user.can_manage_content:
            return qs
        return qs.filter(Q(is_active=True) | Q(posted_by=user))  # closed posts: owner only

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)


class EventViewSet(viewsets.ModelViewSet):
    """/api/events/  ?when=upcoming|past ?search=   (writes: Staff/Admin only)"""

    serializer_class = EventSerializer
    permission_classes = [IsStaffRoleOrReadOnly]
    filterset_fields = ["location"]
    search_fields = ["title", "location", "description"]
    ordering_fields = ["start_at"]

    def get_queryset(self):
        qs = Event.objects.select_related("created_by")
        when = self.request.query_params.get("when")
        if when == "upcoming":
            qs = qs.filter(start_at__gte=timezone.now())
        elif when == "past":
            qs = qs.filter(start_at__lt=timezone.now())
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
