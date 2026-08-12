from django.contrib import admin

from apps.games.models import BacklogEntry, Game, Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "game_count")
    search_fields = ("name", "slug")
    readonly_fields = ("slug",)

    @admin.display(description="Total Games")
    def game_count(self, obj):
        return obj.games.count()


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "published_year",
        "developer",
        "get_genres",
        "has_external_id",
    )
    list_filter = ("published_year", "genres")
    search_fields = ("title", "slug", "developer")
    readonly_fields = ("slug",)
    filter_horizontal = ("genres",)
    fieldsets = (
        (
            "Basic Info",
            {"fields": ("title", "slug", "published_year", "genres", "story_summary")},
        ),
        ("Industry Details", {"fields": ("developer", "publisher")}),
        (
            "Media & External Sync",
            {
                "fields": ("cover_image_url", "external_id"),
            },
        ),
    )

    @admin.display(boolean=True, description="From API")
    def has_external_id(self, obj):
        return bool(obj.external_id)

    @admin.display(description="Genres")
    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()]) or "-"


@admin.register(BacklogEntry)
class BacklogAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "added_at")
    search_fields = ("user__username", "game__title")
