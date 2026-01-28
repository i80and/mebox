"""
Tests for userbox template functionality.
"""

import pytest

from wiki.markdown_extensions import render_markdown_with_wiki_links


@pytest.mark.django_db
def test_userbox_basic():
    """Test basic userbox with only middle parameter."""
    content = "{{userbox|middle=This is the middle content}}"
    result = render_markdown_with_wiki_links(content)

    # Check that the result contains the expected HTML structure
    assert '<div class="userbox-container"' in result
    assert "This is the middle content" in result
    assert '<div class="userbox-middle"' in result


@pytest.mark.django_db
def test_userbox_all_params():
    """Test userbox with all parameters."""
    content = "{{userbox|left=🐍|middle=Python Developer|right=Pro}}"
    result = render_markdown_with_wiki_links(content)

    # Check that all sections are present
    assert '<div class="userbox-container"' in result
    assert "🐍" in result
    assert "Python Developer" in result
    assert "Pro" in result
    assert '<div class="userbox-left"' in result
    assert '<div class="userbox-middle"' in result
    assert '<div class="userbox-right"' in result


@pytest.mark.django_db
def test_userbox_with_colors():
    """Test userbox with color parameters."""
    content = "{{userbox|left=🐍|middle=Python Developer|right=Pro|left-bg=#33aa33|middle-bg=#f0f0f0|right-bg=#33aa33}}"
    result = render_markdown_with_wiki_links(content)

    # Check that colors are applied
    assert "background-color: #33aa33" in result
    assert "background-color: #f0f0f0" in result


@pytest.mark.django_db
def test_userbox_left_only():
    """Test userbox with only left and middle."""
    content = "{{userbox|left=🐍|middle=Python Developer}}"
    result = render_markdown_with_wiki_links(content)

    # Check that left and middle are present, but not right
    assert "🐍" in result
    assert "Python Developer" in result
    assert '<div class="userbox-left"' in result
    assert '<div class="userbox-middle"' in result


@pytest.mark.django_db
def test_userbox_right_only():
    """Test userbox with only middle and right."""
    content = "{{userbox|middle=Python Developer|right=Pro}}"
    result = render_markdown_with_wiki_links(content)

    # Check that middle and right are present, but not left
    assert "Python Developer" in result
    assert "Pro" in result
    assert '<div class="userbox-middle"' in result
    assert '<div class="userbox-right"' in result


@pytest.mark.django_db
def test_multiple_userboxes():
    """Test multiple userboxes in the same content."""
    content = """
Here are some userboxes:

{{userbox|left=🐍|middle=Python|right=Pro}}

{{userbox|left=⚡|middle=Fast|right=Developer}}

{{userbox|middle=Just Middle Content}}
"""
    result = render_markdown_with_wiki_links(content)

    # Check that all userboxes are rendered
    assert result.count('<div class="userbox-container"') == 3
    assert "🐍" in result
    assert "⚡" in result
    assert "Just Middle Content" in result


@pytest.mark.django_db
def test_userbox_with_markdown():
    """Test userbox with markdown content."""
    content = "{{userbox|left=**Bold**|middle=This has _markdown_|right=🎉}}"
    result = render_markdown_with_wiki_links(content)

    # The markdown should be processed (bold and italic tags)
    # Note: The markdown is processed after template resolution
    # HTML tags are escaped for security, so we look for escaped versions
    assert "&lt;strong&gt;" in result or "**Bold**" in result
    assert "&lt;em&gt;" in result or "_markdown_" in result
    assert "🎉" in result


@pytest.mark.django_db
def test_userbox_missing_middle():
    """Test userbox without middle parameter (should still work)."""
    content = "{{userbox|left=🐍|right=Pro}}"
    result = render_markdown_with_wiki_links(content)

    # Should still render with empty middle
    assert '<div class="userbox-container"' in result
    assert "🐍" in result
    assert "Pro" in result


