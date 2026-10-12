from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

MAX_AVATAR_MB = 2


def validate_image_size(file):
    """Reject uploads larger than MAX_AVATAR_MB."""
    if file.size > MAX_AVATAR_MB * 1024 * 1024:
        raise ValidationError(f"Image must be {MAX_AVATAR_MB} MB or smaller.")


class User(AbstractUser):
    """Custom user with a role field for role-based access control (RBAC)."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STAFF = "staff", "Staff"
        USER = "user", "General user"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER, db_index=True)

    REQUIRED_FIELDS = ["email"]  # asked for by `createsuperuser`

    def save(self, *args, **kwargs):
        # Django superusers are always Admins, so the two systems can't disagree.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def can_manage_content(self) -> bool:
        """Admins and Staff may manage events and moderate other people's posts."""
        return self.role in (self.Role.ADMIN, self.Role.STAFF)

    def __str__(self):
        return self.get_full_name() or self.username


class Profile(models.Model):
    """Extra, public-facing information about a user (created automatically)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, validators=[validate_image_size])
    bio = models.TextField(max_length=500, blank=True)
    department = models.CharField(max_length=100, blank=True)
    graduation_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)]
    )
    job_title = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__username"]

    def get_absolute_url(self):
        return reverse("accounts:profile", kwargs={"username": self.user.username})

    def __str__(self):
        return f"Profile of {self.user}"
