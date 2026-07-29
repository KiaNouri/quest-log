from django.contrib.auth import get_user_model
from django.test import TestCase


class CuatomUserTests(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="test", email="testuser@email.com", password="testpass123"
        )
        self.assertEqual(user.username, "test")
        self.assertEqual(user.email, "testuser@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        super_user = User.objects.create_superuser(
            username="superuser", email="superuser@email.com", password="testpass123"
        )
        self.assertEqual(super_user.username, "superuser")
        self.assertEqual(super_user.email, "superuser@email.com")
        self.assertTrue(super_user.is_active)
        self.assertTrue(super_user.is_staff)
        self.assertTrue(super_user.is_superuser)
