"""
Integration tests for wiki functionality
"""

import pytest
from django.contrib.auth.models import User
from wiki.models import WikiPage, PageRevision, UserActivity


class TestFullWorkflow:
    """Test complete user workflows"""

    @pytest.mark.django_db
    def test_complete_workflow(self, client):
        """Test complete workflow: signup → create → edit → view history → restore → delete"""
        # Signup
        response = client.post(
            "/signup/",
            {
                "username": "workflowuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        assert response.status_code == 302
        assert UserActivity.objects.filter(activity_type="signup").exists()

        # Login
        response = client.post(
            "/login/", {"username": "workflowuser", "password": "testpass123"}
        )
        assert response.status_code == 302
        assert UserActivity.objects.filter(activity_type="login").exists()

        # Create page
        response = client.post(
            "/create/", {"title": "Workflow Test Page", "content": "# Version 1"}
        )
        assert response.status_code == 302
        page = WikiPage.objects.get(title="Workflow Test Page")
        assert PageRevision.objects.filter(page=page).count() == 1
        assert UserActivity.objects.filter(activity_type="create_page").exists()

        # Edit page
        response = client.post(
            f"/edit/{page.id}/",
            {"title": "Workflow Test Page", "content": "# Version 2"},
        )
        assert response.status_code == 302
        assert PageRevision.objects.filter(page=page).count() == 2
        assert UserActivity.objects.filter(activity_type="edit_page").exists()

        # View revisions
        response = client.get(f"/page/{page.id}/revisions/")
        assert response.status_code == 200
        assert b"Revision History" in response.content

        # Restore old version
        old_revision = PageRevision.objects.filter(
            page=page, content="# Version 1"
        ).first()
        assert old_revision is not None
        response = client.post(f"/page/{page.id}/revisions/{old_revision.id}/restore/")
        assert response.status_code == 302
        page.refresh_from_db()
        assert page.content == "# Version 1"
        assert UserActivity.objects.filter(activity_type="edit_page").count() >= 2

        # Delete page
        response = client.post(f"/delete/{page.id}/")
        assert response.status_code == 302
        assert not WikiPage.objects.filter(id=page.id).exists()
        assert UserActivity.objects.filter(activity_type="delete_page").exists()

        # Verify activity feed
        response = client.get("/user/workflowuser/activity/")
        assert response.status_code == 200
        assert (
            UserActivity.objects.filter(user__username="workflowuser").count() >= 5
        )  # signup, login, create, edit, delete


class TestMultiplePages:
    """Test handling multiple pages by same user"""

    @pytest.mark.django_db
    def test_user_with_multiple_pages(self, client):
        """Test that a user can create and manage multiple pages"""
        # Signup and login
        client.post(
            "/signup/",
            {
                "username": "multipageuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        client.post("/login/", {"username": "multipageuser", "password": "testpass123"})

        # Create multiple pages
        for i in range(3):
            response = client.post(
                "/create/", {"title": f"Page {i + 1}", "content": f"# Content {i + 1}"}
            )
            assert response.status_code == 302

        # Check that all pages exist
        user = User.objects.get(username="multipageuser")
        assert WikiPage.objects.filter(author=user).count() == 3

        # Check that each page has a revision
        for page in WikiPage.objects.filter(author=user):
            assert PageRevision.objects.filter(page=page).count() >= 1

        # Check that activity was logged for each creation
        assert (
            UserActivity.objects.filter(user=user, activity_type="create_page").count()
            == 3
        )

        # View user profile
        response = client.get(f"/user/{user.username}/")
        assert response.status_code == 200
        assert b"Page 1" in response.content
        assert b"Page 2" in response.content
        assert b"Page 3" in response.content


class TestRevisionHistory:
    """Test comprehensive revision history functionality"""

    @pytest.mark.django_db
    def test_extensive_revision_history(self, client):
        """Test that extensive editing creates proper revision history"""
        # Signup and login
        client.post(
            "/signup/",
            {
                "username": "revisionuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        client.post("/login/", {"username": "revisionuser", "password": "testpass123"})

        # Create page
        client.post("/create/", {"title": "Revision Test", "content": "# Version 1"})
        page = WikiPage.objects.get(title="Revision Test")

        # Edit multiple times
        for i in range(5):
            client.post(
                f"/edit/{page.id}/",
                {"title": "Revision Test", "content": f"# Version {i + 2}"},
            )

        # Check that we have 6 revisions total (1 initial + 5 edits)
        assert PageRevision.objects.filter(page=page).count() == 6

        # Check that only the latest is marked as current
        current_revisions = PageRevision.objects.filter(page=page, is_current=True)
        assert current_revisions.count() == 1
        current_rev = current_revisions.first()
        assert current_rev is not None
        assert current_rev.content == "# Version 6"

        # Check that we can view all revisions
        response = client.get(f"/page/{page.id}/revisions/")
        assert response.status_code == 200

        # Test restoring to middle version
        middle_revision = PageRevision.objects.filter(
            page=page, content="# Version 3"
        ).first()
        assert middle_revision is not None
        client.post(f"/page/{page.id}/revisions/{middle_revision.id}/restore/")

        page.refresh_from_db()
        assert page.content == "# Version 3"

        # Check that a new revision was created for the restoration
        assert PageRevision.objects.filter(page=page).count() == 7
        latest_revision = PageRevision.objects.filter(
            page=page, is_current=True
        ).first()
        assert latest_revision is not None
        assert latest_revision.content == "# Version 3"


class TestPermissionBoundary:
    """Test permission boundaries between users"""

    @pytest.mark.django_db
    def test_users_cannot_interfere_with_each_other(self, client):
        """Test that users cannot access or modify each other's content"""
        # Create two users
        client.post(
            "/signup/",
            {
                "username": "user1",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        client.post(
            "/signup/",
            {
                "username": "user2",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )

        # User1 creates a page
        client.post("/login/", {"username": "user1", "password": "testpass123"})
        client.post("/create/", {"title": "User1 Page", "content": "# User1 Content"})
        page1 = WikiPage.objects.get(title="User1 Page")

        # User2 creates a page
        client.post("/logout/")
        client.post("/login/", {"username": "user2", "password": "testpass123"})
        client.post("/create/", {"title": "User2 Page", "content": "# User2 Content"})
        page2 = WikiPage.objects.get(title="User2 Page")

        # User2 should not be able to edit User1's page
        response = client.get(f"/edit/{page1.id}/")
        assert response.status_code == 302  # Redirect to their own profile

        # User2 should not be able to delete User1's page
        response = client.get(f"/delete/{page1.id}/")
        assert response.status_code == 302  # Redirect to their own profile

        # User2 should not be able to view User1's revisions
        response = client.get(f"/page/{page1.id}/revisions/")
        assert response.status_code == 302  # Redirect to their own profile

        # User2 should not be able to restore User1's revisions
        revision = PageRevision.objects.filter(page=page1).first()
        assert revision is not None
        response = client.post(f"/page/{page1.id}/revisions/{revision.id}/restore/")
        assert response.status_code == 302  # Redirect to their own profile

        # Verify both pages still exist and are unchanged
        page1.refresh_from_db()
        page2.refresh_from_db()
        assert page1.content == "# User1 Content"
        assert page2.content == "# User2 Content"


class TestDataIntegrity:
    """Test data integrity across operations"""

    @pytest.mark.django_db
    def test_revision_integrity(self, client):
        """Test that revision data remains intact across operations"""
        # Signup and login
        client.post(
            "/signup/",
            {
                "username": "integrityuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        client.post("/login/", {"username": "integrityuser", "password": "testpass123"})

        # Create page with specific content
        original_content = """# Main Title

## Section 1

This is the first section.

## Section 2

This is the second section.
"""
        client.post(
            "/create/", {"title": "Integrity Test", "content": original_content}
        )
        page = WikiPage.objects.get(title="Integrity Test")

        # Edit the page
        edited_content = """# Main Title

## Section 1

This is the **edited** first section.

## Section 2

This is the second section.
"""
        client.post(
            f"/edit/{page.id}/", {"title": "Integrity Test", "content": edited_content}
        )

        # Restore to original - get the first revision (which should be the original)
        old_revision = (
            PageRevision.objects.filter(page=page).order_by("created_at").first()
        )
        assert old_revision is not None
        client.post(f"/page/{page.id}/revisions/{old_revision.id}/restore/")

        # Verify original content is restored exactly
        page.refresh_from_db()
        assert page.content == original_content.strip()

        # Verify we can still access the edited version
        edited_revision = PageRevision.objects.filter(
            page=page, content__contains="**edited**"
        ).first()
        assert edited_revision is not None
        assert "**edited**" in edited_revision.content

        # Verify the current revision is marked correctly
        current_revision = PageRevision.objects.filter(
            page=page, is_current=True
        ).first()
        assert current_revision is not None
        assert current_revision.content.strip() == original_content.strip()


class TestPerformance:
    """Test performance with large datasets"""

    @pytest.mark.django_db
    def test_many_revisions_performance(self, client):
        """Test that many revisions don't break the system"""
        # Signup and login
        client.post(
            "/signup/",
            {
                "username": "performanceuser",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        client.post(
            "/login/", {"username": "performanceuser", "password": "testpass123"}
        )

        # Create page
        client.post("/create/", {"title": "Performance Test", "content": "# Version 1"})
        page = WikiPage.objects.get(title="Performance Test")

        # Create many revisions (50)
        for i in range(2, 51):
            client.post(
                f"/edit/{page.id}/",
                {"title": "Performance Test", "content": f"# Version {i}"},
            )

        # Verify all revisions exist
        assert PageRevision.objects.filter(page=page).count() == 50

        # Verify we can still view the page
        response = client.get("/user/performanceuser/performance-test/")
        assert response.status_code == 200

        # Verify we can still view revisions
        response = client.get(f"/page/{page.id}/revisions/")
        assert response.status_code == 200

        # Verify we can still edit the page
        response = client.post(
            f"/edit/{page.id}/",
            {"title": "Performance Test", "content": "# Final Version"},
        )
        assert response.status_code == 302

        # Verify we have 51 revisions now
        assert PageRevision.objects.filter(page=page).count() == 51
