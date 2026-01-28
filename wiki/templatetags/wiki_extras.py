"""
Custom template filters for the wiki app.
"""

import re
from django import template

register = template.Library()


@register.filter
def remove_unresolved_templates(value: str) -> str:
    """
    Remove any unresolved template syntax ({{template}}) from the text.

    This is useful for Open Graph descriptions where we don't want to show
    wiki syntax like {{userbox}}.

    Args:
        value: The text to process

    Returns:
        Text with unresolved templates removed
    """
    if not value:
        return value

    # Remove all {{...}} patterns
    return re.sub(r"\{\{[^}]*\}\}", "", value)
