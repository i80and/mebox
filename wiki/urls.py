from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path("signup/", views.signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    # Wiki page URLs
    path("user/<str:username>/", views.user_profile, name="user_profile"),
    path("user/<str:username>/activity/", views.user_activity, name="user_activity"),
    path(
        "user/<str:username>/<slug:page_slug>/",
        views.view_wiki_page,
        name="view_wiki_page",
    ),
    path("create/", views.create_wiki_page, name="create_wiki_page"),
    path("edit/<int:page_id>/", views.edit_wiki_page, name="edit_wiki_page"),
    path("delete/<int:page_id>/", views.delete_wiki_page, name="delete_wiki_page"),
    # Revision URLs
    path("page/<int:page_id>/revisions/", views.view_revisions, name="view_revisions"),
    path(
        "page/<int:page_id>/revisions/<int:revision_id>/restore/",
        views.restore_revision,
        name="restore_revision",
    ),
]
