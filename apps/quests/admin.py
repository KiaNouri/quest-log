from django.contrib import admin

from apps.quests.models import Challenge, Quest, QuestChallenge


class QuestChallengeInline(admin.TabularInline):
    model = QuestChallenge
    extra = 1


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("name", "difficulty", "xp_value")
    list_filter = ("difficulty",)
    search_fields = ("name",)


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "status", "created_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("user__username", "game__title")
    inlines = (QuestChallengeInline,)
