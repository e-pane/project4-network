
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    # API routes
    path("new-post", views.compose, name="compose"),
    path("posts-data", views.get_posts, name="get_posts"),
    path("profile-data/<int:user_id>", views.get_profile, name="get_profile"),
    path("follow-status/<int:user_id>", views.toggle_follow_status, name="toggle_follow_status"),
    path("follow-usernames/<str:option>", views.get_follow_usernames, name="get_follow_usernames"),
    path("like-update/<int:post_id>", views.toggle_like_status, name="toggle_like_status"),
    path("dislike-update/<int:post_id>", views.toggle_dislike_status, name="toggle_dislike_status"),
]