from django.db.models import Q
from django.views.generic import ListView

from apps.games.models import Game, Genre


class GameListView(ListView):
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
