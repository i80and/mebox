"""
Test cases for wiki views
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from wiki.models import PageRevision, UserActivity, WikiPage


class TestAuthenticationViews:
    """Test authentication views with activity tracking"""

    @pytest.mark.django_db
    def test_signup_creates_activity(self, client):
        """Test that signup creates UserActivity"""
        response = client.post(
            "/signup/",
            {
                "username": "newuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        assert response.status_code == 302
        assert UserActivity.objects.filter(activity_type="signup").exists()

    @pytest.mark.django_db
    def test_signup_redirects_to_home(self, client):
        """Test that signup redirects to home after success"""
        response = client.post(
            "/signup/",
            {
                "username": "newuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        assert response.status_code == 302
        assert response.url == "/"

    @pytest.mark.django_db
    def test_login_creates_activity(self, client, user):
        """Test that login creates UserActivity"""
        response = client.post(
            "/login/", {"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 302
        assert UserActivity.objects.filter(activity_type="login").exists()

    def test_login_redirects_to_home(self, client, user):
        """Test that login redirects to home after success"""
        response = client.post(
            "/login/", {"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_logout_redirects_to_home(self, logged_in_client):
        """Test that logout redirects to home"""
        response = logged_in_client.post("/logout/")
        assert response.status_code == 302
        assert response.url == "/"


class TestWikiPageViews:
    """Test wiki page views"""

    @pytest.mark.django_db
    def test_home_page_works(self, client):
        """Test that home page loads"""
        response = client.get("/")
        assert response.status_code == 200

    def test_signup_page_works(self, client):
        """Test that signup page loads"""
        response = client.get("/signup/")
        assert response.status_code == 200

    def test_login_page_works(self, client):
        """Test that login page loads"""
        response = client.get("/login/")
        assert response.status_code == 200

    def test_create_page_requires_login(self, client):
        """Test that create page requires login"""
        response = client.get("/create/")
        assert response.status_code == 302  # Redirect to login

    def test_create_page_works_for_logged_in_user(self, logged_in_client):
        """Test that create page works for logged in users"""
        response = logged_in_client.get("/create/")
        assert response.status_code == 200

    def test_user_profile_works(self, logged_in_client, user):
        """Test that user profile page works"""
        response = logged_in_client.get(f"/user/{user.username}/")
        assert response.status_code == 200

    def test_view_wiki_page_works(self, logged_in_client, wiki_page, user):
        """Test that viewing a wiki page works"""
        response = logged_in_client.get(f"/user/{user.username}/{wiki_page.slug}/")
        assert response.status_code == 200
        assert wiki_page.title.encode() in response.content


class TestPageCreation:
    """Test page creation functionality"""

    def test_create_wiki_page_creates_revision(self, logged_in_client):
        """Test that creating a page creates initial revision"""
        response = logged_in_client.post(
            "/create/", {"title": "Test Page", "content": "# Test Content"}
        )
        assert response.status_code == 302
        page = WikiPage.objects.get(title="Test Page")
        assert PageRevision.objects.filter(page=page, is_current=True).exists()

    def test_create_wiki_page_creates_activity(self, logged_in_client):
        """Test that creating a page logs activity"""
        response = logged_in_client.post(
            "/create/", {"title": "Test Page", "content": "# Test Content"}
        )
        assert response.status_code == 302
        assert UserActivity.objects.filter(activity_type="create_page").exists()

    def test_create_page_redirects_to_profile(self, logged_in_client, user):
        """Test that create page redirects to user profile"""
        response = logged_in_client.post(
            "/create/", {"title": "Test Page", "content": "# Test Content"}
        )
        assert response.status_code == 302
        assert response.url == f"/user/{user.username}/"


class TestPageEditing:
    """Test page editing functionality"""

    def test_edit_page_requires_login(self, client, wiki_page):
        """Test that edit page requires login"""
        response = client.get(f"/edit/{wiki_page.id}/")
        assert response.status_code == 302  # Redirect to login

    def test_edit_page_works_for_owner(self, logged_in_client, wiki_page, user):
        """Test that edit page works for page owner"""
        response = logged_in_client.get(f"/edit/{wiki_page.id}/")
        assert response.status_code == 200

    def test_edit_page_creates_new_revision(self, logged_in_client, wiki_page, user):
        """Test that editing a page creates new revision"""
        initial_revisions = PageRevision.objects.filter(page=wiki_page).count()

        response = logged_in_client.post(
            f"/edit/{wiki_page.id}/",
            {"title": "Updated Page", "content": "# Updated Content"},
        )

        assert response.status_code == 302
        assert (
            PageRevision.objects.filter(page=wiki_page).count() == initial_revisions + 1
        )

        # Check that new revision is current
        current_revision = PageRevision.objects.filter(
            page=wiki_page, is_current=True
        ).first()
        assert current_revision is not None
        assert current_revision.content == "# Updated Content"

    def test_edit_page_logs_activity(self, logged_in_client, wiki_page):
        """Test that editing a page logs activity"""
        initial_activities = UserActivity.objects.filter(
            activity_type="edit_page"
        ).count()

        response = logged_in_client.post(
            f"/edit/{wiki_page.id}/",
            {"title": "Updated Page", "content": "# Updated Content"},
        )

        assert response.status_code == 302
        assert (
            UserActivity.objects.filter(activity_type="edit_page").count()
            == initial_activities + 1
        )

    def test_edit_page_redirects_to_profile(self, logged_in_client, wiki_page, user):
        """Test that edit page redirects to user profile"""
        response = logged_in_client.post(
            f"/edit/{wiki_page.id}/",
            {"title": "Updated Page", "content": "# Updated Content"},
        )
        assert response.status_code == 302
        assert response.url == f"/user/{user.username}/"


class TestPageDeletion:
    """Test page deletion functionality"""

    def test_delete_page_requires_login(self, client, wiki_page):
        """Test that delete page requires login"""
        response = client.get(f"/delete/{wiki_page.id}/")
        assert response.status_code == 302  # Redirect to login

    def test_delete_page_works_for_owner(self, logged_in_client, wiki_page):
        """Test that delete page works for page owner"""
        response = logged_in_client.get(f"/delete/{wiki_page.id}/")
        assert response.status_code == 200

    def test_delete_page_removes_page(self, logged_in_client, wiki_page):
        """Test that delete page removes the page"""
        page_id = wiki_page.id
        response = logged_in_client.post(f"/delete/{wiki_page.id}/")

        assert response.status_code == 302
        assert not WikiPage.objects.filter(id=page_id).exists()

    def test_delete_page_logs_activity(self, logged_in_client, wiki_page):
        """Test that deleting a page logs activity"""
        initial_activities = UserActivity.objects.filter(
            activity_type="delete_page"
        ).count()

        response = logged_in_client.post(f"/delete/{wiki_page.id}/")

        assert response.status_code == 302
        assert (
            UserActivity.objects.filter(activity_type="delete_page").count()
            == initial_activities + 1
        )

    def test_delete_page_redirects_to_profile(self, logged_in_client, wiki_page, user):
        """Test that delete page redirects to user profile"""
        response = logged_in_client.post(f"/delete/{wiki_page.id}/")
        assert response.status_code == 302
        assert response.url == f"/user/{user.username}/"


class TestRevisionViews:
    """Test revision-related views"""

    def test_view_revisions_requires_login(self, client, wiki_page):
        """Test that view revisions requires login"""
        response = client.get(f"/page/{wiki_page.id}/revisions/")
        assert response.status_code == 302  # Redirect to login

    def test_view_revisions_works_for_owner(
        self, logged_in_client, wiki_page, page_revision
    ):
        """Test that view revisions works for page owner"""
        response = logged_in_client.get(f"/page/{wiki_page.id}/revisions/")
        assert response.status_code == 200
        assert b"Revision History" in response.content

    def test_view_revisions_shows_all_revisions(
        self, logged_in_client, wiki_page, user
    ):
        """Test that view revisions shows all revisions"""
        # Create multiple revisions
        PageRevision.objects.create(
            page=wiki_page,
            title="Version 1",
            content="# Version 1",
            editor=user,
            is_current=False,
        )
        PageRevision.objects.create(
            page=wiki_page,
            title="Version 2",
            content="# Version 2",
            editor=user,
            is_current=True,
        )

        response = logged_in_client.get(f"/page/{wiki_page.id}/revisions/")
        assert response.status_code == 200
        assert b"Version 1" in response.content
        assert b"Version 2" in response.content


class TestRevisionRestoration:
    """Test revision restoration functionality"""

    def test_restore_revision_requires_login(self, client, wiki_page, page_revision):
        """Test that restore revision requires login"""
        response = client.post(
            f"/page/{wiki_page.id}/revisions/{page_revision.id}/restore/"
        )
        assert response.status_code == 302  # Redirect to login

    def test_restore_revision_works_for_owner(
        self, logged_in_client, wiki_page, page_revision
    ):
        """Test that restore revision works for page owner"""
        # First, create a new version
        wiki_page.content = "# New Version"
        wiki_page.save()
        new_revision = PageRevision.objects.create(
            page=wiki_page,
            title="New Version",
            content="# New Version",
            editor=page_revision.editor,
            is_current=True,
        )

        # Now restore the old revision
        response = logged_in_client.post(
            f"/page/{wiki_page.id}/revisions/{page_revision.id}/restore/"
        )
        assert response.status_code == 302

        # Check that page content was restored
        wiki_page.refresh_from_db()
        assert wiki_page.content == page_revision.content

        # Check that new revision is marked as current
        current_revision = PageRevision.objects.filter(
            page=wiki_page, is_current=True
        ).first()
        assert current_revision.content == page_revision.content

    def test_restore_revision_logs_activity(
        self, logged_in_client, wiki_page, page_revision
    ):
        """Test that restoring a revision logs activity"""
        initial_activities = UserActivity.objects.filter(
            activity_type="edit_page"
        ).count()

        response = logged_in_client.post(
            f"/page/{wiki_page.id}/revisions/{page_revision.id}/restore/"
        )

        assert response.status_code == 302
        assert (
            UserActivity.objects.filter(activity_type="edit_page").count()
            == initial_activities + 1
        )

    def test_restore_revision_redirects_to_page(
        self, logged_in_client, wiki_page, page_revision, user
    ):
        """Test that restore revision redirects to the page"""
        response = logged_in_client.post(
            f"/page/{wiki_page.id}/revisions/{page_revision.id}/restore/"
        )
        assert response.status_code == 302
        assert response.url == f"/user/{user.username}/{wiki_page.slug}/"


class TestActivityViews:
    """Test user activity views"""

    def test_user_activity_requires_login(self, client, user):
        """Test that user activity requires login"""
        response = client.get(f"/user/{user.username}/activity/")
        assert response.status_code == 302  # Redirect to login

    def test_user_activity_works_for_logged_in_user(
        self, logged_in_client, user, user_activity
    ):
        """Test that user activity works for logged in users"""
        response = logged_in_client.get(f"/user/{user.username}/activity/")
        assert response.status_code == 200
        assert b"Recent Activity" in response.content

    def test_user_activity_shows_all_activities(self, logged_in_client, user):
        """Test that user activity shows all activities"""
        UserActivity.objects.create(
            user=user, activity_type="login", details="User logged in"
        )
        UserActivity.objects.create(
            user=user, activity_type="create_page", details="User created page"
        )

        response = logged_in_client.get(f"/user/{user.username}/activity/")
        assert response.status_code == 200
        assert b"User logged in" in response.content
        assert b"User created page" in response.content


class TestPermissionChecks:
    """Test permission checks in views"""

    def test_user_cannot_edit_other_users_pages(
        self, logged_in_client, second_user, wiki_page
    ):
        """Test that users cannot edit other users' pages"""
        # Create a page owned by second_user
        second_page = WikiPage.objects.create(
            title="Second User Page", content="# Content", author=second_user
        )

        response = logged_in_client.get(f"/edit/{second_page.id}/")
        assert response.status_code == 302  # Redirect to their own profile

    def test_user_cannot_delete_other_users_pages(
        self, logged_in_client, second_user, wiki_page
    ):
        """Test that users cannot delete other users' pages"""
        # Create a page owned by second_user
        second_page = WikiPage.objects.create(
            title="Second User Page", content="# Content", author=second_user
        )

        response = logged_in_client.get(f"/delete/{second_page.id}/")
        assert response.status_code == 302  # Redirect to their own profile

    def test_user_cannot_view_other_users_revisions(
        self, logged_in_client, second_user, wiki_page, page_revision
    ):
        """Test that users cannot view other users' revisions"""
        # Create a page owned by second_user
        second_page = WikiPage.objects.create(
            title="Second User Page", content="# Content", author=second_user
        )
        second_revision = PageRevision.objects.create(
            page=second_page,
            title="Second User Page",
            content="# Content",
            editor=second_user,
            is_current=True,
        )

        response = logged_in_client.get(f"/page/{second_page.id}/revisions/")
        assert response.status_code == 302  # Redirect to their own profile

    def test_user_cannot_restore_other_users_revisions(
        self, logged_in_client, second_user, wiki_page, page_revision
    ):
        """Test that users cannot restore other users' revisions"""
        # Create a page owned by second_user
        second_page = WikiPage.objects.create(
            title="Second User Page", content="# Content", author=second_user
        )
        second_revision = PageRevision.objects.create(
            page=second_page,
            title="Second User Page",
            content="# Content",
            editor=second_user,
            is_current=True,
        )

        response = logged_in_client.post(
            f"/page/{second_page.id}/revisions/{second_revision.id}/restore/"
        )
        assert response.status_code == 302  # Redirect to their own profile
