from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView

from apps.games.models import BacklogEntry, Game, Genre


class GameListView(ListView):
    """
    Displays games with optional genre, title, developer and
    publisher filtering.

    Results are ordered alphabetically and paginated to 20 games.
    """

    model = Game
    template_name = "games/game_list.html"
    context_object_name = "games"
    paginate_by = 20

    def get_queryset(self):
        queryset = Game.objects.all().order_by("title")

        genre = self.request.GET.get("genre")
        if genre:
            queryset = queryset.filter(genres__slug=genre)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(developer__icontains=query)
                | Q(publisher__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_genres"] = Genre.objects.all()
        return context


class GameDetailView(DetailView):
    model = Game
    template_name = "games/game_detail.html"
    context_object_name = "game"


class AddToBacklogView(LoginRequiredMixin, View):
    """
    Adds selected game to backlog.

    Returns a message if games added susccefully or already added.
    """

    def post(self, request, slug):
        game = get_object_or_404(Game, slug=slug)
        entry, created = BacklogEntry.objects.get_or_create(
            user=request.user, game=game
        )

        if created:
            messages.success(request, f"{entry.game.title} added to your backlog.")
        else:
            messages.info(request, f"{entry.game.title} is already in your backlog.")

        return redirect(request.POST.get("next") or reverse("games:backlog"))


class BacklogListView(LoginRequiredMixin, ListView):
    model = BacklogEntry
    template_name = "games/backlog_list.html"
    context_object_name = "entries"

    def get_queryset(self):
        """
        Return only the current user's backlog entries and preload
        related games to avoid N+1 queries.

        Results are ordered based on time added
        """

        return (
            BacklogEntry.objects.filter(user=self.request.user)
            .select_related("game")
            .order_by("-added_at")
        )

    # add code for filtering based on quest completion status and tests for it


class BacklogRemoveView(LoginRequiredMixin, DeleteView):
    model = BacklogEntry
    success_url = reverse_lazy("games:backlog")

    def get_queryset(self):
        """Each logged in user can only remove their own games"""
        return BacklogEntry.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.error(
            self.request, f"{self.object.game.title} was removed from your backlog"
        )
        return super().form_valid(form)
