from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.games.models import BacklogEntry, Game, Genre

User = get_user_model()


class GameModelTests(TestCase):
    def test_slug_auto_generated_from_title_plus_year(self):
        game = Game.objects.create(title="Elden Ring", published_year=2022)
        self.assertEqual(game.slug, "elden-ring-2022")

    def test_same_titles_and_years_get_unique_slugs(self):
        game1 = Game.objects.create(title="Piece by Piece", published_year=2026)
        game2 = Game.objects.create(title="Piece by Piece", published_year=2026)
        self.assertEqual(game1.slug, "piece-by-piece-2026")
        self.assertEqual(game2.slug, "piece-by-piece-2026-1")

    def test_str_returns_title(self):
        game = Game.objects.create(title="Hollow Knight")
        self.assertEqual(str(game), "Hollow Knight")

    def test_game_can_have_multiple_genres(self):
        game = Game.objects.create(title="Baldur's Gate")
        rpg = Genre.objects.create(name="RPG")
        turn_based = Genre.objects.create(name="Turn Based")
        game.genres.add(rpg, turn_based)
        self.assertEqual(game.genres.count(), 2)


class GenreModelTests(TestCase):
    def test_slug_auto_generated_from_name(self):
        genre = Genre.objects.create(name="Action")
        self.assertEqual(genre.slug, "action")

    def test_str_returns_title(self):
        genre = Genre.objects.create(name="Strategy")
        self.assertEqual(str(genre), "Strategy")


class GameListViewTests(TestCase):
    def setUp(self):
        self.rpg = Genre.objects.create(name="RPG", slug="rpg")
        self.shooter = Genre.objects.create(name="Shooter", slug="shooter")

        self.elden_ring = Game.objects.create(
            title="Elden Ring",
            developer="FromSoftware",
            publisher="Bandai Namco Entertainment",
        )
        self.doom = Game.objects.create(
            title="Doom",
            developer="id Software",
            publisher="Sega",
        )

        self.elden_ring.genres.add(self.rpg)
        self.doom.genres.add(self.shooter)

    def test_list_view_status_code(self):
        response = self.client.get(reverse("games:list"))
        self.assertEqual(response.status_code, 200)

    def test_list_view_shows_all_games_by_default(self):
        response = self.client.get(reverse("games:list"))
        self.assertContains(response, "Elden Ring")
        self.assertContains(response, "Doom")

    def test_search_filters_by_title(self):
        response = self.client.get(reverse("games:list"), {"q": "elden"})
        self.assertContains(response, "Elden Ring")
        self.assertNotContains(response, "Doom")

    def test_search_filters_by_developer(self):
        response = self.client.get(reverse("games:list"), {"q": "from"})
        self.assertContains(response, "Elden Ring")
        self.assertNotContains(response, "Doom")

    def test_search_filters_by_publisher(self):
        response = self.client.get(reverse("games:list"), {"q": "seg"})
        self.assertContains(response, "Doom")
        self.assertNotContains(response, "Elden Ring")

    def test_search_no_results(self):
        response = self.client.get(reverse("games:list"), {"q": "kkajgpuadnfhuj"})
        self.assertContains(response, "No games found")
        self.assertNotContains(response, "Doom")

    def test_genre_filter(self):
        response = self.client.get(reverse("games:list"), {"genre": "rpg"})
        self.assertContains(response, "Elden Ring")
        self.assertNotContains(response, "Doom")

    def test_paginate_starts_past_page_size(self):
        for i in range(25):
            Game.objects.create(title=f"Test Game {i}")

        response = self.client.get(reverse("games:list"))
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["games"]), 20)


class GameDetailViewTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(
            title="Elden Ring",
            developer="FromSoftware",
            publisher="Bandai Namco",
            published_year=2022,
            story_summary="This is a summary",
        )

    def test_detail_view_status_code(self):
        response = self.client.get(
            reverse("games:detail", kwargs={"slug": self.game.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_view_shows_game_info(self):
        response = self.client.get(
            reverse("games:detail", kwargs={"slug": self.game.slug})
        )
        self.assertContains(response, "Elden Ring")
        self.assertContains(response, "FromSoftware")
        self.assertContains(response, "2022")
        self.assertContains(response, "This is a summary")

    def test_detail_view_404_for_invalid_slug(self):
        response = self.client.get(
            reverse("games:detail", kwargs={"slug": "does-not-exist"})
        )
        self.assertEqual(response.status_code, 404)


# Remember to add tests for log/comleted/active tabs that will be added later
class BacklogListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="test2", email="test2@email.com", password="testpass123"
        )

        self.game1 = Game.objects.create(title="Elden Ring")
        self.game2 = Game.objects.create(title="Hollow Knight")
        self.game3 = Game.objects.create(title="Celeste")

        self.url = reverse("games:backlog")

    def test_backlog_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_empty_backlog_shows_empty_state(self):
        self.client.login(username="test", password="testpass123")
        response = self.client.get(self.url)
        self.assertContains(response, "Nothing here yet")

    def test_user_only_sees_own_backlog_entries(self):
        BacklogEntry.objects.create(user=self.user, game=self.game1)
        BacklogEntry.objects.create(user=self.other_user, game=self.game2)

        self.client.login(username="test", password="testpass123")
        response = self.client.get(self.url)

        titles = [entry.game.title for entry in response.context["entries"]]
        self.assertIn("Elden Ring", titles)
        self.assertNotIn("Hollow Knight", titles)

    def test_backlog_ordered_most_recently_added_first(self):
        BacklogEntry.objects.create(user=self.user, game=self.game1)
        BacklogEntry.objects.create(user=self.user, game=self.game2)
        BacklogEntry.objects.create(user=self.user, game=self.game3)

        self.client.login(username="test", password="testpass123")
        response = self.client.get(self.url)

        titles = [entry.game.title for entry in response.context["entries"]]
        self.assertEqual(titles, ["Celeste", "Hollow Knight", "Elden Ring"])


class AddToBacklogViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.game = Game.objects.create(title="Elden Ring")

        self.url = reverse("games:backlog-add", kwargs={"slug": self.game.slug})

    def test_add_to_backlog_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_add_to_backlog_creates_entry(self):
        self.client.login(username="test", password="testpass123")
        self.client.post(self.url)

        self.assertTrue(
            BacklogEntry.objects.filter(user=self.user, game=self.game).exists()
        )

    def test_add_to_backlog_shows_success_message(self):
        self.client.login(username="test", password="testpass123")
        response = self.client.post(self.url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("added to your backlog", str(messages[0]))

    def test_adding_same_game_twice_does_not_duplicate(self):
        self.client.login(username="test", password="testpass123")
        self.client.post(self.url)
        self.client.post(self.url)

        self.assertEqual(
            BacklogEntry.objects.filter(user=self.user, game=self.game).count(), 1
        )

    def test_adding_same_game_twice_shows_info_message(self):
        self.client.login(username="test", password="testpass123")

        self.client.post(self.url)
        response = self.client.post(self.url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertIn("already in your backlog", str(messages[-1]))

    def test_add_to_backlog_404_for_invalid_slug(self):
        self.client.login(username="test", password="testpass123")
        response = self.client.post(
            reverse("games:backlog-add", kwargs={"slug": "nonexjnqafijnistent"})
        )
        self.assertEqual(response.status_code, 404)

    def test_add_to_backlog_redirects_to_next_if_provided(self):
        self.client.login(username="test", password="testpass123")
        response = self.client.post(
            self.url,
            data={"next": reverse("games:detail", kwargs={"slug": self.game.slug})},
        )
        self.assertRedirects(
            response, reverse("games:detail", kwargs={"slug": self.game.slug})
        )


class BacklogRemoveViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@email.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="test2", email="test2@email.com", password="testpass123"
        )

        self.game = Game.objects.create(title="Elden Ring")
        self.entry = BacklogEntry.objects.create(user=self.user, game=self.game)
        self.url = reverse("games:backlog-remove", kwargs={"pk": self.entry.pk})

    def test_user_can_remove_own_backlog_entry(self):
        self.client.login(username="test", password="testpass123")

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("games:backlog"))
        self.assertFalse(BacklogEntry.objects.filter(pk=self.entry.pk).exists())

    def test_remove_creates_success_message(self):
        self.client.login(username="test", password="testpass123")

        response = self.client.post(self.url, follow=True)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn("removed from your backlog", str(messages[0]))

    def test_user_cannot_remove_another_users_entry(self):
        self.client.login(username="test2", password="testpass123")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(BacklogEntry.objects.filter(pk=self.entry.pk).exists())

    def test_anonymous_user_cannot_remove_entry(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(BacklogEntry.objects.filter(pk=self.entry.pk).exists())
