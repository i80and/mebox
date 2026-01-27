"""
Test cases for cross-user wiki links
"""

import pytest
from django.contrib.auth.models import User
from wiki.models import WikiPage
from wiki.markdown_extensions import render_markdown_with_wiki_links, wiki_link_plugin
from markdown_it import MarkdownIt


class TestCrossUserLinks:
    """Test cross-user wiki link functionality"""

    def test_cross_user_link_basic(self, db):
        """Test basic [[User:username/page]] syntax"""
        # Create a user so validation doesn't fail
        User.objects.create_user(username="testuser", password="testpass")

        md = MarkdownIt()
        md.use(wiki_link_plugin)

        result = md.render("This is a [[User:testuser/test_page]] link.")

        # Should have data-wiki-username attribute
        assert 'data-wiki-username="testuser"' in result
        assert 'data-wiki-link="test_page"' in result
        assert '<a href="/test_page.html"' in result

    def test_cross_user_link_with_display_text(self, db):
        """Test [[User:username/page|Display]] syntax"""
        # Create a user so validation doesn't fail
        User.objects.create_user(username="testuser", password="testpass")

        md = MarkdownIt()
        md.use(wiki_link_plugin)

        result = md.render("This is a [[User:testuser/test_page|Custom Text]] link.")

        assert 'data-wiki-username="testuser"' in result
        assert 'data-wiki-link="test_page"' in result
        assert "Custom Text" in result

    def test_cross_user_link_with_spaces(self, db):
        """Test that spaces in page title are converted to underscores"""
        # Create a user so validation doesn't fail
        User.objects.create_user(username="testuser", password="testpass")

        md = MarkdownIt()
        md.use(wiki_link_plugin)

        result = md.render("This is a [[User:testuser/Test Page]] link.")

        assert 'data-wiki-username="testuser"' in result
        assert 'data-wiki-link="Test_Page"' in result

    def test_cross_user_link_validation_valid(self, db):
        """Test that cross-user links are validated correctly"""
        # Create two users
        user1 = User.objects.create_user(username="user1", password="testpass")
        user2 = User.objects.create_user(username="user2", password="testpass")

        # Create a page for user2
        page = WikiPage.objects.create(
            title="Test Page", slug="test_page", content="# Test Content", author=user2
        )

        # Render from user1's perspective
        result = render_markdown_with_wiki_links(
            "Link to [[User:user2/test_page]].", "user1"
        )

        # Should be valid since user2 has the page
        assert 'class="wiki-link-valid"' in result
        assert 'data-wiki-username="user2"' in result

    def test_cross_user_link_validation_invalid(self, db):
        """Test that invalid cross-user links are marked as such"""
        # Create two users
        user1 = User.objects.create_user(username="user1", password="testpass")
        user2 = User.objects.create_user(username="user2", password="testpass")

        # Create a page for user2
        page = WikiPage.objects.create(
            title="Test Page", slug="test_page", content="# Test Content", author=user2
        )

        # Render from user1's perspective - link to non-existent page
        result = render_markdown_with_wiki_links(
            "Link to [[User:user2/nonexistent]].", "user1"
        )

        # Should be invalid
        assert 'class="wiki-link-invalid"' in result
        assert 'data-wiki-username="user2"' in result

    def test_cross_user_link_nonexistent_user(self, db):
        """Test that links to non-existent users are marked as invalid"""
        user1 = User.objects.create_user(username="user1", password="testpass")

        # Link to non-existent user
        result = render_markdown_with_wiki_links(
            "Link to [[User:nonexistent/test_page]].", "user1"
        )

        # Should be invalid
        assert 'class="wiki-link-invalid"' in result
        assert 'data-wiki-username="nonexistent"' in result

    def test_mixed_same_and_cross_user_links(self, db):
        """Test that same-user and cross-user links can coexist"""
        user1 = User.objects.create_user(username="user1", password="testpass")
        user2 = User.objects.create_user(username="user2", password="testpass")

        # Create pages
        page1 = WikiPage.objects.create(
            title="Page 1", slug="page1", content="# Test", author=user1
        )
        page2 = WikiPage.objects.create(
            title="Page 2", slug="page2", content="# Test", author=user2
        )

        # Render from user1's perspective
        result = render_markdown_with_wiki_links(
            "Same user [[page1]] and cross user [[User:user2/page2]].", "user1"
        )

        # Both should be valid
        assert 'class="wiki-link-valid"' in result
        # Should have both types of links
        assert 'data-wiki-username="user2"' in result
        assert 'data-wiki-link="page1"' in result
        assert 'data-wiki-link="page2"' in result

    def test_invalid_user_format(self):
        """Test that invalid User: format is handled gracefully"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)

        # Invalid format - no page specified
        result = md.render("This is a [[User:testuser]] link.")

        # Should still create a link, but without data-wiki-username
        # The User: prefix is removed and treated as regular text
        assert '<a href="/testuser.html"' in result
        assert 'data-wiki-link="testuser"' in result
        assert "User:testuser" in result  # Display text should be preserved

    def test_user_colon_in_regular_link(self):
        """Test that User: in regular text doesn't create a cross-user link"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)

        result = md.render("This is just text with User:testuser in it.")

        # Should not create any wiki links
        assert "data-wiki-link" not in result
