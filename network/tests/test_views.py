import pytest
from django.urls import reverse
from network.models import User, Post
import json

@pytest.fixture
def user_factory(): # fixture to create a user instance in the db with creds.  create_user is specific to 
                    # AbstractUser subclass
    def create_user(username):
        user = User.objects.create_user( 
            username=username, 
            email="test@example.com", 
            password="password123"
        )
        return user
    return create_user

@pytest.fixture  # fixture to mock up a json payload of poster and post content("body") to be sent in the body
                 # of the HTTP request
def post_data(): 
    def create_post_data(poster, body = "Test post body"):
        if poster:
            data = {
                "poster": poster.username,
                "body": body,
            }
        else: 
            data = {
                "body": body,
            }
        return data
    return create_post_data

def reverse_django_url(view_name, args=None, kwargs=None): # utility to build reverse URLs
    reverse_url = reverse(view_name, args = args, kwargs =kwargs)
    return reverse_url

def prepare_json(data): # utility to put together json request package
    request_package = {
        "data": json.dumps(data), # json.dumps() here to manually convert the incoming js data to json
                                  # normally JsonResponse abstracts json.dumps() in the view function
        "content_type": "application/json",
    }
    return request_package

class UserSessionHelper:   #Class to instantiate user instance, PLUS create a login session AND build post data
                           # AND binding the setup_session_and_post method to the instance - for future calling
    def __init__(self, client, username, user_factory, post_data=None):
        self.client = client
        self.username = username
        self.user_factory = user_factory
        self.post_data = post_data
        self.user = None
    
    # Class method to create the instance (if not already created) login to the session, build the post data, 
    # build a url with path params (args and kwargs) and query params (offset and batch_size) and send a post 
    # request with json data to the given view
    def setup_session_and_post(self, view_name, body="Test post body", args=None, kwargs=None,
                               offset=None, batch_size=None):
        if not self.user:
            self.user = self.user_factory(self.username)
        self.client.force_login(self.user)
        data = self.post_data(self.user, body)
        url = reverse_django_url(view_name, args, kwargs)
        if offset is not None and batch_size is not None:
            url = f"{url}?offset={offset}&batchSize={batch_size}"
        response = self.client.post(url,
                   **prepare_json(data))
        return response
    
@pytest.mark.parametrize("view_name, field_name", [
    ("toggle_like_status", "liked_by"),
    ("toggle_dislike_status", "disliked_by"),
])
def test_user_can_toggle_reactions(client, db, user_factory, post_data, view_name, field_name):
    # -- Set-up --
    poster_session = UserSessionHelper(client, "poster", user_factory, post_data) 
    response = poster_session.setup_session_and_post("compose", body="Test post body", args=None, kwargs=None)
    
    posts = response.json()
    post_id = posts[0]["id"]

    toggler_session = UserSessionHelper(client, "toggler", user_factory, post_data)

    # -- Act --
    response_toggle = toggler_session.setup_session_and_post(view_name, args=[post_id])

    # -- Assert --
    assert response_toggle.status_code == 200
    post = Post.objects.get(id=post_id)
    assert getattr(post, field_name).count() == 1

@pytest.mark.parametrize("view_name, method, field_name", [
    ("toggle_like_status", "get", "liked_by"),
    ("toggle_dislike_status", "get", "disliked_by"),
    ("toggle_like_status", "put", "liked_by"),
    ("toggle_dislike_status", "put", "disliked_by"),
])
def test_toggle_reaction_disallowed_methods(client, db, user_factory, post_data, view_name, method, field_name):
    # -- Set-up --
    poster_session = UserSessionHelper(client, "poster", user_factory, post_data) 
    response = poster_session.setup_session_and_post("compose", body="Test post body", args=None, kwargs=None)
    
    post_data = response.json() #parse the serialized json reprsentation of the db instance just created
    post_id = post_data[0]["id"] #extract the post id
    post = Post.objects.get(id=post_id) #use extracted post id to pull actual instance from the db for access
                                        # to all model fields for assetions

    toggler = user_factory("toggler")
    client.force_login(toggler)

    # -- Act --
    toggled_response = getattr(client, method)( # client is an object with a method attribute, so you can't 
                                                # just use a variable name for method.  Need to use getattr
                                                # to dynamically populate the attribute with each method
            reverse(view_name, args=[post_id]),
        )
    
    post.refresh_from_db()        # the http request in the previous line just toggled the db, so we need to
                                  # refresh the db here to be sure we get current toggled db field states
    assert getattr(post, field_name).count() == 0
    assert toggled_response.status_code == 405
 
