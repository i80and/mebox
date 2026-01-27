"""
Test cases for admin interface
"""

import pytest
from django.contrib.admin.sites import AdminSite
from wiki.admin import WikiPageAdmin, PageRevisionAdmin, UserActivityAdmin
from wiki.models import WikiPage, PageRevision, UserActivity


class TestAdminInterfaces:
    """Test admin interfaces"""

    def test_wikipage_admin_list_display(self):
        """Test WikiPageAdmin list_display"""
        assert "title" in WikiPageAdmin.list_display
        assert "author" in WikiPageAdmin.list_display
        assert "created_at" in WikiPageAdmin.list_display
        assert "updated_at" in WikiPageAdmin.list_display

    def test_wikipage_admin_list_filter(self):
        """Test WikiPageAdmin list_filter"""
        assert "author" in WikiPageAdmin.list_filter
        assert "created_at" in WikiPageAdmin.list_filter

    def test_wikipage_admin_search_fields(self):
        """Test WikiPageAdmin search_fields"""
        assert "title" in WikiPageAdmin.search_fields
        assert "content" in WikiPageAdmin.search_fields
        assert "author__username" in WikiPageAdmin.search_fields

    def test_pagerevision_admin_list_display(self):
        """Test PageRevisionAdmin list_display"""
        assert "page" in PageRevisionAdmin.list_display
        assert "editor" in PageRevisionAdmin.list_display
        assert "created_at" in PageRevisionAdmin.list_display
        assert "is_current" in PageRevisionAdmin.list_display

    def test_pagerevision_admin_list_filter(self):
        """Test PageRevisionAdmin list_filter"""
        assert "editor" in PageRevisionAdmin.list_filter
        assert "created_at" in PageRevisionAdmin.list_filter
        assert "is_current" in PageRevisionAdmin.list_filter

    def test_pagerevision_admin_search_fields(self):
        """Test PageRevisionAdmin search_fields"""
        assert "page__title" in PageRevisionAdmin.search_fields
        assert "editor__username" in PageRevisionAdmin.search_fields
        assert "content" in PageRevisionAdmin.search_fields

    def test_useractivity_admin_list_display(self):
        """Test UserActivityAdmin list_display"""
        assert "user" in UserActivityAdmin.list_display
        assert "activity_type" in UserActivityAdmin.list_display
        assert "created_at" in UserActivityAdmin.list_display
        assert "page" in UserActivityAdmin.list_display

    def test_useractivity_admin_list_filter(self):
        """Test UserActivityAdmin list_filter"""
        assert "activity_type" in UserActivityAdmin.list_filter
        assert "created_at" in UserActivityAdmin.list_filter

    def test_useractivity_admin_search_fields(self):
        """Test UserActivityAdmin search_fields"""
        assert "user__username" in UserActivityAdmin.search_fields
        assert "page__title" in UserActivityAdmin.search_fields
        assert "details" in UserActivityAdmin.search_fields


class TestAdminViews:
    """Test admin views"""

    def test_admin_wikipage_list(self, logged_in_admin_client):
        """Test WikiPage admin list view"""
        response = logged_in_admin_client.get("/admin/wiki/wikipage/")
        assert response.status_code == 200

    def test_admin_pagerevision_list(self, logged_in_admin_client):
        """Test PageRevision admin list view"""
        response = logged_in_admin_client.get("/admin/wiki/pagerevision/")
        assert response.status_code == 200

    def test_admin_useractivity_list(self, logged_in_admin_client):
        """Test UserActivity admin list view"""
        response = logged_in_admin_client.get("/admin/wiki/useractivity/")
        assert response.status_code == 200

    def test_admin_wikipage_add(self, logged_in_admin_client, user):
        """Test WikiPage admin add view"""
        response = logged_in_admin_client.get("/admin/wiki/wikipage/add/")
        assert response.status_code == 200

    def test_admin_pagerevision_add(self, logged_in_admin_client, user, wiki_page):
        """Test PageRevision admin add view"""
        response = logged_in_admin_client.get("/admin/wiki/pagerevision/add/")
        assert response.status_code == 200

    def test_admin_useractivity_add(self, logged_in_admin_client, user):
        """Test UserActivity admin add view"""
        response = logged_in_admin_client.get("/admin/wiki/useractivity/add/")
        assert response.status_code == 200


class TestAdminPermissions:
    """Test admin permissions"""

    def test_regular_user_cannot_access_admin(self, logged_in_client):
        """Test that regular users cannot access admin"""
        response = logged_in_client.get("/admin/")
        assert response.status_code == 302  # Redirect to login

    def test_admin_user_can_access_admin(self, logged_in_admin_client):
        """Test that admin users can access admin"""
        response = logged_in_admin_client.get("/admin/")
        assert response.status_code == 200

    def test_admin_user_can_access_wiki_models(self, logged_in_admin_client):
        """Test that admin users can access wiki models"""
        models = ["wikipage", "pagerevision", "useractivity"]
        for model in models:
            response = logged_in_admin_client.get(f"/admin/wiki/{model}/")
            assert response.status_code == 200, f"Failed for model {model}"


class TestAdminModelActions:
    """Test admin model actions"""

    def test_admin_can_create_wikipage(self, logged_in_admin_client, user):
        """Test that admin can create WikiPage"""
        initial_count = WikiPage.objects.count()

        response = logged_in_admin_client.post(
            "/admin/wiki/wikipage/add/",
            {
                "title": "Admin Created Page",
                "content": "# Admin Content",
                "author": user.id,
                "slug": "admin-created-page",
            },
        )

        assert response.status_code == 302
        assert WikiPage.objects.count() == initial_count + 1

    def test_admin_can_create_pagerevision(
        self, logged_in_admin_client, user, wiki_page
    ):
        """Test that admin can create PageRevision"""
        initial_count = PageRevision.objects.count()

        response = logged_in_admin_client.post(
            "/admin/wiki/pagerevision/add/",
            {
                "page": wiki_page.id,
                "title": "Revision Title",
                "content": "# Revision Content",
                "editor": user.id,
                "is_current": True,
            },
        )

        assert response.status_code == 302
        assert PageRevision.objects.count() == initial_count + 1

    def test_admin_can_create_useractivity(self, logged_in_admin_client, user):
        """Test that admin can create UserActivity"""
        initial_count = UserActivity.objects.count()

        response = logged_in_admin_client.post(
            "/admin/wiki/useractivity/add/",
            {
                "user": user.id,
                "activity_type": "create_page",
                "details": "Admin created activity",
            },
        )

        assert response.status_code == 302
        assert UserActivity.objects.count() == initial_count + 1
