"""
Integration test for wiki link functionality
"""

import pytest
from django.contrib.auth.models import User
from wiki.models import WikiPage


class TestWikiLinkIntegration:
    """Test wiki link functionality in the actual view"""

    def test_wiki_link_in_view_with_valid_link(self, client, db):
        """Test that wiki links work in the actual view with valid links"""
        # Create a user
        user = User.objects.create_user(username="testuser", password="testpass")

        # Create a page that will be linked to
        target_page = WikiPage.objects.create(
            title="Target Page",
            slug="target_page",
            content="# This is the target page",
            author=user,
        )

        # Create a page that links to the target
        source_page = WikiPage.objects.create(
            title="Source Page",
            slug="source_page",
            content="# This page links to [[target_page]]",
            author=user,
        )

        # View the source page
        response = client.get(f"/user/{user.username}/{source_page.slug}/")

        # Check that the response is successful
        assert response.status_code == 200

        # Check that the wiki link is rendered with the valid class
        assert 'class="wiki-link-valid"' in response.content.decode()
        assert 'href="/target_page.html"' in response.content.decode()

    def test_wiki_link_in_view_with_invalid_link(self, client, db):
        """Test that wiki links work in the actual view with invalid links"""
        # Create a user
        user = User.objects.create_user(username="testuser2", password="testpass")

        # Create a page that links to a non-existent page
        source_page = WikiPage.objects.create(
            title="Source Page",
            slug="source_page",
            content="# This page links to [[nonexistent_page]]",
            author=user,
        )

        # View the source page
        response = client.get(f"/user/{user.username}/{source_page.slug}/")

        # Check that the response is successful
        assert response.status_code == 200

        # Check that the wiki link is rendered with the invalid class
        assert 'class="wiki-link-invalid"' in response.content.decode()
        assert 'href="/nonexistent_page.html"' in response.content.decode()

    def test_wiki_link_with_display_text(self, client, db):
        """Test that wiki links with display text work correctly"""
        # Create a user
        user = User.objects.create_user(username="testuser3", password="testpass")

        # Create a page that will be linked to
        target_page = WikiPage.objects.create(
            title="Target Page",
            slug="target_page",
            content="# This is the target page",
            author=user,
        )

        # Create a page that links to the target with display text
        source_page = WikiPage.objects.create(
            title="Source Page",
            slug="source_page",
            content="# This page links to [[target_page|Custom Display Text]]",
            author=user,
        )

        # View the source page
        response = client.get(f"/user/{user.username}/{source_page.slug}/")

        # Check that the response is successful
        assert response.status_code == 200

        # Check that the wiki link is rendered with display text and valid class
        assert 'class="wiki-link-valid"' in response.content.decode()
        assert 'href="/target_page.html"' in response.content.decode()
        assert "Custom Display Text" in response.content.decode()

    def test_mixed_wiki_links(self, client, db):
        """Test that both valid and invalid wiki links can coexist"""
        # Create a user
        user = User.objects.create_user(username="testuser4", password="testpass")

        # Create a page that will be linked to
        target_page = WikiPage.objects.create(
            title="Target Page",
            slug="target_page",
            content="# This is the target page",
            author=user,
        )

        # Create a page with both valid and invalid links
        source_page = WikiPage.objects.create(
            title="Source Page",
            slug="source_page",
            content="# Valid [[target_page]] and invalid [[nonexistent]] links",
            author=user,
        )

        # View the source page
        response = client.get(f"/user/{user.username}/{source_page.slug}/")

        # Check that the response is successful
        assert response.status_code == 200

        # Check that both links are rendered correctly
        content = response.content.decode()
        assert 'class="wiki-link-valid"' in content
        assert 'class="wiki-link-invalid"' in content
        assert 'href="/target_page.html"' in content
        assert 'href="/nonexistent.html"' in content
