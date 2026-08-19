from django.contrib import admin

from apps.reviews.models import Review, ReviewVote


class ReviewVoteInline(admin.TabularInline):
    model = ReviewVote
    extra = 0
    readonly_fields = ("user", "value", "created_at")
    can_delete = False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "game",
        "user",
        "rating",
        "net_votes_display",
        "hours_played",
        "created_at",
    )
    list_select_related = ("game", "user")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "game__title")
    raw_id_fields = ("user", "game", "quest")
    inlines = (ReviewVoteInline,)

    @admin.display(description="Net Vote")
    def net_votes_display(self, obj):
        return obj.net_votes


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "user", "value", "created_at")
    list_select_related = ("review__game", "user")
    list_filter = ("value", "created_at")
    search_fields = ("user__username", "review__game__title")
    raw_id_fields = ("review", "user")
