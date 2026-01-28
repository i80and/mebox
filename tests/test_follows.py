"""Tests for follow functionality"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from wiki.models import (
    Follow,
    get_following,
    get_followers,
    is_following,
    get_mutual_follows,
)


@pytest.mark.django_db
def test_follow_model_creation(user, second_user):
    """Test creating a follow relationship"""
    # Create follow
    follow = Follow.objects.create(follower=user, following=second_user)

    # Check fields
    assert follow.follower == user
    assert follow.following == second_user

    # Check string representation
    assert str(follow) == f"{user.username} follows {second_user.username}"


@pytest.mark.django_db
def test_get_following(user, second_user):
    """Test getting users that a user is following"""
    # Create a third user
    user3 = User.objects.create_user(username="user3", password="testpass3")

    # Create follows
    Follow.objects.create(follower=user, following=second_user)
    Follow.objects.create(follower=user, following=user3)

    # Get following for user
    following = get_following(user)

    # Should return both second_user and user3
    assert following.count() == 2
    following_usernames = [f.username for f in following]
    assert second_user.username in following_usernames
    assert user3.username in following_usernames


@pytest.mark.django_db
def test_get_followers(user, second_user):
    """Test getting users that follow a user"""
    # Create a third user
    user3 = User.objects.create_user(username="user3", password="testpass3")

    # Create follows
    Follow.objects.create(follower=user, following=second_user)
    Follow.objects.create(follower=user3, following=second_user)

    # Get followers for second_user
    followers = get_followers(second_user)

    # Should return both user and user3
    assert followers.count() == 2
    follower_usernames = [f.username for f in followers]
    assert user.username in follower_usernames
    assert user3.username in follower_usernames


@pytest.mark.django_db
def test_is_following(user, second_user):
    """Test checking if user is following another user"""
    # Create a third user
    user3 = User.objects.create_user(username="user3", password="testpass3")

    # Create follow between user and second_user
    Follow.objects.create(follower=user, following=second_user)

    # Check that user is following second_user
    assert is_following(user, second_user)

    # Check that second_user is not following user
    assert not is_following(second_user, user)

    # Check that user is not following user3
    assert not is_following(user, user3)
    assert not is_following(user3, user)


@pytest.mark.django_db
def test_get_mutual_follows(user, second_user):
    """Test getting mutual follows between two users"""
    # Create third and fourth users
    user3 = User.objects.create_user(username="user3", password="testpass3")
    user4 = User.objects.create_user(username="user4", password="testpass4")

    # Create follows: user follows user3 and user4
    Follow.objects.create(follower=user, following=user3)
    Follow.objects.create(follower=user, following=user4)

    # Create follows: second_user follows user3 and user4
    Follow.objects.create(follower=second_user, following=user3)
    Follow.objects.create(follower=second_user, following=user4)

    # Get mutual follows
    mutuals = get_mutual_follows(user, second_user)

    # Should return both user3 and user4
    assert mutuals.count() == 2
    mutual_usernames = [f.username for f in mutuals]
    assert user3.username in mutual_usernames
    assert user4.username in mutual_usernames


@pytest.mark.django_db
def test_add_follow_view(client, user, second_user):
    """Test following a user via the add_follow view"""
    client.force_login(user)

    # POST to add_follow with second_user's username
    response = client.post(
        reverse("add_follow"), {"username": second_user.username}, follow=True
    )

    # Should redirect to user's profile
    assert response.status_code == 200

    # Check that follow was created
    assert Follow.objects.filter(follower=user, following=second_user).exists()

    # Check that following is returned
    following = get_following(user)
    assert following.count() == 1
    assert second_user in following


@pytest.mark.django_db
def test_add_self_follow_fails(client, user):
    """Test that a user cannot follow themselves"""
    client.force_login(user)

    # Try to follow self
    response = client.post(
        reverse("add_follow"), {"username": user.username}, follow=True
    )

    # Should redirect to profile
    assert response.status_code == 200

    # Should not create follow
    assert Follow.objects.count() == 0


@pytest.mark.django_db
def test_add_nonexistent_user_follow(client, user):
    """Test following a non-existent user"""
    client.force_login(user)

    # Try to follow non-existent user
    response = client.post(
        reverse("add_follow"), {"username": "nonexistentuser"}, follow=True
    )

    # Should redirect to profile
    assert response.status_code == 200

    # Should not create follow
    assert Follow.objects.count() == 0


@pytest.mark.django_db
def test_remove_follow_view(client, user, second_user):
    """Test unfollowing a user via the remove_follow view"""
    client.force_login(user)

    # First create a follow
    Follow.objects.create(follower=user, following=second_user)

    # Verify follow exists
    assert Follow.objects.count() == 1

    # Remove the follow
    response = client.post(reverse("remove_follow", args=[second_user.id]), follow=True)

    # Should redirect to user's profile
    assert response.status_code == 200

    # Check that follow was removed
    assert Follow.objects.count() == 0


@pytest.mark.django_db
def test_remove_non_follow(client, user, second_user):
    """Test removing a user who is not being followed"""
    client.force_login(user)

    # Don't create a follow
    assert Follow.objects.count() == 0

    # Try to remove second_user follow
    response = client.post(reverse("remove_follow", args=[second_user.id]), follow=True)

    # Should redirect to profile
    assert response.status_code == 200

    # Should still have no follows
    assert Follow.objects.count() == 0


@pytest.mark.django_db
def test_profile_page_shows_following(client, user, second_user):
    """Test that profile page shows following"""
    client.force_login(user)

    # Create a third user
    user3 = User.objects.create_user(username="user3", password="testpass3")

    # Create follows
    Follow.objects.create(follower=user, following=second_user)
    Follow.objects.create(follower=user, following=user3)

    # Visit profile page
    response = client.get(reverse("user_profile", args=[user.username]))

    # Check response
    assert response.status_code == 200

    # Check that following is in context
    assert "following" in response.context
    assert response.context["following"].count() == 2
    following_usernames = [f.username for f in response.context["following"]]
    assert second_user.username in following_usernames
    assert user3.username in following_usernames


@pytest.mark.django_db
def test_profile_page_shows_follow_status(client, user, second_user):
    """Test that profile page shows follow status for other users"""
    client.force_login(user)

    # Visit second_user's profile (not following yet)
    response = client.get(reverse("user_profile", args=[second_user.username]))

    # Check that is_following is False
    assert response.status_code == 200
    assert "is_following" in response.context
    assert not response.context["is_following"]

    # Now create follow
    Follow.objects.create(follower=user, following=second_user)

    # Visit second_user's profile again
    response = client.get(reverse("user_profile", args=[second_user.username]))

    # Check that is_following is now True
    assert response.status_code == 200
    assert response.context["is_following"]


@pytest.mark.django_db
def test_add_follow_form_in_context(client, user, second_user):
    """Test that add_follow_form is in context"""
    client.force_login(user)

    # Visit second_user's profile
    response = client.get(reverse("user_profile", args=[second_user.username]))

    # Check that add_follow_form is in context
    assert response.status_code == 200
    assert "add_follow_form" in response.context


@pytest.mark.django_db
def test_cannot_add_duplicate_follow(client, user, second_user):
    """Test that a user cannot follow the same user twice"""
    client.force_login(user)

    # Create first follow
    Follow.objects.create(follower=user, following=second_user)

    # Try to follow the same user again
    response = client.post(
        reverse("add_follow"), {"username": second_user.username}, follow=True
    )

    # Should redirect to profile
    assert response.status_code == 200

    # Should still only have one follow
    assert Follow.objects.count() == 1


@pytest.mark.django_db
def test_mutual_follows_display(client, user, second_user):
    """Test that mutual follows are displayed correctly"""
    client.force_login(user)

    # Create third user
    user3 = User.objects.create_user(username="user3", password="testpass3")

    # Create follows: user follows user3
    Follow.objects.create(follower=user, following=user3)

    # Create follows: second_user follows user3
    Follow.objects.create(follower=second_user, following=user3)

    # Visit second_user's profile
    response = client.get(reverse("user_profile", args=[second_user.username]))

    # Check that mutual_follows is in context
    assert response.status_code == 200
    assert "mutual_follows" in response.context
    assert response.context["mutual_follows"].count() == 1
    assert user3 in response.context["mutual_follows"]


@pytest.mark.django_db
def test_mutual_follows_bidirectional(client, user, second_user):
    """Test that mutual follows are shown when two users follow each other"""
    client.force_login(user)

    # Create follows: user follows second_user
    Follow.objects.create(follower=user, following=second_user)

    # Create follows: second_user follows user (mutual)
    Follow.objects.create(follower=second_user, following=user)

    # Visit second_user's profile
    response = client.get(reverse("user_profile", args=[second_user.username]))

    # Check that both is_following and is_followed_by are True
    assert response.status_code == 200
    assert response.context["is_following"]
    assert response.context["is_followed_by"]

    # Visit user's profile from second_user's perspective
    client.force_login(second_user)
    response = client.get(reverse("user_profile", args=[user.username]))

    # Check that both is_following and is_followed_by are True
    assert response.status_code == 200
    assert response.context["is_following"]
    assert response.context["is_followed_by"]