@pytest.mark.parametrize("view_name, field_name", [
    ("toggle_like_status", "liked_by"),
    ("toggle_dislike_status", "disliked_by")
])
def test_cannot_react_to_own_post(client, db, user_factory, post_data, view_name, field_name):
    # -- Set-up --
    user_session = UserSessionHelper(client, "poster", user_factory, post_data) 
    
    response = user_session.setup_session_and_post("compose", body="Test post body", args=None, kwargs=None)
    
    posts = response.json()
    post_id = posts[0]["id"]

    post = Post.objects.get(id=post_id)
    assert getattr(post, field_name).count() == 0

    # -- Act --
    response_reaction = user_session.setup_session_and_post(view_name, args=[post_id])
    
    # -- Assert --
    assert response_reaction.status_code == 400
    assert response_reaction.json()["error"] == "Users cannot react to their own posts."
    post.refresh_from_db()
    assert getattr(post, field_name).count() == 0

@pytest.mark.parametrize("number_of_toggles, new_follows", [
    (1, 1),
    (2, 0)
])
def test_user_can_toggle_follow_status(client, db, user_factory, number_of_toggles, new_follows):
    # -- Set-up --
    user = user_factory("user")
    follower = user_factory("follower")
    client.force_login(follower)
    
    # -- Act --
    for _ in range(number_of_toggles): # pytest loops through all Cartesian products for you, but this inner
                                       # loop is b/c we want to test a series of interactions with the db
        response = client.post(
            reverse_django_url("toggle_follow_status", args=[user.id]),
        ) 
    
    # -- Assert --
    assert response.status_code == 200
    assert follower.following.count() == new_follows
    assert user.followers.count() == new_follows
    assert (user in follower.following.all()) if new_follows else (user not in follower.following.all())

def test_cannot_follow_yourself(client, db, user_factory):
    # -- Set-up --
    user = user_factory("user_username")
    client.force_login(user)

    # -- Act --
    response = client.post(
        reverse_django_url("toggle_follow_status", args=[user.id]),
    ) 

    # -- Assert --
    assert response.status_code == 200
    profile = response.json().get("profile")
    assert profile is not None
    assert user.following.count() == 0
    assert user.followers.count() == 0

@pytest.mark.parametrize("poster, post_body", [
    ("poster", "Test post body"),
    ("", "Test post body"),
    ("poster", "")
])
def test_posting_variants(client, db, user_factory, post_data, poster, post_body):
    if poster and post_body:
        poster_session = UserSessionHelper(client, poster, user_factory, post_data) 
        response = poster_session.setup_session_and_post("compose", body= post_body, args=None, kwargs=None)

        assert response.status_code == 200
        assert Post.objects.count() == 1
        posts = response.json()
        assert posts[0]["body"] == "Test post body"
    
    elif post_body and not poster:
        data = post_data(poster, post_body)
        response = client.post(
            reverse_django_url("compose"),
            **prepare_json(data)
        )
        
        assert response.status_code == 302
        assert "/accounts/login" in response.url
        assert Post.objects.count() == 0
    
    elif poster and not post_body:
        poster_session = UserSessionHelper(client, poster, user_factory, post_data) 
        response = poster_session.setup_session_and_post("compose", body= post_body, args=None, kwargs=None)

        assert response.status_code == 400
        assert Post.objects.count() == 0
        assert response.json()["error"] == "Post body cannot be empty"

