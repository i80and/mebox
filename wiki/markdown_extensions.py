"""
Markdown extensions for the wiki application.
"""
from typing import Dict, List, Optional
from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from django.contrib.auth.models import User
from .models import WikiPage


def wiki_link_plugin(md: MarkdownIt, user_pages: Optional[Dict[str, str]] = None) -> None:
    """
    Plugin to handle [[wiki-style]] links.
    
    Args:
        md: The MarkdownIt instance
        user_pages: Optional dict mapping slugs to page titles for validation
    """
    
    def wiki_link_rule(state: StateInline, silent: bool) -> bool:
        """
        Rule to parse [[wiki-style]] links.
        
        Returns:
            True if a wiki link was found and processed, False otherwise
        """
        # Check if we're at [[
        if state.src[state.pos : state.pos + 2] != "[[":
            return False

        start = state.pos
        pos = start + 2

        # Find closing ]]
        while pos < len(state.src) - 1:
            if state.src[pos : pos + 2] == "]]":
                break
            pos += 1
        else:
            return False  # No closing bracket found

        content = state.src[start + 2 : pos]

        if not silent:
            # Parse display text
            if "|" in content:
                target, display = content.split("|", 1)
            else:
                target = display = content

            # Clean up target (remove spaces, convert to slug format)
            target_slug = target.strip().replace(" ", "_")

            # Check if the page exists for validation
            is_valid = False
            if user_pages:
                # Check if the target exists in the provided pages
                # The target_slug should match exactly with a page slug
                is_valid = target_slug in user_pages

            # Create link token
            # Note: The href will be set by the view context, but we need to store the target
            # For now, we'll use a placeholder that the view can replace
            token = state.push("link_open", "a", 1)
            token.attrSet("href", f"/{target_slug}.html")
            token.attrSet("data-wiki-link", target_slug)
            
            # Add class based on validity
            if is_valid:
                token.attrSet("class", "wiki-link-valid")
            else:
                token.attrSet("class", "wiki-link-invalid")

            token = state.push("text", "", 0)
            token.content = display.strip()

            state.push("link_close", "a", -1)

        state.pos = pos + 2
        return True

    # Add the rule before the default link rule
    md.inline.ruler.before("link", "wiki_link", wiki_link_rule)


def render_markdown_with_wiki_links(
    content: str, username: Optional[str] = None
) -> str:
    """
    Render markdown content with wiki link support.
    
    Args:
        content: The markdown content to render
        username: Optional username to validate links against
        
    Returns:
        HTML string with rendered markdown and wiki links
    """
    md = MarkdownIt()
    
    # If username is provided, load all pages by that user for validation
    user_pages = None
    if username:
        try:
            user = User.objects.get(username=username)
            pages = WikiPage.objects.filter(author=user)
            user_pages = {page.slug: page.title for page in pages}
        except User.DoesNotExist:
            user_pages = {}
    
    # Apply the plugin with user pages for validation
    md.use(lambda m: wiki_link_plugin(m, user_pages))
    
    return md.render(content)
