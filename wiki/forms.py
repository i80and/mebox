from django import forms
from .models import WikiPage
from typing import ClassVar, Dict, Any

class WikiPageForm(forms.ModelForm):
    """Form for creating/editing wiki pages"""
    
    class Meta:
        model = WikiPage
        fields = ['title', 'content']
        widgets: ClassVar[Dict[str, Any]] = {
            'content': forms.Textarea(attrs={'rows': 20, 'class': 'markdown-editor'}),
        }
        labels: ClassVar[Dict[str, str]] = {
            'title': 'Page Title',
            'content': 'Content (Markdown)',
        }
        help_texts: ClassVar[Dict[str, str]] = {
            'content': 'Use Markdown formatting for rich text.',
        }