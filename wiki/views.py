from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddFollowForm, WikiPageForm
from .markdown_extensions import render_markdown_with_wiki_links
from .models import (
    PageRevision,
    UserActivity,
    WikiPage,
    Follow,
    get_following,
    get_followers,
    is_following,
    get_mutual_follows,
)

UserModel = get_user_model()


def _get_authenticated_user(request: HttpRequest) -> User:
    """Helper to get authenticated user from request"""
    # This is safe because the views are decorated with @login_required
    assert isinstance(request.user, User)
    return request.user


def home(request: HttpRequest) -> HttpResponse:
    """Home page showing recent wiki pages"""
    pages = WikiPage.objects.all().order_by("-created_at")[:10]
    return render(request, "wiki/home.html", {"pages": pages})


def signup(request: HttpRequest) -> HttpResponse:
    """User signup view"""
    if request.method == "POST":
        form: UserCreationForm = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Log signup activity
            UserActivity.objects.create(
                user=user,
                activity_type="signup",
                details=f"User {user.username} signed up",
            )
            messages.success(request, "Account created successfully!")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "wiki/signup.html", {"form": form})


def user_login(request: HttpRequest) -> HttpResponse:
    """User login view"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Log login activity
                UserActivity.objects.create(
                    user=user,
                    activity_type="login",
                    details=f"User {user.username} logged in",
                )
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "wiki/login.html", {"form": form})


def user_logout(request: HttpRequest) -> HttpResponse:
    """User logout view"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def user_profile(request: HttpRequest, username: str) -> HttpResponse:
    """User profile page"""
    user = User.objects.get(username=username)
    current_user = _get_authenticated_user(request)

    # Get user's wiki pages
    pages = WikiPage.objects.filter(author=user).order_by("-created_at")

    # Get following/followers if viewing own profile
    following = None
    followers = None
    is_following_user = False
    is_followed_by_user = False
    mutual_follows = None

    if current_user == user:
        # Viewing own profile
        following = get_following(current_user)
        followers = get_followers(current_user)
    else:
        # Viewing another user's profile
        is_following_user = is_following(current_user, user)
        is_followed_by_user = is_following(user, current_user)
        mutual_follows = get_mutual_follows(current_user, user)

    return render(
        request,
        "wiki/profile.html",
        {
            "profile_user": user,
            "pages": pages,
            "following": following,
            "followers": followers,
            "is_following": is_following_user,
            "is_followed_by": is_followed_by_user,
            "mutual_follows": mutual_follows,
            "add_follow_form": AddFollowForm(),
        },
    )


@login_required
def create_wiki_page(request: HttpRequest) -> HttpResponse:
    """Create a new wiki page"""
    user = _get_authenticated_user(request)
    if request.method == "POST":
        form = WikiPageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.author = user
            page.save()

            # Create initial revision
            PageRevision.objects.create(
                page=page,
                title=page.title,
                content=page.content,
                editor=user,
                is_current=True,
            )

            # Log page creation activity
            UserActivity.objects.create(
                user=user,
                activity_type="create_page",
                page=page,
                details=f'Created page "{page.title}"',
            )

            messages.success(request, "Wiki page created successfully!")
            return redirect("user_profile", username=user.username)
    else:
        form = WikiPageForm()

    return render(request, "wiki/create_page.html", {"form": form})


@login_required
def edit_wiki_page(request: HttpRequest, page_id: int) -> HttpResponse:
    """Edit an existing wiki page"""
    user = _get_authenticated_user(request)
    page = get_object_or_404(WikiPage, id=page_id)

    # Check if user owns the page
    if page.author != user:
        messages.error(request, "You can only edit your own pages.")
        return redirect("user_profile", username=user.username)

    if request.method == "POST":
        form = WikiPageForm(request.POST, instance=page)
        if form.is_valid():
            # Get the original values from database BEFORE form processes them
            original_page = WikiPage.objects.get(pk=page.pk)
            old_title = original_page.title
            old_content = original_page.content
            new_title = form.cleaned_data["title"]
            new_content = form.cleaned_data["content"]

            # Check if content actually changed BEFORE saving
            content_changed = new_content != old_content
            title_changed = new_title != old_title

            form.save()

            # Create new revision if content changed
            if content_changed or title_changed:
                # Mark current revisions as not current
                PageRevision.objects.filter(page=page, is_current=True).update(
                    is_current=False
                )
                # Create new revision
                PageRevision.objects.create(
                    page=page,
                    title=new_title,
                    content=new_content,
                    editor=user,
                    is_current=True,
                )

            # Log page edit activity
            UserActivity.objects.create(
                user=user,
                activity_type="edit_page",
                page=page,
                details=f'Edited page "{old_title}" → "{page.title}"',
            )

            messages.success(request, "Wiki page updated successfully!")
            return redirect("user_profile", username=user.username)
    else:
        form = WikiPageForm(instance=page)

    return render(request, "wiki/edit_page.html", {"form": form, "page": page})


def view_wiki_page(request: HttpRequest, username: str, page_slug: str) -> HttpResponse:
    """View a wiki page"""
    try:
        user = UserModel.objects.get(username=username)
    except UserModel.DoesNotExist:
        raise Http404(f'User "{username}" does not exist')

    try:
        page = WikiPage.objects.get(author=user, slug=page_slug)
    except WikiPage.DoesNotExist:
        raise Http404(f'Page "{page_slug}" does not exist for user "{username}"')

    # Render markdown content with wiki link support
    html_content = render_markdown_with_wiki_links(page.content, username)

    return render(
        request,
        "wiki/view_page.html",
        {"page": page, "html_content": html_content, "username": username},
    )


