from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.games.models import Game
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


class QuestCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.challenge = Challenge.objects.create(name="No Deaths", xp_value=100)
        self.url = reverse("quests:create")

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
