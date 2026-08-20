from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.games.models import BacklogEntry, Game
from apps.quests.forms import QuestForm
from apps.quests.models import Quest, QuestChallenge


class QuestCreateView(LoginRequiredMixin, CreateView):
    """
    Turns a backlogged game into a quest. Expects ?game=<slug> (GET, and
    carried through as a hidden field on POST). Lets the user pick from
    existing Challenge objects.

    Removes the game related to the created quest from backlog list.
    """

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
            return redirect(existing)

        quest = Quest.objects.create(user=self.request.user, game=game)

        for challenge in form.cleaned_data["challenges"]:
            QuestChallenge.objects.create(quest=quest, challenge=challenge)

        BacklogEntry.objects.filter(user=self.request.user, game=game).delete()

        messages.success(self.request, f"Quest started for {game.title}!")
        self.object = quest
        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()


class QuestDetailView(LoginRequiredMixin, DetailView):
    """users can only ever see their own quests (404 otherwise)."""

    model = Quest
    template_name = "quests/quest_detail.html"
    context_object_name = "quest"

    def get_queryset(self):
        return Quest.objects.filter(user=self.request.user).select_related("game")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quest_challenges"] = self.object.quest_challenges.select_related(
            "challenge"
        )
        return context


class QuestListView(LoginRequiredMixin, ListView):
    """The `My Quest` tab - active and completed quests for logged-in user."""

    model = Quest
    template_name = "quests/quest_list.html"
    context_object_name = "quests"

    def get_queryset(self):
        """
        Returns only user's quests also preloads related games and challenges
        to avoud N+1 queries.

        Results are ordered by time of creation.
        """

        return (
            Quest.objects.filter(user=self.request.user)
            .select_related("game")
            .prefetch_related("quest_challenges__challenge")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quests = context["quests"]
        context["active_quests"] = [
            quest for quest in quests if quest.status == Quest.Status.ACTIVE
        ]
        context["completed_quests"] = [
            quest for quest in quests if quest.status == Quest.Status.COMPLETED
        ]
        context["abandoned_quests"] = [
            quest for quest in quests if quest.status == Quest.Status.ABANDONED
        ]
        return context


class QuestAbandonedView(LoginRequiredMixin, View):
    """
    Active quests can be abandoned. Abandoned game recreates q backlog entry if
    not there already
    """

    def post(self, request, pk):
        quest = get_object_or_404(
            Quest, pk=pk, user=request.user, status=Quest.Status.ACTIVE
        )
        quest.status = Quest.Status.ABANDONED
        quest.save(update_fields=["status"])

        BacklogEntry.objects.get_or_create(user=request.user, game=quest.game)

        messages.error(request, f"Quest abondoned for {quest.game.title}")
        return redirect(quest)
