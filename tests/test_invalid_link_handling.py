"""
Test cases for invalid wiki link handling
"""

import pytest
from django.contrib.auth.models import User
from wiki.models import WikiPage


class TestInvalidLinkHandling:
    """Test handling of invalid wiki links"""

    def test_invalid_same_user_link_redirects_to_create(self, client, db):
        """Test that invalid same-user links redirect to create page"""
        # Create and login a user
        user = User.objects.create_user(username="testuser", password="testpass")
        client.login(username="testuser", password="testpass")

        # Create a page with an invalid link
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="This has an [[invalid_link]]",
            author=user,
        )

        # View the page
        response = client.get(f"/user/{user.username}/{page.slug}/")
        assert response.status_code == 200

        # The link should be marked as invalid
        assert 'class="wiki-link-invalid"' in response.content.decode()

        # Now try to access the invalid link directly
        response = client.get(f"/user/{user.username}/invalid_link/create/")

        # Should redirect to create page
        assert response.status_code in [301, 302, 303]
        assert "/create/" in response.url

    def test_invalid_cross_user_link_returns_404(self, client, db):
        """Test that invalid cross-user links return 404"""
        # Create and login a user
        user1 = User.objects.create_user(username="user1", password="testpass")
        user2 = User.objects.create_user(username="user2", password="testpass")
        client.login(username="user1", password="testpass")

        # Create a page with an invalid cross-user link
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="This has a [[User:user2/nonexistent]] link",
            author=user1,
        )

        # View the page
        response = client.get(f"/user/{user1.username}/{page.slug}/")
        assert response.status_code == 200

        # The link should be marked as invalid
        content = response.content.decode()
        assert 'class="wiki-link-invalid"' in content
        assert 'data-wiki-username="user2"' in content

        # Try to access the invalid cross-user link directly
        response = client.get(f"/user/user2/nonexistent/")

        # Should return 404
        assert response.status_code == 404

    def test_valid_cross_user_link_works(self, client, db):
        """Test that valid cross-user links work correctly"""
        # Create two users
        user1 = User.objects.create_user(username="user1", password="testpass")
        user2 = User.objects.create_user(username="user2", password="testpass")
        client.login(username="user1", password="testpass")

        # Create a page for user2
        target_page = WikiPage.objects.create(
            title="Target Page",
            slug="target_page",
            content="# Target Content",
            author=user2,
        )

        # Create a page for user1 that links to user2's page
        source_page = WikiPage.objects.create(
            title="Source Page",
            slug="source_page",
            content="Link to [[User:user2/target_page]]",
            author=user1,
        )

        # View the source page
        response = client.get(f"/user/{user1.username}/{source_page.slug}/")
        assert response.status_code == 200

        # The link should be marked as valid
        assert 'class="wiki-link-valid"' in response.content.decode()

        # Access the cross-user link
        response = client.get(f"/user/user2/target_page/")
        assert response.status_code == 200
        assert b"Target Content" in response.content

    def test_invalid_same_user_link_with_display_text(self, client, db):
        """Test that invalid same-user links with display text work correctly"""
        # Create and login a user
        user = User.objects.create_user(username="testuser", password="testpass")
        client.login(username="testuser", password="testpass")

        # Create a page with an invalid link with display text
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="This has an [[invalid_link|Custom Display]]",
            author=user,
        )

        # View the page
        response = client.get(f"/user/{user.username}/{page.slug}/")
        assert response.status_code == 200

        # The link should be marked as invalid and show display text
        content = response.content.decode()
        assert 'class="wiki-link-invalid"' in content
        assert "Custom Display" in content

        # Clicking the link should redirect to create page
        response = client.get(f"/user/{user.username}/invalid_link/create/")
        assert response.status_code in [301, 302, 303]
        assert "/create/" in response.url
