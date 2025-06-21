from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

import json

from .models import User, Post

batch_size = 10

def build_profile_dict(request,user_id):
    target_user = User.objects.get(id=user_id)
    serialized_user = target_user.serialize()
    follower_ids = serialized_user["follower_ids"]
    following_ids = serialized_user["following_ids"]
    follower_usernames = serialized_user["follower_usernames"]
    following_usernames = serialized_user["following_usernames"]
    offset = int(request.GET.get('offset', 0))
    batch_size = int(request.GET.get('batchSize',10))
    posts = Post.objects.filter(poster = target_user).order_by('-timestamp')[offset:offset+batch_size]
    serialized_posts = [post.serialize() for post in posts]
    profile = {"user_id": target_user.id,
                "username": target_user.username,
                "follower_count": target_user.followers.count(),
                "following_count": target_user.following.count(),
                "posts": serialized_posts,
                "viewer_id": request.user.id,
                "follower_ids": follower_ids,
                "following_ids": following_ids,
                "follower_usernames": follower_usernames,
                "following_usernames": following_usernames,
    }
    return profile

def toggle_post_reaction(request,post_id,reaction):
    if request.method == 'POST':
        try:
            target_post = Post.objects.get(id=post_id)
            if reaction == "like":
                field_to_toggle = target_post.liked_by
            elif reaction == "dislike":
                field_to_toggle = target_post.disliked_by

            field_to_toggle.add(request.user)
            user_id = request.user.id

            offset = int(request.GET.get('offset', 0))
            batch_size = int(request.GET.get('batchSize',10))
            posts = Post.objects.all().order_by('-timestamp')[offset:offset+batch_size]
            serialized_posts = [post.serialize() for post in posts]
            profile = build_profile_dict(request, user_id)

            return JsonResponse({"profile": profile, "posts":serialized_posts},status=200)
        
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
    else:
        return HttpResponse("Method Not Allowed", status=405)

@login_required
def compose(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    poster = data.get("poster", "")
    post_body = data.get("body", "")

    if not post_body.strip():
        return JsonResponse({"error": "Post body cannot be empty"}, status=400)

    try:
        # Get the User instance for the poster
        poster_user = User.objects.get(username=poster)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    post = Post(poster=poster_user, 
                body=post_body)
    post.save()

    offset = int(request.GET.get('offset', 0))
    batch_size = int(request.GET.get('batchSize',10))
    posts = Post.objects.all().order_by('-timestamp')[offset:offset+batch_size]
    serialized_posts = [post.serialize() for post in posts]
    return JsonResponse(serialized_posts, safe=False)

@login_required
def get_follow_usernames(request,option):
    user_id = request.user.id
    profile = build_profile_dict(request,user_id)

    if option == 'following':
        usernames = profile["following_usernames"]
        ids = profile["following_ids"]
    else:
        usernames = profile["follower_usernames"]
        ids = profile["follower_ids"]

    return JsonResponse({"usernames": usernames,
                         "ids": ids,
                         "option": option
    })

@login_required
def get_posts(request):
    
    if request.GET.get('filter') == 'all-posts':
        offset = int(request.GET.get('offset', 0))
        batch_size = int(request.GET.get('batchSize',10))
        posts = Post.objects.all().order_by('-timestamp')[offset:offset+batch_size]
        serialized_posts = [post.serialize() for post in posts]
        return JsonResponse(serialized_posts, safe=False)
    
    elif request.GET.get('filter') == 'my-posts':
        offset = int(request.GET.get('offset', 0))
        batch_size = int(request.GET.get('batchSize',10))
        posts = Post.objects.filter(poster = request.user).order_by('-timestamp')[offset:offset+batch_size]
        serialized_posts = [post.serialize() for post in posts]
        return JsonResponse(serialized_posts, safe=False)
        
    else:
        return JsonResponse({"error": "Invalid filter parameter"}, status=400)
    
@login_required
def get_profile(request,user_id):
    try:
        return JsonResponse(build_profile_dict(request, user_id))
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    
    return render(request, "network/index.html")
    
def login_view(request):
    if request.method == "POST":
        try:

            print("Request body:", request.body)

            # Attempt to sign user in
            data = json.loads(request.body)
            username = data["username"]
            password = data["password"]
            user = authenticate(request, username=username, password=password)

            # Check if authentication successful
            if user is not None:
                login(request, user)
                return JsonResponse({"redirect": "/"})
            else:
                return JsonResponse({"message": "Invalid username or password."}, status=400
                )
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON."}, status=400)
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

def toggle_follow_status(request, user_id):
    if request.method != 'POST':
        return HttpResponse("Method Not Allowed", status=405)
    try:
        target_user = User.objects.get(id=user_id)
        if request.user.id != target_user.id:
            if not request.user.following.filter(id=target_user.id).exists():
                request.user.following.add(target_user)
            else:
                request.user.following.remove(target_user)
                
        return JsonResponse({"profile": build_profile_dict(request, user_id)},status=200)
    
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

@login_required   
def toggle_like_status(request, post_id):
    if request.method == 'POST':
        try:
            return toggle_post_reaction(request, post_id, "like")
        
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
    else:
        return HttpResponse("Method Not Allowed", status=405)

@login_required   
def toggle_dislike_status(request, post_id):
    if request.method == 'POST':
        try:
            return toggle_post_reaction(request, post_id, "dislike")
        
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found"}, status=404)
    else:
        return HttpResponse("Method Not Allowed", status=405)


    