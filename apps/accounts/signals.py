from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


# create a profile for new users
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile when a User is created.
    """

    if created:
        Profile.objects.create(user=instance)
