from django.contrib import admin
from .models import WikiPage, PageRevision, UserActivity
from typing import Tuple


@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ("title", "author", "created_at", "updated_at")
    list_filter: Tuple[str, ...] = ("author", "created_at")
    search_fields: Tuple[str, ...] = ("title", "content", "author__username")
    date_hierarchy: str = "created_at"


@admin.register(PageRevision)
class PageRevisionAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ("page", "editor", "created_at", "is_current")
    list_filter: Tuple[str, ...] = ("editor", "created_at", "is_current")
    search_fields: Tuple[str, ...] = ("page__title", "editor__username", "content")
    date_hierarchy: str = "created_at"
    readonly_fields: Tuple[str, ...] = ("created_at",)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display: Tuple[str, ...] = ("user", "activity_type", "created_at", "page")
    list_filter: Tuple[str, ...] = ("activity_type", "created_at")
    search_fields: Tuple[str, ...] = ("user__username", "page__title", "details")
    date_hierarchy: str = "created_at"
    readonly_fields: Tuple[str, ...] = ("created_at",)
