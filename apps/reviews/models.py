import uuid

from django.conf import settings
from django.db import models


class Review(models.Model):
    """
    A review is a text that a user writes about a game after completing a quest
    related to that game. user also rates a game from 1 to 5.

    Each user can only write one review for one game.
    """

    class Rating(models.IntegerChoices):
        ONE = 1, "1 Star"
        TWO = 2, "2 Stars"
        THREE = 3, "3 Stars"
        FOUR = 4, "4 Stars"
        FIVE = 5, "5 Stars"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    game = models.ForeignKey(
        "games.Game", on_delete=models.CASCADE, related_name="reviews"
    )
    quest = models.OneToOneField(
        "quests.Quest", on_delete=models.CASCADE, related_name="review"
    )
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    text = models.TextField()
    hours_played = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional - hours it took to complete the quest",
    )
    xp_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("user", "game")

    def __str__(self):
        return f"{self.user.username} on {self.game.title} ({self.rating}/5)"

    # N+1 risk for properties. annotated_review_queryset() in reviews/views.py fixes
    # that for large N
    @property
    def upvote_count(self):
        return self.votes.filter(value=ReviewVote.VoteValue.UP).count()

    @property
    def downvote_count(self):
        return self.votes.filter(value=ReviewVote.VoteValue.DOWN).count()

    @property
    def net_votes(self):
        return self.upvote_count - self.downvote_count


class ReviewVote(models.Model):
    """
    Users can vote reviews. properties in `Review` model return the number of
    downvotes and upvotes from this model then `net_votes` calculates them to get the
    overall votes for a review.

    Each user can only vote a review once.
    """

    class VoteValue(models.IntegerChoices):
        UP = 1, "Upvote"
        DOWN = -1, "Downvote"

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes"
    )
    value = models.SmallIntegerField(choices=VoteValue.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("review", "user")

    def __str__(self):
        return f"{self.user.username} {self.get_value_display()} on review #{self.review_id}"
