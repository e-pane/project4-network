import pytest
from network.models import User, Post

def test_post_serialize_outputs_expected_fields(db):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    post = Post.objects.create(
        poster = user,
        body = "Test post body"
    )
    serialized_post = post.serialize()

    assert isinstance(serialized_post,dict)
    assert "id" in serialized_post
    assert "poster" in serialized_post
    assert "body" in serialized_post
    assert isinstance(serialized_post["id"],int)
    assert isinstance(serialized_post["like_count"],int)
    assert serialized_post["like_count"] == 0
    assert isinstance(serialized_post["timestamp"],str)

def test_user_serialize_outputs_expected_fields(db):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )

    follower1 = User.objects.create_user(
        username="testfollower1",
        email="test@example.com",
        password="password123"
    )

    follower2 = User.objects.create_user(
        username="testfollower2",
        email="test@example.com",
        password="password123"
    )

    follower1.following.add(user)
    follower2.following.add(user)

    user_data = user.serialize()

    assert isinstance(user_data,dict)
    assert "id" in user_data
    assert "follower_usernames" in user_data
    assert "following_ids" in user_data
    assert isinstance(user_data["following_ids"],list)
    assert all(isinstance(i,int) for i in user_data["following_ids"])
    assert isinstance(user_data["following_usernames"],list)
    assert all(isinstance(i,str) for i in user_data["following_usernames"])
    assert follower1.username in user_data["follower_usernames"]
    assert follower2.username in user_data["follower_usernames"]
    assert user_data["following_usernames"] ==[]

def test_user_serialize_with_no_followers_or_following(db):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )

    user_data = user.serialize()

    assert user_data["follower_ids"] == []
    assert user_data["following_ids"] == []
    assert user_data["follower_usernames"] == []
    assert user_data["following_usernames"] == []

def test_post_serialize_with_likes_and_dislikes(db):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    post = Post.objects.create(
        poster = user,
        body = "Test post body"
    )

    reactor1 = User.objects.create_user(
        username="testreactor",
        email="test@example.com",
        password="password123"
    )

    reactor2 = User.objects.create_user(
        username="testreactor2",
        email="test@example.com",
        password="password123"
    )

    post.liked_by.add(reactor1,reactor2)
    post.disliked_by.add(reactor1,reactor2)

    post_data = post.serialize()
    
    assert post_data["like_count"] == 2
    assert post_data["dislike_count"] == 2
    
def test_user_serialize_with_mutual_following(db):
    user1 = User.objects.create_user(
        username="testuser1",
        email="test@example.com",
        password="password123"
    )

    user2 = User.objects.create_user(
        username="testuser2",
        email="test@example.com",
        password="password123"
    )

    user1.following.add(user2)
    user2.following.add(user1)

    user1_data = user1.serialize()
    user2_data = user2.serialize()

    assert len(user1_data["follower_usernames"]) == 1
    assert len(user2_data["following_usernames"]) == 1
    assert len(user1_data["follower_ids"]) == 1
    assert len(user2_data["following_ids"]) == 1
    assert user1.username in user2_data["follower_usernames"]
    assert user1.id in user2_data["follower_ids"]
    assert user2.username in user1_data["follower_usernames"]
    assert user2.id in user1_data["follower_ids"]
    assert user1.username in user2_data["following_usernames"]
    assert user1.id in user2_data["following_ids"]
    assert user2.username in user1_data["following_usernames"]
    assert user2.id in user1_data["following_ids"]

def test_post_serialize_with_empty_body(db):
    user = User.objects.create_user(
    username="testuser",
    email="test@example.com",
    password="password123"
    )
    post = Post.objects.create(
    poster = user,
    body = ""
    )
    post_data = post.serialize()

    assert post_data["body"] == ""
    assert isinstance(post_data,dict)
    assert "id" in post_data
    assert "poster" in post_data
    assert isinstance(post_data["id"],int)
    assert isinstance(post_data["like_count"],int)
    assert post_data["like_count"] == 0
    assert isinstance(post_data["timestamp"],str)

def test_user_deletion_cascades_to_posts(db):
    user = User.objects.create_user(
    username="testuser",
    email="test@example.com",
    password="password123"
    )
    post1 = Post.objects.create(
    poster = user,
    body = "Test body"
    )
    post2 = Post.objects.create(
    poster = user,
    body = "Test body"
    )

    assert user.posts.count() == 2

    user.delete()

    assert Post.objects.count() == 0