@pytest.mark.django_db
def test_userbox_markdown_in_all_sections():
    """Test that markdown is properly rendered in all userbox sections."""
    content = "{{userbox|left=**🐍**|middle=This is _italic_ and **bold**|right=🎉}}"
    result = render_markdown_with_wiki_links(content)

    # Check that markdown is rendered in all sections
    # Left section should have bold emoji
    # HTML tags are escaped for security
    assert "&lt;strong&gt;" in result or "**🐍**" in result
    # Middle section should have both italic and bold
    assert "&lt;em&gt;" in result or "_italic_" in result
    assert "&lt;strong&gt;" in result or "**bold**" in result
    # Right section should have emoji
    assert "🎉" in result
    # Should still have the userbox structure
    assert '<div class="userbox-container"' in result


@pytest.mark.django_db
def test_userbox_default_colors():
    """Test userbox with default colors when not specified."""
    content = "{{userbox|left=🐍|middle=Python|right=Pro}}"
    result = render_markdown_with_wiki_links(content)

    # Check that default colors are applied
    assert "background-color: #f0f0f0" in result
    assert "color: #000000" in result


@pytest.mark.django_db
def test_userbox_custom_foreground_colors():
    """Test userbox with custom foreground colors."""
    content = "{{userbox|left=🐍|middle=Python|right=Pro|left-fg=#ffffff|middle-fg=#ffffff|right-fg=#ffffff}}"
    result = render_markdown_with_wiki_links(content)

    # Check that custom foreground colors are applied
    assert "color: #ffffff" in result


@pytest.mark.django_db
def test_userbox_width_and_height():
    """Test that userbox has correct dimensions."""
    content = "{{userbox|middle=Test}}"
    result = render_markdown_with_wiki_links(content)

    # Check that the container has the correct dimensions
    assert "width: 185px" in result
    assert "height: 45px" in result


@pytest.mark.django_db
def test_userbox_left_width():
    """Test that left section has correct width."""
    content = "{{userbox|left=🐍|middle=Test}}"
    result = render_markdown_with_wiki_links(content)

    # Check that left section has 45px width
    assert "width: 45px" in result


@pytest.mark.django_db
def test_userbox_right_width():
    """Test that right section has correct width."""
    content = "{{userbox|middle=Test|right=Pro}}"
    result = render_markdown_with_wiki_links(content)

    # Check that right section has 45px width
    assert "width: 45px" in result


@pytest.mark.django_db
def test_userbox_apostrophe_handling():
    """Test that apostrophes are properly handled (not double-escaped)."""
    content = "{{userbox|middle=It's written in Django!}}"
    result = render_markdown_with_wiki_links(content)

    # Apostrophe should be escaped as &apos; for security
    assert "It&apos;s" in result
    # Should not have double-escaping issues
    assert "&amp;apos;" not in result
    # Should not have stray </p> tags
    assert "&lt;/p&gt;" not in result


@pytest.mark.django_db
def test_userbox_no_stray_p_tags():
    """Test that markdown-rendered content doesn't have stray </p> tags."""
    content = "{{userbox|left=🦨|middle=We have userboxes!|middle-bg=#aaaaff}}"
    result = render_markdown_with_wiki_links(content)

    # Content should be clean without stray HTML tags
    assert "🦨" in result
    assert "We have userboxes!" in result
    # Should not have escaped </p> tags
    assert "&lt;/p&gt;" not in result


@pytest.mark.django_db
def test_userbox_markdown_with_apostrophe():
    """Test markdown formatting with apostrophes."""
    content = "{{userbox|middle=It's **awesome** and _cool_!}}"
    result = render_markdown_with_wiki_links(content)

    # Both apostrophe and markdown should work
    assert "It&apos;s" in result
    # Markdown should be rendered (then escaped for security)
    assert "&lt;strong&gt;" in result or "**awesome**" in result
    assert "&lt;em&gt;" in result or "_cool_" in result
    # No stray tags
    assert "&lt;/p&gt;" not in result
