from django.contrib import admin
from .models import WikiPage, PageRevision, UserActivity

@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at')
    list_filter = ('author', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    date_hierarchy = 'created_at'

@admin.register(PageRevision)
class PageRevisionAdmin(admin.ModelAdmin):
    list_display = ('page', 'editor', 'created_at', 'is_current')
    list_filter = ('editor', 'created_at', 'is_current')
    search_fields = ('page__title', 'editor__username', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'created_at', 'page')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'page__title', 'details')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
