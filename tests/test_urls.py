"""
Test cases for wiki URLs
"""

import pytest
from django.urls import resolve, reverse


class TestURLPatterns:
    """Test URL patterns"""

    def test_home_url(self):
        """Test home URL"""
        assert reverse("home") == "/"
        assert resolve("/").func.__name__ == "home"

    def test_signup_url(self):
        """Test signup URL"""
        assert reverse("signup") == "/signup/"
        assert resolve("/signup/").func.__name__ == "signup"

    def test_login_url(self):
        """Test login URL"""
        assert reverse("login") == "/login/"
        assert resolve("/login/").func.__name__ == "user_login"

    def test_logout_url(self):
        """Test logout URL"""
        assert reverse("logout") == "/logout/"
        assert resolve("/logout/").func.__name__ == "user_logout"

    def test_create_wiki_page_url(self):
        """Test create wiki page URL"""
        assert reverse("create_wiki_page") == "/create/"
        assert resolve("/create/").func.__name__ == "create_wiki_page"

    def test_user_profile_url(self):
        """Test user profile URL"""
        assert reverse("user_profile", args=["testuser"]) == "/user/testuser/"
        assert resolve("/user/testuser/").func.__name__ == "user_profile"

    def test_user_activity_url(self):
        """Test user activity URL"""
        assert reverse("user_activity", args=["testuser"]) == "/user/testuser/activity/"
        assert resolve("/user/testuser/activity/").func.__name__ == "user_activity"

    def test_view_wiki_page_url(self):
        """Test view wiki page URL"""
        assert (
            reverse("view_wiki_page", args=["testuser", "test-page"])
            == "/user/testuser/test-page/"
        )
        assert resolve("/user/testuser/test-page/").func.__name__ == "view_wiki_page"

    def test_edit_wiki_page_url(self):
        """Test edit wiki page URL"""
        assert reverse("edit_wiki_page", args=[1]) == "/edit/1/"
        assert resolve("/edit/1/").func.__name__ == "edit_wiki_page"

    def test_delete_wiki_page_url(self):
        """Test delete wiki page URL"""
        assert reverse("delete_wiki_page", args=[1]) == "/delete/1/"
        assert resolve("/delete/1/").func.__name__ == "delete_wiki_page"

    def test_view_revisions_url(self):
        """Test view revisions URL"""
        assert reverse("view_revisions", args=[1]) == "/page/1/revisions/"
        assert resolve("/page/1/revisions/").func.__name__ == "view_revisions"

    def test_restore_revision_url(self):
        """Test restore revision URL"""
        assert (
            reverse("restore_revision", args=[1, 1]) == "/page/1/revisions/1/restore/"
        )
        assert (
            resolve("/page/1/revisions/1/restore/").func.__name__ == "restore_revision"
        )


class TestURLReversing:
    """Test URL reversing"""

    def test_all_urls_reverse_correctly(self):
        """Test that all URLs can be reversed"""
        urls_to_test = [
            ("home", []),
            ("signup", []),
            ("login", []),
            ("logout", []),
            ("create_wiki_page", []),
            ("user_profile", ["testuser"]),
            ("user_activity", ["testuser"]),
            ("view_wiki_page", ["testuser", "test-page"]),
            ("edit_wiki_page", [1]),
            ("delete_wiki_page", [1]),
            ("view_revisions", [1]),
            ("restore_revision", [1, 1]),
        ]

        for url_name, args in urls_to_test:
            try:
                reverse(url_name, args=args)
            except Exception as e:
                pytest.fail(f"URL {url_name} with args {args} failed to reverse: {e}")


class TestURLPatternsExist:
    """Test that URL patterns exist"""

    def test_all_expected_urls_exist(self):
        """Test that all expected URL patterns exist"""
        from django.urls import get_resolver

        resolver = get_resolver()

        expected_urls = [
            "home",
            "signup",
            "login",
            "logout",
            "create_wiki_page",
            "user_profile",
            "user_activity",
            "view_wiki_page",
            "edit_wiki_page",
            "delete_wiki_page",
            "view_revisions",
            "restore_revision",
        ]

        for url_name in expected_urls:
            try:
                if url_name == "view_wiki_page":
                    # view_wiki_page requires both username and page_slug
                    reverse(url_name, args=["testuser", "test-page"])
                elif url_name in ["user_profile", "user_activity"]:
                    # user_profile and user_activity require only username
                    reverse(url_name, args=["testuser"])
                elif url_name in ["edit_wiki_page", "delete_wiki_page", "view_revisions"]:
                    # These URLs require a page_id
                    reverse(url_name, args=[1])
                elif url_name == "restore_revision":
                    # restore_revision requires both page_id and revision_id
                    reverse(url_name, args=[1, 1])
                else:
                    # Other URLs don't require arguments
                    reverse(url_name, args=[])
            except Exception:
                pytest.fail(f"URL {url_name} does not exist")
