// =========================
// FEED STATE
// =========================
let skip = 0;
const limit = 10;
let loading = false;
let finished = false;

let newestTimestamp = null;
let pendingNewPosts = [];
const renderedPostIds = new Set();

// =========================
// WEBSOCKET + POLLING STATE
// =========================
let ws = null;
let wsConnected = false;
let pollTimer = null;

// =========================
// DOM REFERENCES
// =========================
let feedEl;
let bannerEl;

// =========================
// WEBSOCKET (REALTIME)
// =========================
function startWebSocket() {
  if (wsConnected) return;

  const protocol = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${protocol}://${location.host}/ws/feed`);

  ws.onopen = () => {
    console.log("🟢 WS connected");
    wsConnected = true;
    stopPolling();
  };

  ws.onmessage = (e) => {
    let msg;
    try {
      msg = JSON.parse(e.data);
    } catch {
      return;
    }

    if (msg.type !== "new_post") return;

    const p = msg.post;
    if (!p || !p.id) return;
    if (renderedPostIds.has(p.id)) return;

    renderPost(p, true);
    renderedPostIds.add(p.id);
    newestTimestamp = p.created_at;
  };

  ws.onclose = () => {
    console.log("🔴 WS disconnected → fallback to polling");
    wsConnected = false;
    ws = null;
    startPolling();
    retryWebSocket();
  };

  ws.onerror = () => ws.close();
}

function retryWebSocket() {
  setTimeout(() => {
    if (!wsConnected) startWebSocket();
  }, 3000);
}

// =========================
// POLLING (FALLBACK)
// =========================
function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(pollNewPosts, 10000);
}

function stopPolling() {
  if (!pollTimer) return;
  clearInterval(pollTimer);
  pollTimer = null;
}

// =========================
// LOAD POSTS (INITIAL + SCROLL)
// =========================
async function loadPosts() {
  if (loading || finished) return;
  loading = true;

  const res = await fetch(`/posts?skip=${skip}&limit=${limit}`, {
    credentials: "include"
  });

  if (res.status === 401) {
    location.replace("/login");
    return;
  }

  if (!res.ok) {
    loading = false;
    return;
  }

  const posts = await res.json();
  if (!Array.isArray(posts) || posts.length === 0) {
    finished = true;
    loading = false;
    return;
  }

  for (const p of posts) {
    if (!p || renderedPostIds.has(p.id)) continue;

    renderPost(p, false);
    renderedPostIds.add(p.id);

    if (!newestTimestamp || p.created_at > newestTimestamp) {
      newestTimestamp = p.created_at;
    }
  }

  skip += limit;
  loading = false;
}

// =========================
// POLL NEW POSTS (ONLY WHEN WS OFF)
// =========================
async function pollNewPosts() {
  if (wsConnected || !newestTimestamp) return;

  const res = await fetch(
    `/posts?after=${encodeURIComponent(newestTimestamp)}&limit=5`,
    { credentials: "include" }
  );

  if (!res.ok) return;

  const posts = await res.json();
  const fresh = posts.filter(
    p => p && p.id && !renderedPostIds.has(p.id)
  );

  if (!fresh.length) return;

  pendingNewPosts = fresh;
  bannerEl?.classList.remove("hidden");
}

function loadNewPosts() {
  pendingNewPosts
    .slice()
    .reverse()
    .forEach(p => {
      renderPost(p, true);
      renderedPostIds.add(p.id);
      newestTimestamp = p.created_at;
    });

  pendingNewPosts = [];
  bannerEl?.classList.add("hidden");
}

// =========================
// RENDER POST
// =========================
function renderPost(p, prepend) {
  const div = document.createElement("div");
  div.className = "post";
  div.dataset.postId = p.id;

  div.innerHTML = `
    <div class="post-header">
      <span>${escapeHTML(p.author)}</span>
      <span class="time">${new Date(p.created_at).toLocaleString()}</span>
    </div>

    <div class="post-content">${escapeHTML(p.content)}</div>

    <div class="post-actions">
      <button class="like-btn">
        ❤️ <span>${p.like_count}</span>
      </button>

      <button class="comment-btn">
        💬 <span>${p.comment_count}</span>
      </button>

      <button disabled>🔁 ${p.share_count}</button>
    </div>
  `;

  // like
  div.querySelector(".like-btn").addEventListener("click", (e) => {
    toggleLike(p.id, e.currentTarget);
  });

  // comments
  div.querySelector(".comment-btn").addEventListener("click", () => {
    window.openComments?.(p.id);
  });

  prepend ? feedEl.prepend(div) : feedEl.appendChild(div);
}

// =========================
// CREATE POST (OWN POST)
// =========================
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

  if (!res.ok) return;

  let post;
  try {
    post = await res.json();
  } catch {
    textarea.value = "";
    return;
  }

  textarea.value = "";

  if (post && post.id && !renderedPostIds.has(post.id)) {
    renderPost(post, true);
    renderedPostIds.add(post.id);
    newestTimestamp = post.created_at;
  }
}

// =========================
// LIKE / UNLIKE
// =========================
async function toggleLike(postId, btn) {
  const res = await fetch(`/posts/${postId}/like`, {
    method: "POST",
    credentials: "include"
  });

  if (!res.ok) return;

  const data = await res.json();
  const span = btn.querySelector("span");
  let count = Number(span.textContent);

  span.textContent =
    data.status === "liked" ? count + 1 : Math.max(0, count - 1);
}

// =========================
// HELPERS
// =========================
function escapeHTML(str) {
  const div = document.createElement("div");
  div.innerText = str;
  return div.innerHTML;
}

// =========================
// SCROLL
// =========================
window.addEventListener("scroll", () => {
  if (loading || finished) return;
  if (innerHeight + scrollY >= document.body.offsetHeight - 120) {
    loadPosts();
  }
});

// =========================
// BOOT
// =========================
document.addEventListener("DOMContentLoaded", () => {
  feedEl = document.getElementById("feed");
  bannerEl = document.getElementById("new-posts-banner");

  window.createPost = createPost;
  window.loadNewPosts = loadNewPosts;

  loadPosts();      // REST = source of truth
  startPolling();   // safety
  startWebSocket(); // realtime
});