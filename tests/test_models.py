"""
Test cases for wiki models
"""
import pytest
from django.contrib.auth.models import User
from wiki.models import WikiPage, PageRevision, UserActivity


class TestPageRevisionModel:
    """Test PageRevision model"""
    
    def test_pagerevision_creation(self, db, user, wiki_page):
        """Test that PageRevision is created properly"""
        revision = PageRevision.objects.create(
            page=wiki_page, 
            title='Test Revision', 
            content='Revision content', 
            editor=user, 
            is_current=True
        )
        assert revision.page == wiki_page
        assert revision.title == 'Test Revision'
        assert revision.content == 'Revision content'
        assert revision.editor == user
        assert revision.is_current is True
    
    def test_pagerevision_str(self, db, user, wiki_page):
        """Test PageRevision string representation"""
        revision = PageRevision.objects.create(
            page=wiki_page, 
            title='Test Page', 
            content='Content', 
            editor=user, 
            is_current=True
        )
        assert str(revision) == f"Revision of 'Test Page' by {user.username}"
    
    def test_pagerevision_ordering(self, db, user, wiki_page):
        """Test that PageRevision is ordered by created_at descending"""
        # Create revisions in different order
        rev1 = PageRevision.objects.create(
            page=wiki_page, 
            title='First', 
            content='First content', 
            editor=user, 
            is_current=False
        )
        rev2 = PageRevision.objects.create(
            page=wiki_page, 
            title='Second', 
            content='Second content', 
            editor=user, 
            is_current=True
        )
        
        revisions = PageRevision.objects.all()
        assert list(revisions) == [rev2, rev1]


class TestUserActivityModel:
    """Test UserActivity model"""
    
    def test_useractivity_creation(self, db, user):
        """Test that UserActivity is created properly"""
        activity = UserActivity.objects.create(
            user=user, 
            activity_type='create_page', 
            details='Created test page'
        )
        assert activity.user == user
        assert activity.activity_type == 'create_page'
        assert activity.details == 'Created test page'
    
    def test_useractivity_get_latest_by(self, db, user):
        """Test that UserActivity has get_latest_by set"""
        UserActivity.objects.create(
            user=user, 
            activity_type='login', 
            details='Login 1'
        )
        UserActivity.objects.create(
            user=user, 
            activity_type='login', 
            details='Login 2'
        )
        latest = UserActivity.objects.latest()
        assert latest.details == 'Login 2'
    
    def test_useractivity_activity_types(self, db, user):
        """Test all activity types"""
        activity_types = ['create_page', 'edit_page', 'delete_page', 'login', 'signup']
        
        for activity_type in activity_types:
            activity = UserActivity.objects.create(
                user=user, 
                activity_type=activity_type, 
                details=f'Test {activity_type}'
            )
            assert activity.get_activity_type_display()
    
    def test_useractivity_ordering(self, db, user):
        """Test that UserActivity is ordered by created_at descending"""
        # Temporarily disable signup signal
        from wiki import signals
        signals.post_save.disconnect(signals.create_user_activity_on_signup, sender=User)
        
        # Create activities without using signals to avoid extra signup activity
        activity1 = UserActivity.objects.create(
            user=user, 
            activity_type='login', 
            details='First login'
        )
        activity2 = UserActivity.objects.create(
            user=user, 
            activity_type='login', 
            details='Second login'
        )
        
        activities = UserActivity.objects.all()
        # Should have exactly 2 login activities (no signup activity)
        assert len(activities) == 2
        assert list(activities) == [activity2, activity1]
        
        # Re-enable signal
        signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)


class TestWikiPageModel:
    """Test WikiPage model"""
    
    def test_wikipage_creation(self, db, user):
        """Test that WikiPage is created properly"""
        page = WikiPage.objects.create(
            title='Test Page',
            content='# Test Content',
            author=user
        )
        assert page.title == 'Test Page'
        assert page.content == '# Test Content'
        assert page.author == user
        assert page.slug == 'test-page'
    
    def test_wikipage_slug_generation(self, db, user):
        """Test that slug is generated from title"""
        page = WikiPage.objects.create(
            title='My Test Page',
            content='# Content',
            author=user
        )
        assert page.slug == 'my-test-page'
    
    def test_wikipage_unique_slug(self, db, user):
        """Test that duplicate slugs get numbered suffix"""
        WikiPage.objects.create(
            title='Test Page',
            content='# Content 1',
            author=user
        )
        page2 = WikiPage.objects.create(
            title='Test Page',
            content='# Content 2',
            author=user
        )
        assert page2.slug == 'test-page-1'
    
    def test_wikipage_get_absolute_url(self, db, user):
        """Test get_absolute_url method"""
        page = WikiPage.objects.create(
            title='Test Page',
            content='# Content',
            author=user
        )
        url = page.get_absolute_url()
        assert url == f'/user/{user.username}/{page.slug}/'
    
    def test_wikipage_get_current_revision(self, db, user):
        """Test get_current_revision method"""
        page = WikiPage.objects.create(
            title='Test Page',
            content='# Content',
            author=user
        )
        
        # No revisions initially
        assert page.get_current_revision() is None
        
        # Add a revision
        revision = PageRevision.objects.create(
            page=page,
            title='Test Page',
            content='# Content',
            editor=user,
            is_current=True
        )
        
        assert page.get_current_revision() == revision


class TestModelRelationships:
    """Test relationships between models"""
    
    def test_wikipage_has_many_revisions(self, db, user):
        """Test that a WikiPage can have multiple revisions"""
        page = WikiPage.objects.create(
            title='Test Page',
            content='# Version 1',
            author=user
        )
        
        PageRevision.objects.create(
            page=page,
            title='Test Page',
            content='# Version 1',
            editor=user,
            is_current=True
        )
        
        PageRevision.objects.create(
            page=page,
            title='Test Page',
            content='# Version 2',
            editor=user,
            is_current=False
        )
        
        assert page.revisions.count() == 2
    
    def test_user_has_many_activities(self, db, user):
        """Test that a User can have multiple activities"""
        # Temporarily disable signup signal
        from wiki import signals
        signals.post_save.disconnect(signals.create_user_activity_on_signup, sender=User)
        
        # Create activities without using signals to avoid extra signup activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            details='First login'
        )
        UserActivity.objects.create(
            user=user,
            activity_type='create_page',
            details='Created page'
        )
        
        # Should have exactly 2 activities (no signup activity)
        assert user.activities.count() == 2
        
        # Re-enable signal
        signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)
    
    def test_useractivity_can_reference_page(self, db, user):
        """Test that UserActivity can reference a WikiPage"""
        page = WikiPage.objects.create(
            title='Test Page',
            content='# Content',
            author=user
        )
        
        activity = UserActivity.objects.create(
            user=user,
            activity_type='create_page',
            page=page,
            details='Created test page'
        )
        
        assert activity.page == page
