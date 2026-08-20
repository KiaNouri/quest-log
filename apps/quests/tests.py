from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.games.models import BacklogEntry, Game
from apps.quests.models import Challenge, Quest, QuestChallenge

User = get_user_model()


class QuestModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Doom", slug="doom")

    def test_quest_defaults_to_active(self):
        quest = Quest.objects.create(user=self.user, game=self.game)
        self.assertEqual(quest.status, Quest.Status.ACTIVE)
        self.assertIsNone(quest.completed_at)

    def test_quest_challenge_through_table_unique_together(self):
        quest = Quest.objects.create(user=self.user, game=self.game)
        challenge = Challenge.objects.create(name="No Deaths", xp_value=100)
        QuestChallenge.objects.create(quest=quest, challenge=challenge)
        with self.assertRaises(IntegrityError):
            QuestChallenge.objects.create(quest=quest, challenge=challenge)

    def test_total_xp_value_with_no_challenges(self):
        quest = Quest.objects.create(user=self.user, game=self.game)
        self.assertEqual(quest.challenge_xp_bonus, 0)
        self.assertEqual(quest.total_xp_value, Quest.COMPLETION_XP)

    def test_total_xp_value_sums_attached_challenges(self):
        quest = Quest.objects.create(user=self.user, game=self.game)
        easy = Challenge.objects.create(name="Easy one", xp_value=25)
        hard = Challenge.objects.create(name="Hard one", xp_value=75)
        QuestChallenge.objects.create(quest=quest, challenge=easy)
        QuestChallenge.objects.create(quest=quest, challenge=hard)
        self.assertEqual(quest.challenge_xp_bonus, 100)
        self.assertEqual(quest.total_xp_value, Quest.COMPLETION_XP + 100)


class QuestCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.challenge = Challenge.objects.create(name="No Deaths", xp_value=100)
        self.url = reverse("quests:create")

    def test_login_required(self):
        response = self.client.get(self.url, {"game": self.game.slug})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)

    def test_get_prefills_game_from_query_param(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"game": self.game.slug})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["game"](), self.game)

    def test_get_missing_game_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"game": "nonexijafdiustant"})
        self.assertEqual(response.status_code, 404)

    def test_post_creates_quest_owned_by_current_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, {"game": self.game.slug, "challenges": self.challenge.pk}
        )
        quest = Quest.objects.get(user=self.user, game=self.game)
        self.assertRedirects(
            response, reverse("quests:detail", kwargs={"pk": quest.pk})
        )
        self.assertTrue(
            QuestChallenge.objects.filter(quest=quest, challenge=self.challenge)
        )

    def test_post_without_chalenges_is_valid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"game": self.game.slug})
        self.assertEqual(response.status_code, 302)
        quest = Quest.objects.filter(user=self.user, game=self.game).first()
        self.assertIsNotNone(quest)
        self.assertEqual(quest.quest_challenges.count(), 0)

    def test_starting_quest_removes_game_from_backlog(self):
        self.client.force_login(self.user)
        BacklogEntry.objects.create(user=self.user, game=self.game)
        self.client.post(self.url, {"game": self.game.slug})
        self.assertFalse(
            BacklogEntry.objects.filter(user=self.user, game=self.game).exists()
        )

    def test_starting_quest_does_not_remove_other_users_backlog_entry(self):
        other_user = User.objects.create_user(
            username="other", email="other@email.com", password="testpass123"
        )
        BacklogEntry.objects.create(user=other_user, game=self.game)
        self.client.force_login(self.user)
        self.client.post(self.url, {"game": self.game.slug})
        self.assertTrue(
            BacklogEntry.objects.filter(user=other_user, game=self.game).exists()
        )

    def test_duplicate_active_quest_redirects_to_existing_instead_of_creating(self):
        self.client.force_login(self.user)
        existing = Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.ACTIVE
        )
        response = self.client.post(self.url, {"game": self.game.slug})
        self.assertEqual(
            Quest.objects.filter(user=self.user, game=self.game).count(), 1
        )
        self.assertRedirects(
            response, reverse("quests:detail", kwargs={"pk": existing.pk})
        )


class QuestListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.url = reverse("quests:list")

    def test_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "quests/quest_list.html")

    def test_empty_state_does_not_error(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["active_quests"]), [])
        self.assertEqual(list(response.context["completed_quests"]), [])

    def test_active_and_completed_split_correctly(self):
        active = Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.ACTIVE
        )
        other_game = Game.objects.create(title="Doom 2", slug="doom-2")
        completed = Quest.objects.create(
            user=self.user, game=other_game, status=Quest.Status.COMPLETED
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["active_quests"], [active])
        self.assertEqual(response.context["completed_quests"], [completed])


class QuestDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = Quest.objects.create(user=self.user, game=self.game)
        self.challenge = Challenge.objects.create(name="No Deaths", xp_value=100)
        self.quest_challenge = QuestChallenge.objects.create(
            quest=self.quest, challenge=self.challenge
        )
        self.url = reverse("quests:detail", kwargs={"pk": self.quest.pk})

    def test_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "quests/quest_detail.html")

    def test_quest_challenges_in_context(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertIn(self.quest_challenge, response.context["quest_challenges"])


class QuestAbandonViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.intruder = User.objects.create_user(username="intruder", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = Quest.objects.create(user=self.user, game=self.game)
        self.url = reverse("quests:abandon", kwargs={"pk": self.quest.pk})

    def test_login_required(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)

    def test_other_user_cannot_abandon(self):
        self.client.force_login(self.intruder)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.ACTIVE)

    def test_owner_can_abandon_active_quest(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.ABANDONED)
        self.assertRedirects(
            response, reverse("quests:detail", kwargs={"pk": self.quest.pk})
        )

    def test_abandoning_restores_backlog_entry(self):
        self.client.force_login(self.user)
        self.assertFalse(
            BacklogEntry.objects.filter(user=self.user, game=self.game).exists()
        )
        self.client.post(self.url)
        self.assertTrue(
            BacklogEntry.objects.filter(user=self.user, game=self.game).exists()
        )

    def test_abandoning_does_not_error_if_backlog_entry_already_exists(self):
        BacklogEntry.objects.create(user=self.user, game=self.game)
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            BacklogEntry.objects.filter(user=self.user, game=self.game).count(), 1
        )

    def test_cannot_abandon_completed_quest(self):
        self.quest.status = Quest.Status.COMPLETED
        self.quest.save(update_fields=["status"])
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.COMPLETED)

    def test_cannot_abandon_already_abandoned_quest(self):
        self.quest.status = Quest.Status.ABANDONED
        self.quest.save(update_fields=["status"])
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class QuestListViewAbandonedBucketTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.url = reverse("quests:list")

    def test_abandoned_quest_appears_in_abandoned_bucket_only(self):
        quest = Quest.objects.create(
            user=self.user, game=self.game, status=Quest.Status.ABANDONED
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["abandoned_quests"], [quest])
        self.assertEqual(response.context["active_quests"], [])
        self.assertEqual(response.context["completed_quests"], [])


class QuestOwnershipScopingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", email="owner@email.com", password="testpass123"
        )
        self.intruder = User.objects.create_user(
            username="intruder", email="intruder@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = Quest.objects.create(user=self.owner, game=self.game)

    def test_owner_can_view_own_quest(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("quests:detail", kwargs={"pk": self.quest.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_gets_404_not_someone_elses_quest(self):
        self.client.force_login(self.intruder)
        response = self.client.get(
            reverse("quests:detail", kwargs={"pk": self.quest.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_quest_list_only_shows_own_quests(self):
        Quest.objects.create(user=self.intruder, game=self.game)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("quests:list"))
        quests = response.context["quests"]
        self.assertEqual(list(quests), [self.quest])

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(
            reverse("quests:detail", kwargs={"pk": self.quest.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)
