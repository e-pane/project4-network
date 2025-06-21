from django.contrib.auth.models import AbstractUser
from django.db import models

class Post(models.Model):
    poster = models.ForeignKey("User", on_delete=models.CASCADE, related_name="posts")
    liked_by = models.ManyToManyField("User", related_name="likes")
    disliked_by = models.ManyToManyField("User", related_name="dislikes")
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def serialize(self):
        return {
            "id": self.id,
            "poster": self.poster.username,
            "user_id": self.poster.id,
            "body": self.body,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "like_count": self.liked_by.count(),
            "dislike_count": self.disliked_by.count(),
        }

class User(AbstractUser):
    following = models.ManyToManyField("User", related_name="followers")
    
    def serialize(self):
        following = self.following.all()
        followers = self.followers.all()
        return {
            "id": self.id,
            "follower_ids" : [f.id for f in followers],
            "following_ids" : [f.id for f in following],
            "follower_usernames": [f.username for f in followers],
            "following_usernames": [f.username for f in following],
        }
    