from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WikiPage
from .forms import WikiPageForm
import markdown_it

md = markdown_it.MarkdownIt()

def home(request):
    """Home page showing recent wiki pages"""
    pages = WikiPage.objects.all().order_by('-created_at')[:10]
    return render(request, 'wiki/home.html', {'pages': pages})

def signup(request):
    """User signup view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'wiki/signup.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'wiki/login.html', {'form': form})

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def user_profile(request, username):
    """User profile page"""
    from django.contrib.auth.models import User
    user = User.objects.get(username=username)
    
    # Get user's wiki pages
    pages = WikiPage.objects.filter(author=user).order_by('-created_at')
    
    return render(request, 'wiki/profile.html', {
        'profile_user': user,
        'pages': pages
    })

@login_required
def create_wiki_page(request):
    """Create a new wiki page"""
    if request.method == 'POST':
        form = WikiPageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.author = request.user
            page.save()
            messages.success(request, 'Wiki page created successfully!')
            return redirect('user_profile', username=request.user.username)
    else:
        form = WikiPageForm()
    
    return render(request, 'wiki/create_page.html', {'form': form})

@login_required
def edit_wiki_page(request, page_id):
    """Edit an existing wiki page"""
    page = WikiPage.objects.get(id=page_id)
    
    # Check if user owns the page
    if page.author != request.user:
        messages.error(request, 'You can only edit your own pages.')
        return redirect('user_profile', username=request.user.username)
    
    if request.method == 'POST':
        form = WikiPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, 'Wiki page updated successfully!')
            return redirect('user_profile', username=request.user.username)
    else:
        form = WikiPageForm(instance=page)
    
    return render(request, 'wiki/edit_page.html', {'form': form, 'page': page})

def view_wiki_page(request, username, page_slug):
    """View a wiki page"""
    from django.contrib.auth.models import User
    
    user = User.objects.get(username=username)
    page = WikiPage.objects.get(author=user, slug=page_slug)
    
    # Render markdown content
    html_content = md.render(page.content)
    
    return render(request, 'wiki/view_page.html', {
        'page': page,
        'html_content': html_content
    })

@login_required
def delete_wiki_page(request, page_id):
    """Delete a wiki page"""
    page = WikiPage.objects.get(id=page_id)
    
    # Check if user owns the page
    if page.author != request.user:
        messages.error(request, 'You can only delete your own pages.')
        return redirect('user_profile', username=request.user.username)
    
    if request.method == 'POST':
        page.delete()
        messages.success(request, 'Wiki page deleted successfully!')
        return redirect('user_profile', username=request.user.username)
    
    return render(request, 'wiki/delete_page.html', {'page': page})