@pytest.mark.parametrize("view_name, error_message", [
    ("toggle_like_status", "Post not found"),
    ("toggle_dislike_status", "Post not found"), 
    ("toggle_follow_status", "User not found"),
])
def test_resource_not_found_for_toggling_error(client, db, user_factory, post_data, view_name, error_message):
    user = user_factory("user_username")
    client.force_login(user)

    # -- Act --
    response = client.post(
        reverse_django_url(view_name, args=[999999]),
    ) 

    # -- Assert --
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == error_message

def test_compose_rejects_malformed_json(client, db, user_factory, post_data):
        # -- Set-up --
    user = user_factory("user_username")
    client.force_login(user)

    # -- Act -- 
    response = client.post( 
                reverse_django_url("compose"),
                data = "garbage string",
                content_type="application/json"
            )
  
    # -- Assert --
    assert response.status_code == 400
    bad_post_response = response.json()
    assert bad_post_response["error"] == "Invalid JSON."

@pytest.mark.parametrize("posts_option, post_counter", [
    ("all-posts", 4),
    ("my-posts", 2),
])
def test_allposts_filter(client, db, user_factory, post_data, posts_option, post_counter):
    user1_session = UserSessionHelper(client, "user1", user_factory, post_data) 
    user2_session = UserSessionHelper(client, "user2", user_factory, post_data) 

    for _ in range(2):
        user1_session.setup_session_and_post("compose", body="Test post body", args=None, kwargs=None)

    for _ in range(2):
        user2_session.setup_session_and_post("compose", body="Test post body", args=None, kwargs=None)

    client.force_login(user1_session.user)
    url = reverse("get_posts")    
    filtered_response = client.get(
        url, data={"filter":posts_option, "offset": 0, "batchSize": 5}
    )

    retrieved_posts = filtered_response.json()
    assert filtered_response.status_code == 200
    assert len(retrieved_posts) == post_counter

@pytest.mark.parametrize("view_name, method", [
    ("compose", "post"),
    ("get_follow_usernames", "get"),
    ("get_posts", "get"),
    ("get_profile", "get"),
    ("toggle_follow_status", "post"),
    ("toggle_like_status", "post"),
    ("toggle_dislike_status", "post"),
])
def test_protected_views_redirect_unauthenticated_users(client, db, view_name, method):
    # -- Set-up -- 
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )

    post = Post.objects.create(
        poster = user,
        body = "Test post body"
    )

    if view_name == "toggle_follow_status" or view_name == "get_profile":
        args = [user.id]
    
    elif view_name in ["toggle_like_status","toggle_dislike_status"]:
        post = Post.objects.create(poster=user, body="Test post body")
        args = [post.id]
    
    elif view_name in ["get_posts", "compose"]: 
        args = []

    elif view_name == "get_follow_usernames":
        args = ["following"]

    # -- Act --
    response = getattr(client, method)(
        reverse_django_url(view_name, args=args),
    ) 

    # -- Assert --
    assert response.status_code == 302
    assert "/login" in response.url

weird_pagination_values = [
    (-1, 5),        # Negative offset
    (0, 0),         # Zero batch size
    (99999, 5),      # Very large offset
    (0, 9999),      # Very large batch size
    ("foo", 5),     # Non-numeric offset
    (0, "bar"),     # Non-numeric batch size
    (None, 5),      # None as offset
    (0, None),      # None as batch size
]
@pytest.mark.parametrize("view_name, offset, batch_size", [
    (view_name, offset, batch_size) for view_name in ["get_posts", "get_profile"] for (offset,batch_size) in weird_pagination_values
])
def test_get_views_handle_invalid_pagination(client, db, user_factory, post_data, view_name, offset, batch_size):
    user = user_factory(f"user_{view_name}_{offset}_{batch_size}")
    client.force_login(user)

    if offset is None:
        offset = ""
    if batch_size is None:
        batch_size = ""
    if view_name == "get_profile":
        url = reverse_django_url(view_name, args=[user.id])
        url_with_params = url + "?offset=" + str(offset) + "&batchSize=" + str(batch_size) 

        response = (client.get)(url_with_params)
        assert response.status_code == 400
        invalid_pagination_response = response.json()
        assert invalid_pagination_response["error"] == "Invalid pagination parameters"

    elif view_name == "get_posts":   # need an inner loop in this conditional branch to accoun for 2 filters
        for filter in ["all-posts", "my-posts"]:
            url = reverse_django_url(view_name)
            url_with_params = url + "?filter=" + filter + "&offset=" + str(offset) + "&batchSize=" + str(batch_size) 
            response = (client.get)(url_with_params)
            assert response.status_code == 400
            invalid_pagination_response = response.json()
            assert invalid_pagination_response["error"] == "Invalid pagination parameters"

