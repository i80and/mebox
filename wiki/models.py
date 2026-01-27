from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse

class WikiPage(models.Model):
    """Model for user wiki pages"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wiki Page'
        verbose_name_plural = 'Wiki Pages'
    
    def __str__(self):
        return f"{self.title} by {self.author.username}"
    
    def save(self, *args, **kwargs):
        """Automatically generate slug from title if not provided"""
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique
            counter = 1
            original_slug = self.slug
            while WikiPage.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get absolute URL for the wiki page"""
        return reverse('view_wiki_page', args=[self.author.username, self.slug])
