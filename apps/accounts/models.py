import math

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F


class CustomUser(AbstractUser):
    pass


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @staticmethod
    def level_for_xp(total_xp):
        """Calculates level based on the XP given to it."""
        return math.floor(math.sqrt(total_xp / 100)) + 1

    def add_xp(self, amount):
        """
        The only method that should ever change `total_xp`. Uses an `F()`
        expression so concurrent XP awards to the same profile don't lose
        an increment to a race condition (read-modify-write on total_xp
        directly would be vulnerable to that).
        """
        if amount < 0:
            raise ValueError("XP amount must be positive")
        Profile.objects.filter(pk=self.pk).update(total_xp=F("total_xp") + amount)
        self.refresh_from_db(fields=["total_xp"])
        self.level = self.level_for_xp(self.total_xp)
        self.save(update_fields=["level"])
        return self.level

    def save(self, *args, **kwargs):
        # Redundant but guarantees level can never drift out of sync with `total_xp`,
        # even if someone hand-edits `total_xp` from django admin.
        self.level = self.level_for_xp(self.total_xp)
        super().save(*args, **kwargs)
