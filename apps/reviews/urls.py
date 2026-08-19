from django.urls import path

from apps.reviews.models import ReviewVote
from apps.reviews.views import (
    ReviewCreateView,
    ReviewDeleteView,
    ReviewDetailView,
    ReviewListView,
    ReviewVoteView,
)

app_name = "reviews"

urlpatterns = [
    path("", ReviewListView.as_view(), name="list"),
    path("quest/<int:quest_pk>/create/", ReviewCreateView.as_view(), name="create"),
    path("<uuid:pk>/", ReviewDetailView.as_view(), name="detail"),
    path("<uuid:pk>/delete/", ReviewDeleteView.as_view(), name="delete"),
    path(
        "<uuid:pk>/upvote/",
        ReviewVoteView.as_view(vote_value=ReviewVote.VoteValue.UP),
        name="upvote",
    ),
    path(
        "<uuid:pk>/downvote/",
        ReviewVoteView.as_view(vote_value=ReviewVote.VoteValue.DOWN),
        name="downvote",
    ),
]
