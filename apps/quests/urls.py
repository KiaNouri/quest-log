from django.urls import path

from apps.quests.views import QuestCreateView

app_name = "quests"

urlpatterns = [
    path("create/", QuestCreateView.as_view(), name="create"),
]
