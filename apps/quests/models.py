from django.conf import settings
from django.db import models
from django.urls import reverse


class Challenge(models.Model):
    """
    A challenge that can be added to quests.

    challenges are categorized by their difficulty (easy, medium, hard).

    `xp_value` can only be changed by admin. real xp calculation will be done
    after user submits a review
    """

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    xp_value = models.PositiveIntegerField(default=50)

    class Meta:
        ordering = ("difficulty", "name")

    def __str__(self):
        return self.name


class Quest(models.Model):
    """
    A user's quest for a specfic game.

    A quest belongs to one user and one game and may contain zero or more
    challenges. Challenge completion is tracked separately through the
    QuestChallenge model.

    A quest can be active or completed or abandoned. `compeleted_at` stores
    the time of completion.

    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quests"
    )
    game = models.ForeignKey(
        "games.Game", on_delete=models.CASCADE, related_name="quests"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    challenges = models.ManyToManyField(Challenge, through="QuestChallenge", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} - {self.game.title} ({self.status})"

    def get_absolute_url(self):
        return reverse("quests:detail", kwargs={"pk": self.pk})


class QuestChallenge(models.Model):
    """
    Associates a challenge with a quest and tracks its completion

    The same challenge cannot be added to the same quest more than once.

    completion is tracked here because a challenge may be completed in
    one quest but incomplete in another
    """

    quest = models.ForeignKey(
        Quest, on_delete=models.CASCADE, related_name="quest_challenges"
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="quest_challenges"
    )
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("quest", "challenge")

    def __str__(self):
        return f"{self.quest} - {self.challenge}"
