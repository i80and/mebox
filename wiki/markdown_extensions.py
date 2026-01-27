"""
Markdown extensions for the wiki application.
"""

from typing import Dict, Optional, TYPE_CHECKING
from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from .models import WikiPage
else:
    from .models import WikiPage

UserModel = get_user_model()


def _parse_template_params(param_str: str) -> Dict[str, str]:
    """
    Parse template parameters from the pipe-separated string.
    
    Args:
        param_str: String like "name=Bob|age=25"
        
    Returns:
        Dict mapping parameter names to values, e.g., {"name": "Bob", "age": "25"}
    """
    params = {}
    if not param_str:
        return params
    
    # Split by pipe, but only at top level (not within nested pipes)
    parts = param_str.split("|")
    for part in parts:
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip()
    
    return params


def _resolve_template_content(
    template_name: str, 
    params: Dict[str, str], 
    username: Optional[str] = None,
    visited: Optional[set] = None,
    max_depth: int = 10
) -> Optional[str]:
    """
    Resolve a template by its name and substitute parameters.
    
    Args:
        template_name: The slug of the template page to resolve
        params: Dictionary of parameters to substitute
        username: Optional username to look up the template
        visited: Set of already-visited template names to detect cycles
        max_depth: Maximum recursion depth to prevent stack overflow
        
    Returns:
        The resolved content with parameters substituted, or None if template not found
    """
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion
    if max_depth <= 0:
        return None
    
    if template_name in visited:
        # Template cycle detected
        return None
    
    visited.add(template_name)
    
    try:
        # Find the template page
        if username:
            # First try to find the template in the current user's namespace
            user = UserModel.objects.get(username=username)
            try:
                template_page = WikiPage.objects.get(author=user, slug=template_name)
            except Exception:  # WikiPage.DoesNotExist
                # If not found in current user's namespace, try to find it in any user's namespace
                # This allows cross-user template usage
                template_page = WikiPage.objects.get(slug=template_name)
        else:
            # If no username specified, look for any page with this slug
            template_page = WikiPage.objects.get(slug=template_name)
        
        content = template_page.content
        
        # Recursively resolve any nested templates in the content
        # We need to find all {{template}} patterns and resolve them
        import re
        
        # Find all template invocations in the content
        pattern = r'\{\{([^|\}]+)(?:\|([^}]*))?\}\}'
        
        def replace_template(match: re.Match) -> str:
            nested_template_name = match.group(1).strip()
            nested_params_str = match.group(2) if match.group(2) else ""
            nested_params = _parse_template_params(nested_params_str)
            
            # Recursively resolve the nested template
            resolved = _resolve_template_content(
                nested_template_name,
                nested_params,
                username,
                visited,
                max_depth - 1
            )
            
            if resolved is not None:
                return resolved
            else:
                # If template not found, return the original text
                return match.group(0)
        
        # Resolve nested templates first
        content = re.sub(pattern, replace_template, content)
        
        # Now substitute parameters in the resolved content
        # Parameters are in the format {{{param_name}}}
        def substitute_param(match: re.Match) -> str:
            param_name = match.group(1).strip()
            return params.get(param_name, match.group(0))
        
        content = re.sub(r'\{\{\{([^}]+)\}\}\}', substitute_param, content)
        
        visited.remove(template_name)
        return content
        
    except (UserModel.DoesNotExist, Exception):  # WikiPage.DoesNotExist
        visited.remove(template_name)
        return None


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
    # First, resolve all templates in the content
    # We need to do this before markdown processing so that wiki links
    # inside templates are also processed
    import re
    
    def resolve_templates(match: re.Match) -> str:
        template_name = match.group(1).strip()
        params_str = match.group(2) if match.group(2) else ""
        params = _parse_template_params(params_str)
        
        resolved = _resolve_template_content(template_name, params, username)
        return resolved if resolved is not None else match.group(0)
    
    # Resolve templates in the content
    content = re.sub(r'\{\{([^|\}]+)(?:\|([^}]*))?\}\}', resolve_templates, content)
    
    # Then process with markdown
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

    # Apply the wiki link plugin
    md.use(lambda m: wiki_link_plugin(m, user_pages, username))

    return md.render(content)
