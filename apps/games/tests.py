from django.test import TestCase
from django.urls import reverse

from apps.games.models import Game, Genre


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

    # Add test for "Add to backog" button
