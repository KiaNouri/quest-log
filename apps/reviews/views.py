from django.db.models import Count, F, Q
from django.views.generic import DetailView, ListView

from apps.reviews.models import Review, ReviewVote


def annotated_review_queryset():
    """
    Shared base queryset for anywhere reviews are listed.

    Annotates vote counts instead of relying on Review's properties, which each run
    their own query per row (N+1). Names are deliberately different from the property
    names to avoid clashing with them.
    """

    return (
        Review.objects.select_related("user", "user__profile", "game", "quest")
        .annotate(
            upvote_total=Count("votes", filter=Q(votes__value=ReviewVote.VoteValue.UP)),
            downvote_total=Count(
                "votes", filter=Q(votes__value=ReviewVote.VoteValue.DOWN)
            ),
        )
        .annotate(vote_score=F("upvote_total") - F("downvote_total"))
    )


SORT_OPTIONS = {
    "newest": "-created_at",
    "oldest": "created_at",
    "top": "-vote_score",
    "highest_rated": "-rating",
    "lowest_rated": "rating",
}


class ReviewListView(ListView):
    """
    The Reviews tab - all reviews, filterable by rating and game, also sortable.
    Pagination kicks after 12 reviews.
    """

    model = Review
    template_name = "reviews/review_list.html"
    context_object_name = "reviews"
    paginate_by = 12

    def get_queryset(self):
        queryset = annotated_review_queryset()

        rating = self.request.GET.get("rating")
        if rating:
            queryset = queryset.filter(rating=rating)

        game_slug = self.request.GET.get("game")
        if game_slug:
            queryset = queryset.filter(game__slug=game_slug)

        sort = self.request.GET.get("sort", "newest")
        queryset = queryset.order_by(SORT_OPTIONS.get(sort, "-created_at"))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rating_choices"] = Review.Rating.choices
        context["sort_options"] = SORT_OPTIONS.keys()
        context["current_rating"] = self.request.GET.get("rating", "")
        context["current_sort"] = self.request.GET.get("sort", "newest")
        context["current_game"] = self.request.GET.get("game", "")
        return context


class ReviewDetailView(DetailView):
    model = Review
    template_name = "reviews/review_detail.html"
    context_object_name = "review"

    def get_queryset(self):
        return annotated_review_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quest_challenges"] = self.object.quest.quest_challenges.select_related(
            "challenge"
        )
        return context
