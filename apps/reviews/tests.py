from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.games.models import Game
from apps.quests.models import Challenge, Quest, QuestChallenge
from apps.reviews.models import Review, ReviewVote
from apps.reviews.views import annotated_review_queryset

User = get_user_model()


def make_completed_quest(user, game, **kwargs):
    """Helper: most review tests need an already-completed quest to attach to."""
    defaults = {"status": Quest.Status.COMPLETED, "completed_at": timezone.now()}
    defaults.update(kwargs)
    return Quest.objects.create(user=user, game=game, **defaults)


class ReviewModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = make_completed_quest(self.user, self.game)

    def test_one_review_per_user_per_game(self):
        Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=5, text="Great!"
        )
        other_quest = make_completed_quest(self.user, self.game)
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                user=self.user,
                game=self.game,
                quest=other_quest,
                rating=3,
                text="Again",
            )

    def test_one_review_per_quest(self):
        # quest is a OneToOneField, so a second review can't attach to the
        # same quest even for a different game
        Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=5, text="Great!"
        )
        other_game = Game.objects.create(title="Doom 2", slug="doom-2")
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                user=self.user,
                game=other_game,
                quest=self.quest,
                rating=3,
                text="Again",
            )

    def test_vote_count_properties(self):
        review = Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=5, text="Great!"
        )
        voter1 = User.objects.create_user(username="v1", password="pw")
        voter2 = User.objects.create_user(username="v2", password="pw")
        voter3 = User.objects.create_user(username="v3", password="pw")
        ReviewVote.objects.create(
            review=review, user=voter1, value=ReviewVote.VoteValue.UP
        )
        ReviewVote.objects.create(
            review=review, user=voter2, value=ReviewVote.VoteValue.UP
        )
        ReviewVote.objects.create(
            review=review, user=voter3, value=ReviewVote.VoteValue.DOWN
        )

        self.assertEqual(review.upvote_count, 2)
        self.assertEqual(review.downvote_count, 1)
        self.assertEqual(review.net_votes, 1)


class ReviewVoteModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.voter = User.objects.create_user(username="voter", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = make_completed_quest(self.user, self.game)
        self.review = Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=5, text="Great!"
        )

    def test_one_vote_per_user_per_review(self):
        ReviewVote.objects.create(
            review=self.review, user=self.voter, value=ReviewVote.VoteValue.UP
        )
        with self.assertRaises(IntegrityError):
            ReviewVote.objects.create(
                review=self.review, user=self.voter, value=ReviewVote.VoteValue.DOWN
            )


class AnnotatedReviewQuerysetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = make_completed_quest(self.user, self.game)
        self.review = Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=4, text="Solid"
        )
        for i in range(3):
            voter = User.objects.create_user(username=f"up{i}", password="pw")
            ReviewVote.objects.create(
                review=self.review, user=voter, value=ReviewVote.VoteValue.UP
            )
        voter = User.objects.create_user(username="down0", password="pw")
        ReviewVote.objects.create(
            review=self.review, user=voter, value=ReviewVote.VoteValue.DOWN
        )

    def test_annotations_match_properties(self):
        annotated = annotated_review_queryset().get(pk=self.review.pk)
        self.assertEqual(annotated.upvote_total, 3)
        self.assertEqual(annotated.downvote_total, 1)
        self.assertEqual(annotated.vote_score, 2)
        # sanity check the annotations agree with the (slower) properties
        self.assertEqual(annotated.upvote_total, self.review.upvote_count)
        self.assertEqual(annotated.vote_score, self.review.net_votes)


class ReviewListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.other_game = Game.objects.create(title="Doom 2", slug="doom-2")
        self.url = reverse("reviews:list")

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "reviews/review_list.html")

    def test_empty_state_does_not_error(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["reviews"]), [])

    def test_filter_by_rating(self):
        quest1 = make_completed_quest(self.user, self.game)
        Review.objects.create(
            user=self.user, game=self.game, quest=quest1, rating=5, text="A"
        )
        other_user = User.objects.create_user(username="other", password="pw")
        quest2 = make_completed_quest(other_user, self.other_game)
        Review.objects.create(
            user=other_user, game=self.other_game, quest=quest2, rating=2, text="B"
        )

        response = self.client.get(self.url, {"rating": 5})
        reviews = list(response.context["reviews"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].rating, 5)

    def test_filter_by_game(self):
        quest1 = make_completed_quest(self.user, self.game)
        Review.objects.create(
            user=self.user, game=self.game, quest=quest1, rating=5, text="A"
        )
        other_user = User.objects.create_user(username="other", password="pw")
        quest2 = make_completed_quest(other_user, self.other_game)
        Review.objects.create(
            user=other_user, game=self.other_game, quest=quest2, rating=2, text="B"
        )

        response = self.client.get(self.url, {"game": self.game.slug})
        reviews = list(response.context["reviews"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].game, self.game)

    def test_sort_top_orders_by_vote_score(self):
        other_user = User.objects.create_user(username="other", password="pw")
        quest1 = make_completed_quest(self.user, self.game)
        quest2 = make_completed_quest(other_user, self.other_game)
        low_score = Review.objects.create(
            user=self.user, game=self.game, quest=quest1, rating=5, text="A"
        )
        high_score = Review.objects.create(
            user=other_user, game=self.other_game, quest=quest2, rating=5, text="B"
        )

        for i in range(3):
            voter = User.objects.create_user(username=f"v{i}", password="pw")
            ReviewVote.objects.create(
                review=high_score, user=voter, value=ReviewVote.VoteValue.UP
            )

        response = self.client.get(self.url, {"sort": "top"})
        reviews = list(response.context["reviews"])
        self.assertEqual(reviews[0], high_score)
        self.assertEqual(reviews[1], low_score)

    def test_sort_highest_rated(self):
        other_user = User.objects.create_user(username="other", password="pw")
        quest1 = make_completed_quest(self.user, self.game)
        quest2 = make_completed_quest(other_user, self.other_game)
        low = Review.objects.create(
            user=self.user, game=self.game, quest=quest1, rating=2, text="A"
        )
        high = Review.objects.create(
            user=other_user, game=self.other_game, quest=quest2, rating=5, text="B"
        )

        response = self.client.get(self.url, {"sort": "highest_rated"})
        reviews = list(response.context["reviews"])
        self.assertEqual(reviews[0], high)
        self.assertEqual(reviews[1], low)

    def test_context_includes_filter_state(self):
        response = self.client.get(
            self.url, {"rating": "4", "sort": "top", "game": self.game.slug}
        )
        self.assertEqual(response.context["current_rating"], "4")
        self.assertEqual(response.context["current_sort"], "top")
        self.assertEqual(response.context["current_game"], self.game.slug)


class ReviewDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = make_completed_quest(self.user, self.game)
        self.challenge = Challenge.objects.create(name="No Deaths", xp_value=100)
        self.quest_challenge = QuestChallenge.objects.create(
            quest=self.quest, challenge=self.challenge, completed=True
        )
        self.review = Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=5, text="Great!"
        )
        self.url = reverse("reviews:detail", kwargs={"pk": self.review.pk})

    def test_no_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "reviews/review_detail.html")

    def test_quest_challenges_in_context(self):
        response = self.client.get(self.url)
        self.assertIn(self.quest_challenge, response.context["quest_challenges"])


class ReviewCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = Quest.objects.create(user=self.user, game=self.game)  # active
        self.challenge = Challenge.objects.create(name="No Deaths", xp_value=100)
        self.quest_challenge = QuestChallenge.objects.create(
            quest=self.quest, challenge=self.challenge
        )
        self.url = reverse("reviews:create", kwargs={"quest_pk": self.quest.pk})

    def test_quest_must_belong_to_current_user(self):
        intruder = User.objects.create_user(username="intruder", password="pw")
        self.client.force_login(intruder)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_renders_form_with_quest_in_context(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["quest"], self.quest)

    def test_post_creates_review_and_completes_quest(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, {"rating": 5, "text": "Amazing game", "hours_played": 20}
        )
        review = Review.objects.get(user=self.user, game=self.game)
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": review.pk})
        )
        self.assertEqual(review.quest, self.quest)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.hours_played, 20)

        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.COMPLETED)
        self.assertIsNotNone(self.quest.completed_at)

    def test_post_marks_all_quest_challenges_completed(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"rating": 5, "text": "Amazing game"})
        self.quest_challenge.refresh_from_db()
        self.assertTrue(self.quest_challenge.completed)

    def test_post_sets_xp_awarded_on_review(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"rating": 5, "text": "Amazing game"})
        review = Review.objects.get(user=self.user, game=self.game)
        expected_xp = Quest.COMPLETION_XP + self.challenge.xp_value
        self.assertEqual(review.xp_awarded, expected_xp)

    def test_post_awards_xp_with_no_challenges_attached(self):
        # a quest with zero challenges should still award COMPLETION_XP
        bare_game = Game.objects.create(title="Doom 2", slug="doom-2")
        bare_quest = Quest.objects.create(user=self.user, game=bare_game)
        url = reverse("reviews:create", kwargs={"quest_pk": bare_quest.pk})
        self.client.force_login(self.user)
        self.client.post(url, {"rating": 5, "text": "Fine"})
        review = Review.objects.get(user=self.user, game=bare_game)
        self.assertEqual(review.xp_awarded, Quest.COMPLETION_XP)

    def test_post_increments_profile_total_xp(self):
        self.client.force_login(self.user)
        profile_before = self.user.profile.total_xp
        self.client.post(self.url, {"rating": 5, "text": "Amazing game"})
        self.user.profile.refresh_from_db()
        expected_xp = Quest.COMPLETION_XP + self.challenge.xp_value
        self.assertEqual(self.user.profile.total_xp, profile_before + expected_xp)

    def test_post_updates_profile_level_to_match_new_total_xp(self):
        from apps.accounts.models import Profile

        self.client.force_login(self.user)
        self.client.post(self.url, {"rating": 5, "text": "Amazing game"})
        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.level, Profile.level_for_xp(self.user.profile.total_xp)
        )

    def test_get_redirects_if_quest_already_has_review(self):
        review = Review.objects.create(
            user=self.user,
            game=self.game,
            quest=self.quest,
            rating=5,
            text="Already reviewed",
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": review.pk})
        )

    def test_get_redirects_if_different_quest_for_same_game_already_reviewed(self):
        other_quest = make_completed_quest(self.user, self.game)
        existing_review = Review.objects.create(
            user=self.user,
            game=self.game,
            quest=other_quest,
            rating=4,
            text="First review",
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": existing_review.pk})
        )

    def test_can_review_again_after_deleting_previous_review(self):
        # simulates: review exists for this exact quest, gets deleted, then
        # the same quest can be reviewed again
        review = Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=2, text="Meh"
        )
        review.delete()
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class ReviewDeleteViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hero", password="pw")
        self.intruder = User.objects.create_user(username="intruder", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = make_completed_quest(self.user, self.game)
        self.review = Review.objects.create(
            user=self.user, game=self.game, quest=self.quest, rating=5, text="Great!"
        )
        self.url = reverse("reviews:delete", kwargs={"pk": self.review.pk})

    def test_other_user_cannot_delete(self):
        self.client.force_login(self.intruder)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=self.review.pk).exists())

    def test_owner_can_delete(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("reviews:list"))
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())

    def test_quest_remains_completed_after_review_deleted(self):
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.COMPLETED)


class ReviewVoteViewTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="hero", password="pw")
        self.voter = User.objects.create_user(username="voter", password="pw")
        self.game = Game.objects.create(title="Doom", slug="doom")
        self.quest = make_completed_quest(self.author, self.game)
        self.review = Review.objects.create(
            user=self.author, game=self.game, quest=self.quest, rating=5, text="Great!"
        )
        self.upvote_url = reverse("reviews:upvote", kwargs={"pk": self.review.pk})
        self.downvote_url = reverse("reviews:downvote", kwargs={"pk": self.review.pk})

    def test_cannot_vote_on_own_review(self):
        self.client.force_login(self.author)
        self.client.post(self.upvote_url)
        self.assertFalse(
            ReviewVote.objects.filter(review=self.review, user=self.author).exists()
        )

    def test_upvote_creates_vote(self):
        self.client.force_login(self.voter)
        self.client.post(self.upvote_url)
        vote = ReviewVote.objects.get(review=self.review, user=self.voter)
        self.assertEqual(vote.value, ReviewVote.VoteValue.UP)

    def test_voting_same_value_again_toggles_off(self):
        self.client.force_login(self.voter)
        self.client.post(self.upvote_url)
        self.client.post(self.upvote_url)
        self.assertFalse(
            ReviewVote.objects.filter(review=self.review, user=self.voter).exists()
        )

    def test_voting_opposite_value_switches_vote(self):
        self.client.force_login(self.voter)
        self.client.post(self.upvote_url)
        self.client.post(self.downvote_url)
        vote = ReviewVote.objects.get(review=self.review, user=self.voter)
        self.assertEqual(vote.value, ReviewVote.VoteValue.DOWN)

    def test_redirects_to_next_param_when_provided(self):
        self.client.force_login(self.voter)
        response = self.client.post(self.upvote_url, {"next": "/some/other/page/"})
        self.assertRedirects(
            response, "/some/other/page/", fetch_redirect_response=False
        )

    def test_redirects_to_review_detail_by_default(self):
        self.client.force_login(self.voter)
        response = self.client.post(self.upvote_url)
        self.assertRedirects(
            response, reverse("reviews:detail", kwargs={"pk": self.review.pk})
        )
