from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.quests.models import Quest
from apps.reviews.forms import ReviewForm
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
    """Review detail page - also shows the related completed quest."""

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


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """
    Reviewing a quest is the only way to complete it.

    Tied to a specific quest via URL so the review can only be written by that quest's
    owner for that quest.

    Form gets the user, game, quest from this view by overrided `form_valid()`. also
    updates the status and time of completion for that quest
    """

    model = Review
    form_class = ReviewForm
    template_name = "reviews/review_create.html"

    def get_quest(self):
        return get_object_or_404(
            Quest, pk=self.kwargs["quest_pk"], user=self.request.user
        )

    def dispatch(self, request, *args, **kwargs):
        self.quest = self.get_quest()

        # If this quest already has a review redirect them to that review detail instead
        # of letting it double submit.
        if hasattr(self.quest, "review"):
            return redirect(self.quest.review)

        # If a diffrent quest for the same game already has a review, since each game
        # can only have one review per user (`unique together` in reviews/models.py),
        # they have to delete that review first rather than getting an IntegrityError.
        existing_review = Review.objects.filter(
            user=request.user, game=self.quest.game
        ).first()
        if existing_review:
            messages.info(
                request,
                f"You've already reviewed {self.quest.game.title}. "
                "Delete your existing review to write a new one.",
            )
            return redirect(existing_review)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quest"] = self.quest
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.game = self.quest.game
        form.instance.quest = self.quest
        response = super().form_valid(form)

        self.quest.status = Quest.Status.COMPLETED
        self.quest.completed_at = timezone.now()
        self.quest.save(update_fields=["status", "completed_at"])
        self.quest.quest_challenges.update(completed=True)

        messages.success(self.request, "Review submitted and quest completed!")
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()
