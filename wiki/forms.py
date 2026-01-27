from django import forms
from .models import WikiPage

class WikiPageForm(forms.ModelForm):
    """Form for creating/editing wiki pages"""
    
    class Meta:
        model = WikiPage
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'class': 'markdown-editor'}),
        }
        labels = {
            'title': 'Page Title',
            'content': 'Content (Markdown)',
        }
        help_texts = {
            'content': 'Use Markdown formatting for rich text.',
        }