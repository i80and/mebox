from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserActivity
from typing import Any


@receiver(post_save, sender=User)
def create_user_activity_on_signup(
    sender: type[User], instance: User, created: bool, **kwargs: Any
) -> None:
    """Create activity when a user signs up"""
    if created:
        UserActivity.objects.create(
            user=instance,
            activity_type="signup",
            details=f"User {instance.username} signed up",
        )


# Import this module to connect signals
import django.db.models.signals
import django.dispatch.dispatcher
from django.apps import apps

# Connect the signal
post_save.connect(create_user_activity_on_signup, sender=User)
