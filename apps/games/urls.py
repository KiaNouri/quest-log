from django.urls import path

from apps.games.views import GameListView

app_name = "games"

urlpatterns = [
    path("", GameListView.as_view(), name="list"),
    # detail view here
]
