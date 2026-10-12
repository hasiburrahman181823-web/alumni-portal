"""All REST API routes live under /api/."""
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from accounts.api import AlumniViewSet, AvatarUploadAPIView, MeAPIView, RegisterAPIView
from portal.api import EventViewSet, JobPostViewSet

router = DefaultRouter()
router.register("jobs", JobPostViewSet, basename="job")
router.register("events", EventViewSet, basename="event")
router.register("alumni", AlumniViewSet, basename="alumni")

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="api-register"),
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("me/", MeAPIView.as_view(), name="api-me"),
    path("me/avatar/", AvatarUploadAPIView.as_view(), name="api-me-avatar"),
    path("", include(router.urls)),
]
