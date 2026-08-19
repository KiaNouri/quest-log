from django.urls import path

from apps.reviews.views import (
    ReviewCreateView,
    ReviewDeleteView,
    ReviewDetailView,
    ReviewListView,
)

app_name = "reviews"

urlpatterns = [
    path("", ReviewListView.as_view(), name="list"),
    path("quest/<int:quest_pk>/create/", ReviewCreateView.as_view(), name="create"),
    path("<uuid:pk>/", ReviewDetailView.as_view(), name="detail"),
    path("<uuid:pk>/delete/", ReviewDeleteView.as_view(), name="delete"),
]
