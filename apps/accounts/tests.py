from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Profile
from apps.games.models import Game
from apps.quests.models import Quest
from apps.reviews.models import Review

User = get_user_model()

# Smallest possible valid GIF — used to test image upload without needing a
# real image file on disk.
TINY_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


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


class ProfileDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.other_user = User.objects.create_user(username="rival", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.url = reverse("accounts:detail", kwargs={"username": self.user.username})

    def test_no_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "accounts/profile_detail.html")

    def test_404_for_nonexistent_username(self):
        response = self.client.get(
            reverse("accounts:detail", kwargs={"username": "nobody"})
        )
        self.assertEqual(response.status_code, 404)

    def test_context_profile_matches_url_username(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["profile"], self.user.profile)

    def test_completed_quest_count_scoped_to_profile_user(self):
        Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.COMPLETED
        )
        Quest.objects.create(
            user=self.other_user,
            game=Game.objects.create(title="Doom 2", slug="doom-2"),
            status=Quest.Status.COMPLETED,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["completed_quest_count"], 1)

    def test_review_count_and_reviews_scoped_to_profile_user(self):
        quest = Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.COMPLETED
        )
        review = Review.objects.create(
            user=self.user, game=self.game, quest=quest, rating=5, text="Great"
        )

        other_quest = Quest.objects.create(
            user=self.other_user,
            game=Game.objects.create(title="Doom 3", slug="doom-3"),
            status=Quest.Status.COMPLETED,
        )
        Review.objects.create(
            user=self.other_user,
            game=other_quest.game,
            quest=other_quest,
            rating=2,
            text="Meh",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context["review_count"], 1)
        self.assertEqual(list(response.context["reviews"]), [review])

    def test_edit_button_shown_to_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Edit Profile")

    def test_edit_button_hidden_from_other_users(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertNotContains(response, "Edit Profile")

    def test_edit_button_hidden_from_anonymous_visitors(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, "Edit Profile")


class ProfileUpdateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.other_user = User.objects.create_user(username="rival", password="pw")
        self.url = reverse("accounts:settings")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)

    def test_get_returns_current_users_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["object"], self.user.profile)

    def test_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "accounts/profile_settings.html")

    def test_post_updates_bio(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"bio": "I like retro shooters."})
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "I like retro shooters.")

    def test_post_redirects_to_own_profile_detail(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"bio": "Hello"})
        self.assertRedirects(
            response,
            reverse("accounts:detail", kwargs={"username": self.user.username}),
        )

    def test_editing_never_affects_another_users_profile(self):
        # This test onfirms two different logged-in users editing only
        # ever touch their own profile.
        self.client.force_login(self.user)
        self.client.post(self.url, {"bio": "Hero's bio"})

        self.client.force_login(self.other_user)
        self.client.post(self.url, {"bio": "Rival's bio"})

        self.user.profile.refresh_from_db()
        self.other_user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Hero's bio")
        self.assertEqual(self.other_user.profile.bio, "Rival's bio")

    def test_total_xp_and_level_are_not_editable_via_form(self):
        self.client.force_login(self.user)
        original_xp = self.user.profile.total_xp
        original_level = self.user.profile.level
        self.client.post(
            self.url, {"bio": "trying to cheat", "total_xp": 99999, "level": 50}
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.total_xp, original_xp)
        self.assertEqual(self.user.profile.level, original_level)

    def test_bio_over_max_length_is_rejected(self):
        self.client.force_login(self.user)
        too_long = "x" * 301
        response = self.client.post(self.url, {"bio": too_long})
        self.assertEqual(
            response.status_code, 200
        )  # re-rendered with errors, not redirected
        self.assertTrue(response.context["form"].errors)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "")

    def test_profile_picture_upload(self):
        self.client.force_login(self.user)
        image = SimpleUploadedFile("avatar.gif", TINY_GIF, content_type="image/gif")
        self.client.post(self.url, {"bio": "", "profile_picture": image})
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture)
        self.assertIn(f"user_{self.user.pk}", self.user.profile.profile_picture.name)

    def test_non_image_file_upload_is_rejected(self):
        self.client.force_login(self.user)
        bad_file = SimpleUploadedFile(
            "not_an_image.txt", b"just some text", content_type="text/plain"
        )
        response = self.client.post(self.url, {"bio": "", "profile_picture": bad_file})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.profile_picture)
