"""
Test cases for wiki signals
"""
import pytest
from django.contrib.auth.models import User
from wiki.models import UserActivity
from wiki import signals


class TestSignupSignal:
    """Test signup signal"""
    
    def test_signup_signal_creates_activity(self, db):
        """Test that signup signal creates UserActivity"""
        # Temporarily disable signal to test it directly
        signals.post_save.disconnect(signals.create_user_activity_on_signup, sender=User)
        
        user = User.objects.create_user(username='testuser', password='testpass')
        assert not UserActivity.objects.filter(user=user, activity_type='signup').exists()
        
        # Re-enable signal and test
        signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)
        user2 = User.objects.create_user(username='testuser2', password='testpass')
        assert UserActivity.objects.filter(user=user2, activity_type='signup').exists()
    
    def test_signup_activity_details(self, db):
        """Test that signup activity has correct details"""
        signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)
        
        user = User.objects.create_user(username='testuser', password='testpass')
        activity = UserActivity.objects.get(user=user, activity_type='signup')
        
        assert 'signed up' in activity.details
        assert user.username in activity.details
    
    def test_signup_signal_only_on_create(self, db):
        """Test that signup signal only fires on user creation, not update"""
        signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)
        
        user = User.objects.create_user(username='testuser', password='testpass')
        initial_count = UserActivity.objects.filter(user=user, activity_type='signup').count()
        
        # Update user
        user.email = 'test@example.com'
        user.save()
        
        # Should still be only one signup activity
        assert UserActivity.objects.filter(user=user, activity_type='signup').count() == initial_count


class TestSignalIntegration:
    """Test signal integration"""
    
    def test_signals_connected_on_app_ready(self):
        """Test that signals are connected when app is ready"""
        from django.apps import apps
        from wiki.apps import WikiConfig
        
        # Get the wiki config
        config = apps.get_app_config('wiki')
        
        # Check that signals are connected by looking through receivers
        # post_save.receivers is a list of tuples, each containing the signal handler
        signal_connected = False
        for receiver_tuple in signals.post_save.receivers:
            # receiver_tuple[1] is the weakref to the signal handler function
            if hasattr(receiver_tuple[1], '__call__'):
                actual_function = receiver_tuple[1]()
                if actual_function == signals.create_user_activity_on_signup:
                    signal_connected = True
                    break
        
        assert signal_connected, "Signal create_user_activity_on_signup is not connected to post_save"
    
    def test_multiple_users_signup_activities(self, db):
        """Test that multiple users each get their own signup activity"""
        signals.post_save.connect(signals.create_user_activity_on_signup, sender=User)
        
        user1 = User.objects.create_user(username='user1', password='testpass')
        user2 = User.objects.create_user(username='user2', password='testpass')
        
        assert UserActivity.objects.filter(user=user1, activity_type='signup').exists()
        assert UserActivity.objects.filter(user=user2, activity_type='signup').exists()
        
        # Each user should have exactly one signup activity
        assert UserActivity.objects.filter(user=user1, activity_type='signup').count() == 1
        assert UserActivity.objects.filter(user=user2, activity_type='signup').count() == 1
