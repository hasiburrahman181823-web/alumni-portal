from rest_framework import filters, generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Profile
from .serializers import AlumniSerializer, AvatarSerializer, RegisterSerializer, UserSerializer


class RegisterAPIView(generics.CreateAPIView):
    """POST /api/auth/register/ -> creates a General user and returns an auth token."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        data = {"user": UserSerializer(user, context={"request": request}).data, "token": token.key}
        return Response(data, status=status.HTTP_201_CREATED)


class MeAPIView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/me/ -> the logged-in user's account + profile."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class AvatarUploadAPIView(generics.UpdateAPIView):
    """PUT/PATCH /api/me/avatar/ (multipart form, field name `avatar`)."""

    serializer_class = AvatarSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.profile


class AlumniViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only alumni directory with ?search=, ?graduation_year=, ?department=."""

    queryset = Profile.objects.select_related("user").filter(user__is_active=True)
    serializer_class = AlumniSerializer
    filterset_fields = ["graduation_year", "department"]
    search_fields = ["user__first_name", "user__last_name", "user__username", "company", "job_title"]
    ordering_fields = ["graduation_year", "user__first_name"]
