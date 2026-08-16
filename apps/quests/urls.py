from django.urls import path

from apps.quests.views import QuestCreateView, QuestDetailView, QuestListView

app_name = "quests"

urlpatterns = [
    path("create/", QuestCreateView.as_view(), name="create"),
    path("", QuestListView.as_view(), name="list"),
    path("<int:pk>/", QuestDetailView.as_view(), name="detail"),
]
