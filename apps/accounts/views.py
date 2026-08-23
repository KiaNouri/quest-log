from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView

from apps.accounts.forms import ProfileForm
from apps.accounts.models import Profile
from apps.quests.models import Quest
from apps.reviews.models import Review
from apps.reviews.views import annotated_review_queryset


class ProfileDetailView(DetailView):
    """Anyone can see anyones profile logged-in or not. Always read-only"""

    model = Profile
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile"
    slug_field = "user__username"
    slug_url_kwarg = "username"

    def get_queryset(self):
        return Profile.objects.select_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object.user

        context["completed_quest_count"] = Quest.objects.filter(
            user=profile_user, status=Quest.Status.COMPLETED
        ).count()
        context["review_count"] = Review.objects.filter(user=profile_user).count()
        context["reviews"] = (
            annotated_review_queryset()
            .filter(user=profile_user)
            .order_by("-created_at")
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Private. Deliberately ignores anyhting in URL - always operates on request.user's
    own profile (`get_object`), so only that user can edit his own profile no matter
    what they type in a URL.
    """

    model = Profile
    form_class = ProfileForm
    template_name = "accounts/profile_settings.html"

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)
