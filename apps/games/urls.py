from django.urls import path

from apps.games.views import GameDetailView, GameListView

app_name = "games"

urlpatterns = [
    path("", GameListView.as_view(), name="list"),
    path("<slug:slug>/", GameDetailView.as_view(), name="detail"),
]
