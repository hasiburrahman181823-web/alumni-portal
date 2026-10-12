from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either the username or the email address (case-insensitive)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        username = username or kwargs.get(User.USERNAME_FIELD)
        if not username or not password:
            return None
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            User().set_password(password)  # run the hasher anyway to mask timing differences
            return None
        except MultipleObjectsReturned:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
