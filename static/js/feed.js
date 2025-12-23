let skip = 0;
const limit = 10;
let loading = false;
let finished = false;
let newestTimestamp = null;
let pendingNewPosts = [];

/* =========================
   Load initial feed
   ========================= */
async function loadPosts() {
  if (loading || finished) return;
  loading = true;

  const res = await fetch(`/posts?skip=${skip}&limit=${limit}`, {
    credentials: "include"
  });

  if (res.status === 401) {
    location.href = "/login";
    return;
  }

  const data = await res.json();

  if (data.length === 0) {
    finished = true;
    loading = false;
    return;
  }

  const feed = document.getElementById("feed");

  data.forEach(p => renderPost(p, false));

  if (!newestTimestamp && data.length > 0) {
    newestTimestamp = data[0].created_at;
  }

  skip += limit;
  loading = false;
}

/* =========================
   Poll for new posts
   ========================= */
async function pollNewPosts() {
  if (!newestTimestamp) return;

  const res = await fetch(`/posts?skip=0&limit=5`, {
    credentials: "include"
  });

  if (!res.ok) return;

  const data = await res.json();

  const fresh = data.filter(
    p => new Date(p.created_at) > new Date(newestTimestamp)
  );

  if (fresh.length === 0) return;

  pendingNewPosts = fresh;
  document.getElementById("new-posts-banner").classList.remove("hidden");
}

/* =========================
   Load new posts on click
   ========================= */
function loadNewPosts() {
  const feed = document.getElementById("feed");

  pendingNewPosts.reverse().forEach(p => renderPost(p, true));

  newestTimestamp = pendingNewPosts[0].created_at;
  pendingNewPosts = [];

  document.getElementById("new-posts-banner").classList.add("hidden");
}

/* =========================
   Render post
   ========================= */
function renderPost(p, prepend) {
  const div = document.createElement("div");
  div.className = "post";
  div.innerHTML = `
    <div class="author">${p.author}</div>
    <div class="post-content">${p.content}</div>
  `;

  const feed = document.getElementById("feed");
  prepend ? feed.prepend(div) : feed.appendChild(div);
}

/* =========================
   Create post
   ========================= */
async function createPost() {
  const textarea = document.getElementById("content");
  const content = textarea.value.trim();
  if (!content) return;

  const res = await fetch("/posts", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content })
  });

  if (res.status === 401) {
    location.href = "/login";
    return;
  }

  textarea.value = "";
}

/* =========================
   Infinite scroll
   ========================= */
window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
    loadPosts();
  }
});

/* =========================
   Boot
   ========================= */
loadPosts();
setInterval(pollNewPosts, 10000);