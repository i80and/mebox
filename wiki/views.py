from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from .models import WikiPage, PageRevision, UserActivity
from .forms import WikiPageForm
import markdown_it

md = markdown_it.MarkdownIt()


def _get_authenticated_user(request: HttpRequest) -> User:
    """Helper to get authenticated user from request"""
    # This is safe because the views are decorated with @login_required
    return request.user  # type: ignore[attr-defined]


def home(request: HttpRequest) -> HttpResponse:
    """Home page showing recent wiki pages"""
    pages = WikiPage.objects.all().order_by("-created_at")[:10]
    return render(request, "wiki/home.html", {"pages": pages})


def signup(request: HttpRequest) -> HttpResponse:
    """User signup view"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
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

    # Get user's wiki pages
    pages = WikiPage.objects.filter(author=user).order_by("-created_at")

    return render(request, "wiki/profile.html", {"profile_user": user, "pages": pages})


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
    user = User.objects.get(username=username)
    page = WikiPage.objects.get(author=user, slug=page_slug)

    # Render markdown content
    html_content = md.render(page.content)

    return render(
        request, "wiki/view_page.html", {"page": page, "html_content": html_content}
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