@pytest.mark.parametrize("view_name, offset, batch_size", [
    (view_name, offset, batch_size) for view_name in ["compose", "toggle_like_status", "toggle_dislike_status"] 
    for (offset,batch_size) in weird_pagination_values
])
def test_post_views_handle_invalid_pagination(client, db, user_factory, post_data, view_name, offset, batch_size):
    # -- Set-up --
    poster_session = UserSessionHelper(client, "poster", user_factory, post_data) 

    user = user_factory(f"poster_{offset}_{batch_size}")
    post = Post.objects.create(poster=user, body="test body")

    # -- Act --
    if offset is None:
        offset = ""
    if batch_size is None:
        batch_size = ""
    if view_name == "compose":
        response = poster_session.setup_session_and_post(
            view_name, body="Test post body", args=None, kwargs=None, offset=offset, batch_size=batch_size
            )

    elif view_name in ["toggle_like_status", "toggle_dislike_status"]:
        response = poster_session.setup_session_and_post(
            view_name, body="Test post body", args=[post.id], kwargs=None, offset=offset, batch_size=batch_size
        )   

    # -- Assert --
    assert response.status_code == 400
    invalid_pagination_response = response.json()
    assert invalid_pagination_response["error"] == "Invalid pagination parameters" 

@pytest.mark.parametrize("view_name, data_structure", [
    ("compose", "list_of_dicts"),
    ("toggle_like_status", "dict_with_list_of_dicts"),
    ("toggle_dislike_status", "dict_with_list_of_dicts"),
    ("get_posts", "list_of_dicts")
])
def test_post_serialization_returns_expected_structure(client, db, user_factory, post_data, view_name, data_structure):
    # -- Set-up -- 
    poster_user = user_factory("poster")
    post = Post.objects.create(poster=poster_user, body="test body")

    user = user_factory("user")
    client.force_login(user)

    if view_name == "compose":
        data = post_data(user, "Test body")
        url = reverse_django_url(view_name)
        url_with_params = f"{url}?offset=0&batchSize=5"
        response = client.post(
            url_with_params,
            **prepare_json(data)
        )

    elif view_name in ["toggle_like_status", "toggle_dislike_status"]:
        url = reverse_django_url(view_name, args = [post.id])
        url_with_params = f"{url}?offset=0&batchSize=5"
        response = client.post(url_with_params)

    elif view_name == "get_posts":
        filter = "all-posts"
        url = reverse_django_url(view_name)
        url_with_params = f"{url}?filter={filter}&offset=0&batchSize=5"
        response = client.get(url_with_params)

    assert response.status_code == 200
    if data_structure == "list_of_dicts":
        list_of_dicts = response.json()
        assert isinstance(list_of_dicts,list)
        assert len(list_of_dicts) >= 1
        assert isinstance(list_of_dicts[0],dict)
        latest_post = Post.objects.latest('id') 
        assert list_of_dicts[0]["id"] == latest_post.id
    if data_structure == "dict_with_list_of_dicts":
        dict_with_list_of_dicts = response.json()
        assert isinstance(dict_with_list_of_dicts,dict)
        list_of_dicts = dict_with_list_of_dicts["posts"]
        assert len(list_of_dicts) >= 1
        assert isinstance(list_of_dicts,list)
        assert list_of_dicts[0]["id"] == post.id
