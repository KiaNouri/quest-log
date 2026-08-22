from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.games.models import BacklogEntry
from apps.quests.models import Quest
from apps.reviews.models import Review
from apps.reviews.views import annotated_review_queryset


class IntroPageView(TemplateView):
    template_name = "pages/intro.html"


class DashboardPageView(LoginRequiredMixin, TemplateView):
    """
    The logged-in landing page

    Always request.user's own data; never takes a username/pk from the URL
    (that's what the public Profile page is for).
    """

    template_name = "pages/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.profile

        context["profile"] = profile
        context.update(self._xp_progress(profile))

        context["active_quests"] = (
            Quest.objects.filter(user=user, status=Quest.Status.ACTIVE)
            .select_related("game")
            .order_by("-created_at")
        )
        context["active_quest_count"] = Quest.objects.filter(
            user=user, status=Quest.Status.ACTIVE
        ).count()
        context["completed_quest_count"] = Quest.objects.filter(
            user=user, status=Quest.Status.COMPLETED
        ).count()
        context["backlog_count"] = BacklogEntry.objects.filter(user=user).count()

        user_reviews = (
            annotated_review_queryset().filter(user=user).order_by("-created_at")
        )
        context["recent_reviews"] = user_reviews[:3]
        context["review_count"] = Review.objects.filter(user=user).count()

        return context

    @staticmethod
    def _xp_progress(profile):
        level = profile.level
        current_threshold = ((level - 1) ** 2) * 100
        next_threshold = (level**2) * 100
        xp_needed = next_threshold - current_threshold
        xp_into_level = profile.total_xp - current_threshold

        percent = int((xp_into_level / xp_needed) * 100) if xp_needed else 100
        # Percent never drops below 0 or exceeds 100
        percent = min(max(percent, 0), 100)

        return {
            "xp_progress_percent": percent,
            "xp_to_next_level": max(next_threshold - profile.total_xp, 0),
        }
