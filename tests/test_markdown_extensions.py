"""
Test cases for markdown extensions
"""
import pytest
from django.contrib.auth.models import User
from wiki.models import WikiPage
from wiki.markdown_extensions import render_markdown_with_wiki_links, wiki_link_plugin
from markdown_it import MarkdownIt


class TestWikiLinkPlugin:
    """Test the wiki link markdown plugin"""

    def test_wiki_link_basic(self):
        """Test basic [[wiki link]] syntax"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("This is a [[Test Page]] link.")
        
        assert '<a href="/Test_Page.html" data-wiki-link="Test_Page" class="wiki-link-invalid">Test Page</a>' in result

    def test_wiki_link_with_display_text(self):
        """Test [[target|display]] syntax"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("This is a [[test_page|Display Text]] link.")
        
        assert '<a href="/test_page.html" data-wiki-link="test_page" class="wiki-link-invalid">Display Text</a>' in result

    def test_wiki_link_with_spaces(self):
        """Test that spaces are converted to underscores"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("This is a [[Test Page]] link.")
        
        assert '<a href="/Test_Page.html" data-wiki-link="Test_Page" class="wiki-link-invalid">Test Page</a>' in result

    def test_wiki_link_mixed_with_regular_markdown(self):
        """Test wiki links mixed with regular markdown"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("# Heading\n\nSome text with [[wiki link]] and [regular link](http://example.com).")
        
        assert '<a href="/wiki_link.html" data-wiki-link="wiki_link" class="wiki-link-invalid">wiki link</a>' in result
        assert "<a href=" in result
        assert "http://example.com" in result

    def test_wiki_link_nested_in_other_elements(self):
        """Test wiki links inside other markdown elements"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("**Bold [[wiki link]]** and *italic [[another link]]*.")
        
        assert '<strong>Bold <a href="/wiki_link.html" data-wiki-link="wiki_link" class="wiki-link-invalid">wiki link</a></strong>' in result
        # Note: The italic text has a space after "italic" so we need to account for that
        assert '<em>italic <a href="/another_link.html" data-wiki-link="another_link" class="wiki-link-invalid">another link</a></em>' in result

    def test_wiki_link_in_list(self):
        """Test wiki links in list items"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("- Item with [[wiki link]]\n- Another item")
        
        assert '<li>Item with <a href="/wiki_link.html" data-wiki-link="wiki_link" class="wiki-link-invalid">wiki link</a></li>' in result

    def test_wiki_link_in_code_block(self):
        """Test that wiki links don't work inside code blocks"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("```\n[[This should not be a link]]\n```")
        
        # Code blocks should preserve the original text
        assert "[[This should not be a link]]" in result

    def test_wiki_link_with_pipe_in_display_text(self):
        """Test wiki link with pipe in display text"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("[[target|display|with|pipes]]")
        
        # Should only split on first pipe
        assert '<a href="/target.html" data-wiki-link="target" class="wiki-link-invalid">display|with|pipes</a>' in result

    def test_wiki_link_unclosed(self):
        """Test that unclosed wiki links are not processed"""
        md = MarkdownIt()
        md.use(wiki_link_plugin)
        
        result = md.render("This has [[an unclosed link")
        
        # Should not create a link
        assert "[[an unclosed link" in result


class TestRenderMarkdownWithWikiLinks:
    """Test the render_markdown_with_wiki_links function"""

    def test_render_without_username(self):
        """Test rendering without username (no validation)"""
        result = render_markdown_with_wiki_links("This is [[a test]] link.")
        
        # Should render the link but without validation
        assert '<a href="/a_test.html" data-wiki-link="a_test" class="wiki-link-invalid">a test</a>' in result

    def test_render_with_username_no_pages(self, db):
        """Test rendering with username but no pages exist"""
        # Create a user but no pages
        user = User.objects.create_user(username="testuser_no_pages", password="testpass")
        
        result = render_markdown_with_wiki_links("This is [[a test]] link.", "testuser_no_pages")
        
        # Should render the link as invalid
        assert '<a href="/a_test.html" data-wiki-link="a_test" class="wiki-link-invalid">a test</a>' in result

    def test_render_with_valid_link(self, db):
        """Test rendering with a valid wiki link"""
        user = User.objects.create_user(username="testuser_valid", password="testpass")
        page = WikiPage.objects.create(
            title="Test Page Valid",
            slug="test_page_valid",
            content="# Test Content",
            author=user
        )
        
        result = render_markdown_with_wiki_links("This is [[test_page_valid]] link.", "testuser_valid")
        
        # Should render the link as valid
        assert '<a href="/test_page_valid.html" data-wiki-link="test_page_valid" class="wiki-link-valid">test_page_valid</a>' in result

    def test_render_with_invalid_link(self, db):
        """Test rendering with an invalid wiki link"""
        user = User.objects.create_user(username="testuser_invalid", password="testpass")
        page = WikiPage.objects.create(
            title="Test Page Invalid",
            slug="test_page_invalid",
            content="# Test Content",
            author=user
        )
        
        result = render_markdown_with_wiki_links("This is [[nonexistent]] link.", "testuser_invalid")
        
        # Should render the link as invalid
        assert '<a href="/nonexistent.html" data-wiki-link="nonexistent" class="wiki-link-invalid">nonexistent</a>' in result

    def test_render_with_display_text(self, db):
        """Test rendering with display text"""
        user = User.objects.create_user(username="testuser_display", password="testpass")
        page = WikiPage.objects.create(
            title="Test Page Display",
            slug="test_page_display",
            content="# Test Content",
            author=user
        )
        
        result = render_markdown_with_wiki_links("This is [[test_page_display|Display Text]] link.", "testuser_display")
        
        # Should render with display text and valid class
        assert '<a href="/test_page_display.html" data-wiki-link="test_page_display" class="wiki-link-valid">Display Text</a>' in result

    def test_render_mixed_valid_and_invalid(self, db):
        """Test rendering with both valid and invalid links"""
        user = User.objects.create_user(username="testuser_mixed", password="testpass")
        page1 = WikiPage.objects.create(
            title="Test Page 1 Mixed",
            slug="test_page_1_mixed",
            content="# Test Content 1",
            author=user
        )
        
        result = render_markdown_with_wiki_links(
            "Valid [[test_page_1_mixed]] and invalid [[test_page_2_mixed]].",
            "testuser_mixed"
        )
        
        # Should have one valid and one invalid link
        assert '<a href="/test_page_1_mixed.html" data-wiki-link="test_page_1_mixed" class="wiki-link-valid">test_page_1_mixed</a>' in result
        assert '<a href="/test_page_2_mixed.html" data-wiki-link="test_page_2_mixed" class="wiki-link-invalid">test_page_2_mixed</a>' in result

    def test_render_with_nonexistent_user(self, db):
        """Test rendering with a username that doesn't exist"""
        result = render_markdown_with_wiki_links("This is [[a test]] link.", "nonexistent_user")
        
        # Should render the link as invalid (no validation possible)
        assert '<a href="/a_test.html" data-wiki-link="a_test" class="wiki-link-invalid">a test</a>' in result
