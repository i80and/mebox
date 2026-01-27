from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager
    from django.db.models.fields.related import ForeignKey

    # Django model instances have the actual attributes at runtime
    class WikiPage(models.Model):
        """Type stub for WikiPage with proper attributes"""

        title: str
        slug: str
        content: str
        author: ForeignKey[User, "WikiPage"]
        created_at: models.DateTimeField
        updated_at: models.DateTimeField
        objects: BaseManager["WikiPage"]

        def get_current_revision(self) -> Optional["PageRevision"]: ...

    class PageRevision(models.Model):
        """Type stub for PageRevision with proper attributes"""

        page: ForeignKey[WikiPage, "PageRevision"]
        title: str
        content: str
        editor: ForeignKey[User, "PageRevision"]
        created_at: models.DateTimeField
        is_current: bool
        objects: BaseManager["PageRevision"]

    class UserActivity(models.Model):
        """Type stub for UserActivity with proper attributes"""

        user: ForeignKey[User, "UserActivity"]
        activity_type: str
        page: Optional[ForeignKey[WikiPage, "UserActivity"]]
        details: str
        created_at: models.DateTimeField
        objects: BaseManager["UserActivity"]

        def get_activity_type_display(self) -> str: ...


class WikiPage(models.Model):
    """Model for user wiki pages"""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects: "BaseManager['WikiPage']"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wiki Page"
        verbose_name_plural = "Wiki Pages"

    def __str__(self) -> str:
        return f"{self.title} by {self.author.username}"  # type: ignore[attr-defined]

    def save(self, *args, **kwargs) -> None:
        """Automatically generate slug from title if not provided"""
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique
            counter = 1
            original_slug = self.slug
            while WikiPage.objects.filter(slug=self.slug).exclude(id=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Get absolute URL for the wiki page"""
        return reverse("view_wiki_page", args=[self.author.username, self.slug])  # type: ignore[attr-defined]

    def get_current_revision(self) -> Optional["PageRevision"]:
        """Get the current revision of this page"""
        return self.revisions.filter(is_current=True).first()  # type: ignore[attr-defined]


class PageRevision(models.Model):
    """Model for tracking revisions of wiki pages"""

    page = models.ForeignKey(
        WikiPage, on_delete=models.CASCADE, related_name="revisions"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    objects: "BaseManager['PageRevision']"

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"
        verbose_name = "Page Revision"
        verbose_name_plural = "Page Revisions"

    def __str__(self) -> str:
        return f"Revision of '{self.page.title}' by {self.editor.username if self.editor else 'Unknown'}"  # type: ignore[attr-defined]


class UserActivity(models.Model):
    """Model for tracking user activity"""

    ACTIVITY_TYPES = [
        ("create_page", "Created Page"),
        ("edit_page", "Edited Page"),
        ("delete_page", "Deleted Page"),
        ("login", "Logged In"),
        ("signup", "Signed Up"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    page = models.ForeignKey(WikiPage, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects: "BaseManager['UserActivity']"

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"

    def __str__(self) -> str:
        return f"{self.get_activity_type_display()} by {self.user.username}"  # type: ignore[attr-defined]
