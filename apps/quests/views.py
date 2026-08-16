from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView

from apps.games.models import Game
from apps.quests.forms import QuestForm
from apps.quests.models import Quest, QuestChallenge


class QuestCreateView(LoginRequiredMixin, CreateView):
    model = Quest
    form_class = QuestForm
    template_name = "quests/quest_create.html"

    def get_game(self):
        game_slug = self.request.GET.get("game") or self.request.POST.get("game")
        return get_object_or_404(Game, slug=game_slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["game"] = self.get_game
        return context

    def form_valid(self, form):
        game = self.get_game()

        existing = Quest.objects.filter(
            user=self.request.user, game=game, status=Quest.Status.ACTIVE
        ).first()
        if existing:
            messages.info(
                self.request, f"You already have an active quest for {game.title}."
            )
            return redirect("quests:detail", pk=existing.pk)

        quest = Quest.objects.create(user=self.request.user, game=game)

        for challenge in form.cleaned_data["challenges"]:
            QuestChallenge.objects.create(quest=quest, challenge=challenge)

        messages.success(self.request, f"Quest started for {game.title}!")
        self.object = quest
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("quests:detail", kwargs={"pk": self.object.pk})
