from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Every new user automatically gets an (empty) Profile."""
    if created:
        Profile.objects.get_or_create(user=instance)
