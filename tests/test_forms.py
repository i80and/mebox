"""
Test cases for wiki forms
"""
import pytest
from wiki.forms import WikiPageForm


class TestWikiPageForm:
    """Test WikiPageForm"""
    
    def test_wikipageform_valid_data(self):
        """Test WikiPageForm with valid data"""
        form_data = {
            'title': 'Test Page',
            'content': '# Test Content'
        }
        form = WikiPageForm(data=form_data)
        assert form.is_valid()
    
    def test_wikipageform_required_fields(self):
        """Test WikiPageForm validates required fields"""
        form = WikiPageForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'content' in form.errors
    
    def test_wikipageform_title_field(self):
        """Test WikiPageForm title field"""
        form_data = {
            'title': 'Test Page',
            'content': '# Test Content'
        }
        form = WikiPageForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['title'] == 'Test Page'
    
    def test_wikipageform_content_field(self):
        """Test WikiPageForm content field"""
        form_data = {
            'title': 'Test Page',
            'content': '# Test Content'
        }
        form = WikiPageForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['content'] == '# Test Content'
    
    def test_wikipageform_long_title(self):
        """Test WikiPageForm with long title"""
        long_title = 'A' * 201  # Exceeds max_length
        form_data = {
            'title': long_title,
            'content': '# Test Content'
        }
        form = WikiPageForm(data=form_data)
        assert not form.is_valid()
        assert 'title' in form.errors
    
    def test_wikipageform_empty_content(self):
        """Test WikiPageForm with empty content"""
        form_data = {
            'title': 'Test Page',
            'content': ''
        }
        form = WikiPageForm(data=form_data)
        assert not form.is_valid()
        assert 'content' in form.errors
    
    def test_wikipageform_markdown_content(self):
        """Test WikiPageForm accepts markdown content"""
        markdown_content = """# Heading 1

## Heading 2

**Bold text**
*Italic text*

- List item 1
- List item 2

```python
# Code block
print("Hello")
```
"""
        form_data = {
            'title': 'Markdown Test',
            'content': markdown_content
        }
        form = WikiPageForm(data=form_data)
        assert form.is_valid()
        # Just check that content is preserved (exact match might fail due to whitespace)
        assert 'Heading 1' in form.cleaned_data['content']
        assert 'Bold text' in form.cleaned_data['content']
        assert 'List item 1' in form.cleaned_data['content']
        assert 'Code block' in form.cleaned_data['content']
