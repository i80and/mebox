"""
Markdown extensions for the wiki application.
"""

from typing import Dict, Optional
from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from django.contrib.auth import get_user_model
from .models import WikiPage

UserModel = get_user_model()


def wiki_link_plugin(
    md: MarkdownIt,
    user_pages: Optional[Dict[str, str]] = None,
    username: Optional[str] = None,
) -> None:
    """
    Plugin to handle [[wiki-style]] links.

    Args:
        md: The MarkdownIt instance
        user_pages: Optional dict mapping slugs to page titles for validation
        username: Optional username for cross-user link validation
    """

    def wiki_link_rule(state: StateInline, silent: bool) -> bool:
        """
        Rule to parse [[wiki-style]] links.

        Supports two formats:
        - [[page]] - same user namespace
        - [[User:username/page]] - cross-user namespace

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

            # Parse target - check for User: namespace
            target_slug = target.strip()
            cross_user = False
            target_username = None

            if target_slug.startswith("User:"):
                # Cross-user link format: User:username/page
                parts = target_slug[5:].split("/", 1)  # Remove "User:" prefix
                if len(parts) == 2:
                    target_username = parts[0].strip()
                    target_slug = parts[1].strip().replace(" ", "_")
                    cross_user = True
                else:
                    # Invalid User: format (no page specified), treat as regular link
                    # Remove the User: prefix and treat as normal text
                    target_slug = target_slug[5:].strip().replace(" ", "_")
                    cross_user = False
            else:
                # Same-user link - convert spaces to underscores
                target_slug = target_slug.replace(" ", "_")

            # Check if the page exists for validation
            is_valid = False
            validation_username = target_username if cross_user else username

            if validation_username:
                # Check if this user has a page with the target slug
                try:
                    target_user = UserModel.objects.get(username=validation_username)
                    is_valid = WikiPage.objects.filter(
                        author=target_user, slug=target_slug
                    ).exists()
                except UserModel.DoesNotExist:
                    is_valid = False
            elif not cross_user and user_pages:
                # Same-user link - check in the current user's pages
                is_valid = target_slug in user_pages

            # Create link token
            # Store information for JavaScript to fix the URL
            token = state.push("link_open", "a", 1)
            token.attrSet("href", f"/{target_slug}.html")
            token.attrSet("data-wiki-link", target_slug)

            if cross_user and target_username:
                token.attrSet("data-wiki-username", target_username)

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
            user = UserModel.objects.get(username=username)
            pages = WikiPage.objects.filter(author=user)
            user_pages = {page.slug: page.title for page in pages}
        except UserModel.DoesNotExist:
            user_pages = {}

    # Apply the plugin with user pages for validation
    md.use(lambda m: wiki_link_plugin(m, user_pages, username))

    return md.render(content)
