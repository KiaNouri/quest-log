from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Profile

User = get_user_model()


class CuatomUserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="test", email="testuser@email.com", password="testpass123"
        )
        self.assertEqual(user.username, "test")
        self.assertEqual(user.email, "testuser@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        super_user = User.objects.create_superuser(
            username="superuser", email="superuser@email.com", password="testpass123"
        )
        self.assertEqual(super_user.username, "superuser")
        self.assertEqual(super_user.email, "superuser@email.com")
        self.assertTrue(super_user.is_active)
        self.assertTrue(super_user.is_staff)
        self.assertTrue(super_user.is_superuser)


class ProfileModelTests(TestCase):
    def test_profile_created_automatically_on_user_creation(self):
        """Post_save signal should create a profile right after creation"""
        user = User.objects.create_user(
            username="test", email="testuser@email.com", password="testpass123"
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_defaults(self):
        """New profile should start at level 1 with 0 XP"""
        user = User.objects.create_user(
            username="test", email="testuser@email.com", password="testpass123"
        )
        profile = user.profile
        self.assertEqual(profile.total_xp, 0)
        self.assertEqual(profile.level, 1)

    def test_deleting_user_deletes_profile(self):
        """on_delete=CASCADE should delete profile too"""
        user = User.objects.create_user(
            username="test", email="testuser@email.com", password="testpass123"
        )
        profile_id = user.profile.id
        user.delete()
        self.assertFalse(Profile.objects.filter(id=profile_id).exists())