@login_required
def view_revisions(request: HttpRequest, page_id: int) -> HttpResponse:
    """View all revisions of a wiki page"""
    user = _get_authenticated_user(request)
    page = get_object_or_404(WikiPage, id=page_id)

    # Check if user owns the page or is admin
    if page.author != user and not user.is_staff:
        messages.error(request, "You can only view revisions of your own pages.")
        return redirect("user_profile", username=user.username)

    revisions = PageRevision.objects.filter(page=page).order_by("-created_at")

    return render(
        request, "wiki/revisions.html", {"page": page, "revisions": revisions}
    )


@login_required
def restore_revision(
    request: HttpRequest, page_id: int, revision_id: int
) -> HttpResponse:
    """Restore a previous revision of a wiki page"""
    user = _get_authenticated_user(request)
    page = get_object_or_404(WikiPage, id=page_id)
    revision = get_object_or_404(PageRevision, id=revision_id, page=page)

    # Check if user owns the page
    if page.author != user:
        messages.error(request, "You can only restore revisions of your own pages.")
        return redirect("user_profile", username=user.username)

    if request.method == "POST":
        # Mark current revisions as not current
        PageRevision.objects.filter(page=page, is_current=True).update(is_current=False)

        # Update the page with the revision content
        page.title = revision.title
        page.content = revision.content
        page.save()

        # Create a new revision marking the restoration
        PageRevision.objects.create(
            page=page,
            title=page.title,
            content=page.content,
            editor=user,
            is_current=True,
        )

        # Log restoration activity
        UserActivity.objects.create(
            user=user,
            activity_type="edit_page",
            page=page,
            details=f'Restored page "{page.title}" to revision from {revision.created_at}',
        )

        messages.success(request, "Page restored successfully!")
        return redirect(
            "view_wiki_page", username=page.author.username, page_slug=page.slug
        )

    return render(
        request, "wiki/restore_confirm.html", {"page": page, "revision": revision}
    )


@login_required
def user_activity(request: HttpRequest, username: str) -> HttpResponse:
    """View user activity feed"""
    user = User.objects.get(username=username)

    # Get user's activity
    activities = UserActivity.objects.filter(user=user).order_by("-created_at")

    return render(
        request, "wiki/activity.html", {"profile_user": user, "activities": activities}
    )


@login_required
def delete_wiki_page(request: HttpRequest, page_id: int) -> HttpResponse:
    """Delete a wiki page"""
    user = _get_authenticated_user(request)
    page = get_object_or_404(WikiPage, id=page_id)

    # Check if user owns the page
    if page.author != user:
        messages.error(request, "You can only delete your own pages.")
        return redirect("user_profile", username=user.username)

    if request.method == "POST":
        page_title = page.title
        page.delete()

        # Log page deletion activity
        UserActivity.objects.create(
            user=user,
            activity_type="delete_page",
            details=f'Deleted page "{page_title}"',
        )

        messages.success(request, "Wiki page deleted successfully!")
        return redirect("user_profile", username=user.username)

    return render(request, "wiki/delete_page.html", {"page": page})


@login_required
def handle_invalid_wiki_link(
    request: HttpRequest, username: str, page_slug: str
) -> HttpResponse:
    """
    Handle invalid wiki links.

    If the link is to the current user's namespace, redirect to create page.
    If the link is to another user's namespace, return 404.
    """
    current_user = _get_authenticated_user(request)

    # If the link is to the current user's namespace
    if username == current_user.username:
        # Redirect to create page with the slug pre-filled
        messages.info(
            request, f'Page "{page_slug}" does not exist. Creating a new page.'
        )
        return redirect("create_wiki_page")
    else:
        # Link is to another user's namespace - 404
        raise Http404(
            f'Page "{page_slug}" does not exist in user "{username}" namespace'
        )


@login_required
def add_follow(request: HttpRequest) -> HttpResponse:
    """Follow a user"""
    user = _get_authenticated_user(request)

    if request.method == "POST":
        form = AddFollowForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]

            try:
                target_user = User.objects.get(username=username)

                # Can't follow yourself
                if target_user == user:
                    messages.error(request, "You cannot follow yourself.")
                    return redirect("user_profile", username=user.username)

                # Check if already following
                if is_following(user, target_user):
                    messages.info(request, f"You are already following {username}.")
                    return redirect("user_profile", username=user.username)

                # Create follow relationship
                Follow.objects.create(follower=user, following=target_user)
                messages.success(request, f"You are now following {username}!")

                return redirect("user_profile", username=user.username)

            except User.DoesNotExist:
                messages.error(request, f"User '{username}' does not exist.")
                return redirect("user_profile", username=user.username)

    # If not POST, redirect to profile
    return redirect("user_profile", username=user.username)


@login_required
def remove_follow(request: HttpRequest, follow_id: int) -> HttpResponse:
    """Unfollow a user"""
    user = _get_authenticated_user(request)

    try:
        target_user = User.objects.get(id=follow_id)

        # Check if they are actually following
        if not is_following(user, target_user):
            messages.error(request, f"You are not following {target_user.username}.")
            return redirect("user_profile", username=user.username)

        # Remove follow relationship
        Follow.objects.filter(follower=user, following=target_user).delete()

        messages.success(request, f"You have unfollowed {target_user.username}.")

    except User.DoesNotExist:
        messages.error(request, "User not found.")

    return redirect("user_profile", username=user.username)
