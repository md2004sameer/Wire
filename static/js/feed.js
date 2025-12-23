let skip = 0;
const limit = 10;
let loading = false;
let finished = false;

/* =========================
   Load posts (AUTH REQUIRED)
   ========================= */
async function loadPosts() {
  if (loading || finished) return;
  loading = true;

  const token = localStorage.getItem("access_token");
  if (!token) {
    location.href = "/login";
    return;
  }

  const res = await fetch(`/posts?skip=${skip}&limit=${limit}`, {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  if (!res.ok) {
    console.error("Failed to load posts:", res.status);
    loading = false;
    return;
  }

  const data = await res.json();

  if (data.length === 0) {
    finished = true;
    loading = false;
    return;
  }

  const feed = document.getElementById("feed");

  data.forEach(p => {
    const div = document.createElement("div");
    div.className = "post";
    div.innerHTML = `
      <div class="author">${p.author}</div>
      <div class="post-content">${p.content}</div>
    `;
    feed.appendChild(div);
  });

  skip += limit;
  loading = false;
}

/* =========================
   Create post
   ========================= */
async function createPost() {
  const textarea = document.getElementById("content");
  const content = textarea.value.trim();

  if (!content) return;

  const token = localStorage.getItem("token");
  if (!token) {
    location.href = "/login";
    return;
  }

  const res = await fetch("/posts", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ content })
  });

  if (!res.ok) {
    alert("Failed to post");
    return;
  }

  textarea.value = "";
  skip = 0;
  finished = false;
  document.getElementById("feed").innerHTML = "";
  loadPosts();
}

/* =========================
   Infinite scroll
   ========================= */
window.addEventListener("scroll", () => {
  if (
    window.innerHeight + window.scrollY >=
    document.body.offsetHeight - 100
  ) {
    loadPosts();
  }
});

/* =========================
   Navigation
   ========================= */
function goToProfile() {
  location.href = "/profile";
}

/* =========================
   Initial load
   ========================= */
loadPosts();