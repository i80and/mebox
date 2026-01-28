from typing import ClassVar, Tuple

from django.contrib import admin

from .models import PageRevision, UserActivity, WikiPage


@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = (
        "title",
        "author",
        "created_at",
        "updated_at",
    )
    list_filter: ClassVar[Tuple[str, ...]] = ("author", "created_at")
    search_fields: ClassVar[Tuple[str, ...]] = ("title", "content", "author__username")
    date_hierarchy: ClassVar[str] = "created_at"


@admin.register(PageRevision)
class PageRevisionAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ("page", "editor", "created_at", "is_current")
    list_filter: ClassVar[Tuple[str, ...]] = ("editor", "created_at", "is_current")
    search_fields: ClassVar[Tuple[str, ...]] = (
        "page__title",
        "editor__username",
        "content",
    )
    date_hierarchy: ClassVar[str] = "created_at"
    readonly_fields: ClassVar[Tuple[str, ...]] = ("created_at",)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ("user", "activity_type", "created_at", "page")
    list_filter: ClassVar[Tuple[str, ...]] = ("activity_type", "created_at")
    search_fields: ClassVar[Tuple[str, ...]] = (
        "user__username",
        "page__title",
        "details",
    )
    date_hierarchy: ClassVar[str] = "created_at"
    readonly_fields: ClassVar[Tuple[str, ...]] = ("created_at",)
