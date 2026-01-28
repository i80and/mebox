from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify





class WikiPage(models.Model):
    """Model for user wiki pages"""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Wiki Page"
        verbose_name_plural = "Wiki Pages"

    def __str__(self) -> str:
        return f"{self.title} by {self.author.username}"

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
        return reverse("view_wiki_page", args=[self.author.username, self.slug])

    def get_current_revision(self) -> Optional["PageRevision"]:
        """Get the current revision of this page"""
        return self.revisions.filter(is_current=True).first()


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

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"
        verbose_name = "Page Revision"
        verbose_name_plural = "Page Revisions"

    def __str__(self) -> str:
        return f"Revision of '{self.page.title}' by {self.editor.username if self.editor else 'Unknown'}"


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

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"

    def __str__(self) -> str:
        return f"{self.get_activity_type_display()} by {self.user.username}"


class Follow(models.Model):
    """Model for tracking follow relationships between users"""

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Follow"
        verbose_name_plural = "Follows"
        # Ensure we don't have duplicate follows
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.follower.username} follows {self.following.username}"

    def save(self, *args, **kwargs) -> None:
        """Ensure no self-follows"""
        if self.follower == self.following:
            raise ValueError("Users cannot follow themselves")
        super().save(*args, **kwargs)


def get_following(user: User) -> models.QuerySet[User]:
    """
    Get all users that the given user is following.
    
    Returns a QuerySet of User objects that the user follows.
    """
    return User.objects.filter(
        id__in=Follow.objects.filter(follower=user).values("following_id")
    ).order_by("username")


def get_followers(user: User) -> models.QuerySet[User]:
    """
    Get all users that follow the given user.
    
    Returns a QuerySet of User objects that follow the user.
    """
    return User.objects.filter(
        id__in=Follow.objects.filter(following=user).values("follower_id")
    ).order_by("username")


def is_following(user: User, target_user: User) -> bool:
    """
    Check if user is following target_user.
    
    Returns True if user follows target_user, False otherwise.
    """
    return Follow.objects.filter(follower=user, following=target_user).exists()


def get_mutual_follows(user: User, target_user: User) -> models.QuerySet[User]:
    """
    Get mutual follows between two users.
    
    Returns a QuerySet of User objects that both users follow.
    """
    # Get IDs of users that user follows
    user_following_ids = set(get_following(user).values_list("id", flat=True))
    # Get IDs of users that target_user follows
    target_following_ids = set(get_following(target_user).values_list("id", flat=True))
    # Find intersection
    mutual_ids = user_following_ids & target_following_ids
    # Return users with those IDs
    return User.objects.filter(id__in=mutual_ids).order_by("username")
