"""
Test cases for template instantiation
"""

from django.contrib.auth.models import User
from wiki.models import WikiPage
from wiki.markdown_extensions import render_markdown_with_wiki_links


class TestTemplateInstantiation:
    """Test template instantiation with and without parameters"""

    def test_simple_template(self, db):
        """Test basic {{template}} syntax"""
        user = User.objects.create_user(username="testuser_template", password="testpass")
        
        # Create a template page
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Hello!",
            author=user,
        )
        
        # Create a page that uses the template
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome to my page! {{userbox}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should replace the template with its content
        assert "Welcome to my page!" in result
        assert "Hello!" in result
        assert "{{userbox}}" not in result

    def test_template_with_parameters(self, db):
        """Test {{template|param=value}} syntax"""
        user = User.objects.create_user(username="testuser_params", password="testpass")
        
        # Create a template with parameters
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Hello {{{name}}}!",
            author=user,
        )
        
        # Create a page that uses the template with parameters
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome to my page! {{userbox|name=Bob}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should substitute the parameter
        assert "Welcome to my page!" in result
        assert "Hello Bob!" in result
        assert "{{{name}}}" not in result
        assert "{{userbox|name=Bob}}" not in result

    def test_template_with_multiple_parameters(self, db):
        """Test template with multiple parameters"""
        user = User.objects.create_user(username="testuser_multi", password="testpass")
        
        # Create a template with multiple parameters
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Hello {{{name}}}, you are {{{age}}} years old!",
            author=user,
        )
        
        # Create a page that uses the template with multiple parameters
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome! {{userbox|name=Alice|age=30}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should substitute all parameters
        assert "Welcome!" in result
        assert "Hello Alice, you are 30 years old!" in result
        assert "{{{name}}}" not in result
        assert "{{{age}}}" not in result

    def test_nonexistent_template(self, db):
        """Test that nonexistent templates are left as-is"""
        user = User.objects.create_user(username="testuser_nonexist", password="testpass")
        
        # Create a page that uses a nonexistent template
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome! {{nonexistent_template}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should keep the original text
        assert "Welcome! {{nonexistent_template}}" in result

    def test_nested_templates(self, db):
        """Test nested template instantiation"""
        user = User.objects.create_user(username="testuser_nested", password="testpass")
        
        # Create a base template
        WikiPage.objects.create(
            title="Base",
            slug="base",
            content="Base content with {{{name}}}",
            author=user,
        )
        
        # Create a template that uses the base template
        WikiPage.objects.create(
            title="Nested",
            slug="nested",
            content="Nested: {{base|name=Test}}",
            author=user,
        )
        
        # Create a page that uses the nested template
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Page: {{nested}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should resolve both templates
        assert "Page: Nested: Base content with Test" in result
        assert "{{nested}}" not in result
        assert "{{base|name=Test}}" not in result

    def test_template_cycle_detection(self, db):
        """Test that circular template references are handled"""
        user = User.objects.create_user(username="testuser_cycle", password="testpass")
        
        # Create templates that reference each other
        WikiPage.objects.create(
            title="Template A",
            slug="template_a",
            content="A: {{template_b}}",
            author=user,
        )
        
        WikiPage.objects.create(
            title="Template B",
            slug="template_b",
            content="B: {{template_a}}",
            author=user,
        )
        
        # Create a page that uses template A
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Page: {{template_a}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should detect the cycle and not infinite loop
        # The cycle should be broken and the unresolved template should be shown
        assert "Page: A: B: {{template_a}}" in result

    def test_template_with_wiki_links(self, db):
        """Test that templates can contain wiki links"""
        user = User.objects.create_user(username="testuser_wiki", password="testpass")
        
        # Create a template with a wiki link
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Check out my [[other_page]]!",
            author=user,
        )
        
        # Create the target page for the wiki link
        WikiPage.objects.create(
            title="Other Page",
            slug="other_page",
            content="Other content",
            author=user,
        )
        
        # Create a page that uses the template
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome! {{userbox}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should render both the template and the wiki link
        assert "Welcome!" in result
        assert "Check out my" in result
        assert '<a href="/other_page.html"' in result
        assert "wiki-link-valid" in result

    def test_template_without_username(self, db):
        """Test template resolution without username (cross-user templates)"""
        user1 = User.objects.create_user(username="user1", password="testpass")
        user2 = User.objects.create_user(username="user2", password="testpass")
        
        # Create a template in user1's namespace
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Hello from user1!",
            author=user1,
        )
        
        # Create a page in user2's namespace that uses the template
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome! {{userbox}}",
            author=user2,
        )
        
        # Render the page with user2's username
        result = render_markdown_with_wiki_links(page.content, user2.username)
        
        # Should still find the template (cross-user template usage)
        assert "Welcome!" in result
        assert "Hello from user1!" in result

    def test_template_with_markdown(self, db):
        """Test that template content is rendered as markdown"""
        user = User.objects.create_user(username="testuser_md", password="testpass")
        
        # Create a template with inline markdown
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="This is **bold** text and *italic* text.",
            author=user,
        )
        
        # Create a page that uses the template
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome! {{userbox}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should render markdown in the template
        assert "Welcome!" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_template_with_multiple_invocations(self, db):
        """Test multiple invocations of the same template"""
        user = User.objects.create_user(username="testuser_multi_inv", password="testpass")
        
        # Create a template
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Hello {{{name}}}!",
            author=user,
        )
        
        # Create a page with multiple template invocations
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="First: {{userbox|name=Alice}}\n\nSecond: {{userbox|name=Bob}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should substitute both parameters correctly
        assert "First: Hello Alice!" in result
        assert "Second: Hello Bob!" in result

    def test_template_with_no_parameters_but_param_syntax(self, db):
        """Test template with parameter placeholders but no parameters provided"""
        user = User.objects.create_user(username="testuser_no_params", password="testpass")
        
        # Create a template with parameter placeholders
        WikiPage.objects.create(
            title="Userbox",
            slug="userbox",
            content="Hello {{{name}}}, you are {{{age}}} years old!",
            author=user,
        )
        
        # Create a page that uses the template without providing parameters
        page = WikiPage.objects.create(
            title="Test Page",
            slug="test_page",
            content="Welcome! {{userbox}}",
            author=user,
        )
        
        # Render the page
        result = render_markdown_with_wiki_links(page.content, user.username)
        
        # Should keep the parameter placeholders since no values were provided
        assert "Welcome!" in result
        assert "Hello {{{name}}}, you are {{{age}}} years old!" in result
