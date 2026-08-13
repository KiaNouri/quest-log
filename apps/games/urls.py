from django.urls import path

from apps.games.views import (
    AddToBacklogView,
    BacklogListView,
    BacklogRemoveView,
    GameDetailView,
    GameListView,
)

app_name = "games"

urlpatterns = [
    path("", GameListView.as_view(), name="list"),
    path("backlog/", BacklogListView.as_view(), name="backlog"),
    path("backlog/add/<slug:slug>/", AddToBacklogView.as_view(), name="backlog-add"),
    path(
        "backlog/remove/<int:pk>/",
        BacklogRemoveView.as_view(),
        name="backlog-remove",
    ),
    path("<slug:slug>/", GameDetailView.as_view(), name="detail"),
]
