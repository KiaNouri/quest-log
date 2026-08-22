from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from apps.games.models import BacklogEntry, Game
from apps.pages.views import DashboardPageView, IntroPageView
from apps.quests.models import Quest
from apps.reviews.models import Review

User = get_user_model()


class IntroPageTest(SimpleTestCase):
    def setUp(self):
        url = reverse("pages:intro")
        self.response = self.client.get(url)

    def test_intropage_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_intropage_template(self):
        self.assertTemplateUsed(self.response, "pages/intro.html")

    def test_intropage_contains_correct_html(self):
        self.assertContains(self.response, "Your backlog, gamified")

    def test_intropage_url_resolves_intropageview(self):
        view = resolve("/")
        self.assertEqual(view.func.view_class, IntroPageView)


class DashboardPageViewAccessTests(TestCase):
    def setUp(self):
        self.url = reverse("pages:dashboard")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)

    def test_logged_in_user_gets_200(self):
        user = User.objects.create_user(username="hero", password="pw")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        user = User.objects.create_user(username="hero", password="pw")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "pages/dashboard.html")


class DashboardPageViewContextTests(TestCase):
    """
    Every count/queryset in context must be scoped to the logged-in user
    only — the other_user fixtures exist specifically to catch leakage.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.other_user = User.objects.create_user(username="rival", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.other_game = Game.objects.create(title="Doom 2", slug="doom-2")
        self.url = reverse("pages:dashboard")
        self.client.force_login(self.user)

    def test_profile_in_context_is_current_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["profile"], self.user.profile)

    def test_backlog_count_scoped_to_current_user(self):
        BacklogEntry.objects.create(user=self.user, game=self.game)
        BacklogEntry.objects.create(user=self.other_user, game=self.other_game)
        response = self.client.get(self.url)
        self.assertEqual(response.context["backlog_count"], 1)

    def test_active_quest_count_scoped_to_current_user(self):
        Quest.objects.create(user=self.user, game=self.game, status=Quest.Status.ACTIVE)
        Quest.objects.create(
            user=self.other_user, game=self.other_game, status=Quest.Status.ACTIVE
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["active_quest_count"], 1)

    def test_completed_quest_count_scoped_to_current_user(self):
        Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.COMPLETED
        )
        Quest.objects.create(
            user=self.other_user, game=self.other_game, status=Quest.Status.COMPLETED
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["completed_quest_count"], 1)

    def test_active_quests_excludes_completed_and_abandoned(self):
        active = Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.ACTIVE
        )
        Quest.objects.create(
            user=self.user,
            game=Game.objects.create(title="Doom 3", slug="doom-3"),
            status=Quest.Status.COMPLETED,
        )
        Quest.objects.create(
            user=self.user,
            game=Game.objects.create(title="Doom 4", slug="doom-4"),
            status=Quest.Status.ABANDONED,
        )
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["active_quests"]), [active])

    def test_active_quests_excludes_other_users(self):
        Quest.objects.create(
            user=self.other_user, game=self.other_game, status=Quest.Status.ACTIVE
        )
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["active_quests"]), [])

    def test_review_count_scoped_to_current_user(self):
        quest = Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.COMPLETED
        )
        Review.objects.create(
            user=self.user, game=self.game, quest=quest, rating=5, text="Great"
        )

        other_quest = Quest.objects.create(
            user=self.other_user, game=self.other_game, status=Quest.Status.COMPLETED
        )
        Review.objects.create(
            user=self.other_user,
            game=self.other_game,
            quest=other_quest,
            rating=3,
            text="Meh",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context["review_count"], 1)

    def test_recent_reviews_limited_to_three(self):
        for i in range(5):
            game = Game.objects.create(title=f"Game {i}", slug=f"game-{i}")
            quest = Quest.objects.create(
                user=self.user, game=game, status=Quest.Status.COMPLETED
            )
            Review.objects.create(
                user=self.user, game=game, quest=quest, rating=4, text=f"Review {i}"
            )
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["recent_reviews"]), 3)
        self.assertEqual(response.context["review_count"], 5)

    def test_recent_reviews_excludes_other_users(self):
        other_quest = Quest.objects.create(
            user=self.other_user, game=self.other_game, status=Quest.Status.COMPLETED
        )
        Review.objects.create(
            user=self.other_user,
            game=self.other_game,
            quest=other_quest,
            rating=3,
            text="Meh",
        )
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["recent_reviews"]), [])


class DashboardNudgeRenderingTests(TestCase):
    """Integration-style checks that the right nudge card actually renders."""

    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.url = reverse("pages:dashboard")
        self.client.force_login(self.user)

    def test_shows_start_quest_nudge_when_backlog_nonempty_and_no_active_quest(self):
        BacklogEntry.objects.create(user=self.user, game=self.game)
        response = self.client.get(self.url)
        self.assertContains(response, "Start a quest")

    def test_shows_browse_games_nudge_when_totally_empty(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Browse games")

    def test_no_nudge_when_user_has_active_quest(self):
        BacklogEntry.objects.create(user=self.user, game=self.game)
        Quest.objects.create(
            user=self.user,
            game=Game.objects.create(title="Doom 2", slug="doom-2"),
            status=Quest.Status.ACTIVE,
        )
        response = self.client.get(self.url)
        self.assertNotContains(response, "Start a quest")
        self.assertNotContains(response, "Browse games")


class XPProgressTests(TestCase):
    """
    Tests DashboardPageView._xp_progress directly against a real Profile, since
    the math depends on Profile.level being correctly recomputed from
    total_xp on save (per the save() override added alongside the XP logic).
    """

    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.profile = self.user.profile

    def _set_xp(self, amount):
        self.profile.total_xp = amount
        self.profile.save()  # recomputes level via the model's save() override
        self.profile.refresh_from_db()
        return self.profile

    def test_zero_xp_at_level_one(self):
        profile = self._set_xp(0)
        result = DashboardPageView._xp_progress(profile)
        self.assertEqual(profile.level, 1)
        self.assertEqual(result["xp_progress_percent"], 0)
        self.assertEqual(result["xp_to_next_level"], 100)

    def test_halfway_through_level_one(self):
        profile = self._set_xp(50)
        result = DashboardPageView._xp_progress(profile)
        self.assertEqual(result["xp_progress_percent"], 50)
        self.assertEqual(result["xp_to_next_level"], 50)

    def test_exactly_at_level_two_threshold(self):
        profile = self._set_xp(100)
        result = DashboardPageView._xp_progress(profile)
        self.assertEqual(profile.level, 2)
        self.assertEqual(result["xp_progress_percent"], 0)
        self.assertEqual(result["xp_to_next_level"], 300)  # next threshold (400) - 100

    def test_partway_through_level_two(self):
        profile = self._set_xp(250)  # halfway between 100 and 400
        result = DashboardPageView._xp_progress(profile)
        self.assertEqual(profile.level, 2)
        self.assertEqual(result["xp_progress_percent"], 50)
        self.assertEqual(result["xp_to_next_level"], 150)

    def test_progress_percent_never_exceeds_100(self):
        profile = self._set_xp(99999)
        result = DashboardPageView._xp_progress(profile)
        self.assertLessEqual(result["xp_progress_percent"], 100)

    def test_progress_percent_never_below_zero(self):
        profile = self._set_xp(0)
        result = DashboardPageView._xp_progress(profile)
        self.assertGreaterEqual(result["xp_progress_percent"], 0)
