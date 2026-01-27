import pytest
from django.test import Client
from django.contrib.auth.models import User
from wiki.models import WikiPage, PageRevision, UserActivity

@pytest.fixture
def client():
    """Provide a Django test client"""
    return Client()

@pytest.fixture
def user(db):
    """Create a test user"""
    # Temporarily disable signup signal
    from wiki import signals
    signals.post_save.disconnect(signals.create_user_activity_on_signup, sender=User)
    
    user = User.objects.create_user(username='testuser', password='testpass')
    
    # Re-enable signal
    signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)
    
    return user

@pytest.fixture
def admin_user(db):
    """Create a test admin user"""
    return User.objects.create_superuser(
        username='admin', 
        password='adminpass',
        email='admin@test.com'
    )

@pytest.fixture
def wiki_page(db, user):
    """Create a test wiki page"""
    return WikiPage.objects.create(
        title='Test Page',
        content='# Test Content',
        author=user
    )

@pytest.fixture
def page_revision(db, wiki_page, user):
    """Create a test page revision"""
    return PageRevision.objects.create(
        page=wiki_page,
        title='Test Page',
        content='# Test Content',
        editor=user,
        is_current=True
    )

@pytest.fixture
def user_activity(db, user):
    """Create a test user activity"""
    return UserActivity.objects.create(
        user=user,
        activity_type='create_page',
        details='Test activity'
    )

@pytest.fixture
def logged_in_client(client, user):
    """Provide a client logged in as test user"""
    client.login(username='testuser', password='testpass')
    return client

@pytest.fixture
def logged_in_admin_client(client, admin_user):
    """Provide a client logged in as admin"""
    client.login(username='admin', password='adminpass')
    return client

@pytest.fixture
def second_user(db):
    """Create a second test user for permission tests"""
    return User.objects.create_user(username='user2', password='testpass2')
