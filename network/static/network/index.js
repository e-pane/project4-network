document.addEventListener('DOMContentLoaded', function() {

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        // Does this cookie string begin with the name we want?
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const spinner = document.createElement('div');
  spinner.id = "spinner";
  spinner.style.display = 'none';
  spinner.innerHTML = "Loading...";
  document.body.appendChild(spinner);

  let currentFilter = 'all-posts';

  const postManager = (function() {
    let offset = 0;
    let batchSize = 10;

    function resetOffset(){
      offset = 0;
    }

    function loadPosts(filter){
      spinner.style.display = 'block';
      fetch(`posts-data?filter=${filter}&offset=${offset}&batchSize=${batchSize}`)
        .then(response => {
          if(!response.ok){
            throw new Error("Posts could not be successfully retrieved")
          }
          return response.json()
        })
        .then(posts => {
          renderPosts(posts, true);
          offset += batchSize;
        })
        .catch(error => console.error(error))
        .finally(() => {
          spinner.style.display = 'none';
        });
    }

    if(isAuthenticated){
      offset = 0;
      spinner.style.display = 'block';
      loadPosts('all-posts');
    }

    function handleTogglingRequest(toggleArg){        
      const refId = toggleArg.id;
      let errorVar;
      let urlPath;
      if(toggleArg.type === 'user'){
        errorVar = "follow";
        urlPath = "follow-status/"
      }
      else{
        urlPath = toggleArg.opinion === "like" ? "like-update/" : "dislike-update/";
        errorVar = toggleArg.opinion === "like" ? "like" : "dislike";
      }
      
      spinner.style.display = 'block';
      fetch(`${urlPath}${refId}?offset=${offset}&batchSize=${batchSize}`,{
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        }
      })
      .then(response => {
        if (response.ok){
          return response.json();
        }
        else{
          throw new Error(`Failed to toggle ${errorVar} status`)
        }
      })
      
      .then(updatedResponse => {
        if (toggleArg.type === 'user') {
          const updatedProfile = updatedResponse.profile;
          renderProfile(updatedProfile);
        } else {
          const updatedPosts = updatedResponse.posts;
          renderPosts(updatedPosts, false);
        }
      })
      .catch(error => console.error(error))
      .finally(() => {
        spinner.style.display = 'none';
      });
    }

    function handleNewPost(event){
      event.preventDefault();

      const body = document.getElementById('post-body').value;
      const poster = document.getElementById('poster-username').value;
      
      const newPostData = {
        body:body,
        poster:poster,
      }

      spinner.style.display = 'block';
      fetch(`/new-post?offset=${offset}&batchSize=${batchSize}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(newPostData),
      })

      .then(response => {
        if(!response.ok){
          throw new Error("Failed to submit new post")
        }
        return response.json();
      })
      .then(data => {
        renderPosts(data, false);
        document.getElementById('post-body').value = "";
      })
      .catch(error => console.error("Error submitting post", error))
      .finally(() => {
        spinner.style.display = 'none';
      })
    }

    return{
      resetOffset,
      loadPosts,
      handleNewPost,
      handleTogglingRequest,
    };
  })();

  function setupEventListeners() {

    const loginForm = document.getElementById('login-form');
    if(loginForm){
      loginForm.addEventListener('submit', handleLoginSubmit);
    }

    const composeForm = document.getElementById('compose-form');
    if(composeForm){
      composeForm.addEventListener('submit', postManager.handleNewPost);
    }

    const allPostsBtn = document.getElementById('all-posts');
    if (allPostsBtn) {
      allPostsBtn.addEventListener('click', event => handlePostRequest(event, 'all-posts'));
    }
    
    const myPostsBtn = document.getElementById('my-posts');
    if (myPostsBtn) {
      myPostsBtn.addEventListener('click', event => handlePostRequest(event, 'my-posts'));
    }

    const followingBtn = document.getElementById('following');
    if (followingBtn) {
      followingBtn.addEventListener('click', event => handleFollowDisplay(event, 'following'));
    }

    const followersBtn = document.getElementById('followers');
    if (followersBtn) {
      followersBtn.addEventListener('click', event => handleFollowDisplay(event, 'followers'));
    }

    const postsView = document.getElementById('posts-view');
    if(postsView){   
      postsView.addEventListener('click', event => { 
        const userLink = event.target.closest('.user-link');
        if(userLink){
          const userId = userLink.dataset.userId;
          handleProfileRequest(event, userId);
        }

        const likeBtn = event.target.closest('.like-button')
        if(likeBtn){
          const postId = likeBtn.dataset.postId;
          handleLikeUpdate(event, postId);
        }

        const dislikeBtn = event.target.closest('.dislike-button')
        if(dislikeBtn){
          const postId = dislikeBtn.dataset.postId;
          handleDislikeUpdate(event,postId);
        }
      });

      let timeoutId = null;
      postsView.addEventListener('scroll', () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(()=> {
          if((postsView.scrollHeight - (postsView.clientHeight + postsView.scrollTop)) < 100){
            postManager.loadPosts(currentFilter);
          }
          }, 200);
      })
    }

    const profileView = document.getElementById('profile-view');
    if(profileView){
      profileView.addEventListener('click', event => {
        const followBtn = event.target.closest('#follow-btn, #unfollow-btn');
        if(followBtn){
          const userId = followBtn.dataset.userId;
          handleFollowRequest(event, userId);
        }
      });
    }

    const usernamesView = document.getElementById('usernames-view');
    if(usernamesView){
      usernamesView.addEventListener('click', event => {
        const username = event.target.closest('.following-user-link');
        if(username){
          const userId = username.dataset.userId;
          handleProfileRequest(event, userId);
          return;
        }
      
        const unfollowButton = event.target.closest('.unfollow-button');
        if(unfollowButton){
          const userId = unfollowButton.dataset.userId;
          handleFollowRequest(event, userId);
        }
      })
    }
  }
  
  setupEventListeners();

  function handleFollowRequest(event, userId){
    event.preventDefault();
    const toggleArg = {type: "user", id: userId}
    postManager.handleTogglingRequest(toggleArg);
  }
    
  function handleFollowDisplay(event, option){
    event.preventDefault();
    spinner.style.display = 'block';
    fetch(`follow-usernames/${option}`,{
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      }
    })
    .then(response => {
      if(!response.ok){
        throw new Error("Data could not be retrieved");
      }
      return response.json();
    })
    .then(data => {
      renderUsernames(data.usernames, data.ids, option);
    })
    .catch(error => {
      console.error("Could not retrieve data", error);
    })
    .finally(() => {
      spinner.style.display = 'none';
    });
  }

  function handleLikeUpdate(event,postId){
    event.preventDefault();
    const toggleArg = {type: "post", id: postId, opinion:"like"}
    postManager.handleTogglingRequest(toggleArg);
  }

  function handleDislikeUpdate(event,postId){
    event.preventDefault();
    const toggleArg = {type: "post", id: postId, opinion:"dislike"}
    postManager.handleTogglingRequest(toggleArg);
  }

  function handleLoginSubmit(event) {
    // Prevent default link behavior
    event.preventDefault();

    const username = document.querySelector('[name="username"]').value;
    const password = document.querySelector('[name="password"]').value;

    const loginData = {
      username: username,
      password: password,
    }

    spinner.style.display = 'block';
    fetch('/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(loginData),
    })

    .then(response => {
      if(!response.ok){
        throw new Error("Login unsuccessful")
      }
      return response.json()
    })
    .then(data => {
      if (data.redirect) {
        // If a redirect URL is returned, go there
        window.location.href = data.redirect;

      } else if (data.message) {
        alert(data.message);
      } else {
        console.error("Unexpected response", data);
      }
    })
    .catch(error => {
      console.error("Login error:", error);
      alert("Login failed. Please try again.");
    })
    .finally(() =>{
      spinner.style.display = 'none';
    })
  }

  function handlePostRequest(event, postRequest){
    event.preventDefault();
    currentFilter = postRequest;
    postManager.resetOffset();
    postManager.loadPosts(currentFilter);
  }

  function handleProfileRequest(event, userId){
    event.preventDefault();
    console.log("Fetching profile for userId:", userId);

    spinner.style.display = 'block';
    fetch(`profile-data/${userId}`)
    .then(response => {
      if(!response.ok){
        throw new Error("Profile could not be retrieved")
      }
      return response.json()
    })
    .then(profile => {
      const profilePosts = profile.posts;  
      renderProfile(profile);
      renderPosts(profilePosts, false);
    })
    .catch(error => console.error("Error fetching profile data:", error))
    .finally(() => {
      spinner.style.display = 'none';
    })
  }

  function renderProfile(profile){
    const usernamesView = document.getElementById('usernames-view');
    const postsView = document.getElementById('posts-view');
    const newPostsView = document.getElementById('new-post-view');
    const profileView = document.getElementById('profile-view');

    if(usernamesView){
      usernamesView.style.display = 'none';
    }
    postsView.style.display = 'block';
    newPostsView.style.display = 'block';  // Show the new-posts-view
    profileView.style.display = 'block';
    
    profileView.innerHTML = `
      <div class="profile">  
        <div>
              <strong>${profile.username}</strong> 
        </div>        
        <div>${profile.follower_count} followers - ${profile.following_count} following</div>
      </div>
    `;

    if(profile.user_id !== profile.viewer_id){
      const followUnfollowBtn = document.createElement('button');

      if(profile.follower_ids.includes(profile.viewer_id)){
        followUnfollowBtn.innerHTML = 'Unfollow';
        followUnfollowBtn.id = 'unfollow-btn'; 
        followUnfollowBtn.dataset.userId = profile.user_id;
      }
      else{
        followUnfollowBtn.innerHTML = 'Follow';
        followUnfollowBtn.id ='follow-btn'; 
        followUnfollowBtn.dataset.userId = profile.user_id;
      }
      profileView.appendChild(followUnfollowBtn);
    }
  }

  function renderPosts(posts, append) {
    const usernamesView = document.getElementById('usernames-view')
    const postsView = document.getElementById('posts-view');
    const newPostsView = document.getElementById('new-post-view');
    const profileView = document.getElementById('profile-view');

    if(usernamesView){
      usernamesView.style.display = 'none';
    }
    postsView.style.display = 'block';
    if(!append){
      postsView.innerHTML = '';
    }   

    newPostsView.style.display = 'block';  // Show the new-posts-view
    profileView.style.display = 'block';

    posts.forEach(post => {
      // Dynamically create HTML for each post
      const postElement = document.createElement('div');
      postElement.classList.add('post'); // Add a class for styling

      postElement.innerHTML = `
        <div>
          <a href ="#" class="user-link" data-user-id="${post.user_id}">
            <strong>${post.poster}</strong> - ${post.timestamp}
          </a>
        </div>        
        <div>${post.body}</div>
        <div style="display:inline-block; cursor: pointer"
             class="like-button"
             data-post-id="${post.id}">👍</div>
        <div style="display:inline-block; cursor: pointer"
             class="dislike-button"
             data-post-id="${post.id}">👎</div>
        <div style="display:inline-block">Likes: ${post.like_count}</div>
        <div style="display:inline-block">Dislikes: ${post.dislike_count}</div>
        <br></br>
      `;

      postsView.appendChild(postElement); // Append the new post to the posts view
    });
  }

  function renderUsernames(usernames, ids, option){
    const usernamesView = document.getElementById('usernames-view');
    const postsView = document.getElementById('posts-view');
    const profileView = document.getElementById('profile-view');

    postsView.style.display = 'none';
    profileView.style.display = 'none';
    usernamesView.style.display = 'block';
    usernamesView.innerHTML = ''

    const h3 = document.createElement('h3');
    h3.innerHTML = option === 'following' ? 'You are following:' : 'You are followed by:'

    const ul = document.createElement('ul');
    usernames.forEach((username, index) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <a href ="#" class="following-user-link" data-user-id = "${ids[index]}">
          <strong>${username}</strong> 
        </a>
      `

      const unfollowBtn = document.createElement('button');
      unfollowBtn.innerHTML = "Unfollow";
      unfollowBtn.style.marginLeft = "10px";
      unfollowBtn.classList.add('unfollow-button');
      unfollowBtn.dataset.userId = ids[index];

      if(option === "following"){
        li.appendChild(unfollowBtn);
      }
      ul.appendChild(li);
    })

    usernamesView.appendChild(h3);
    usernamesView.appendChild(ul);
  }

})
