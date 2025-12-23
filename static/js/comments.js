// =========================
// COMMENTS
// =========================
let activePostId = null;

async function openComments(postId) {
  activePostId = postId;
  document.getElementById("comment-modal").classList.remove("hidden");
  loadComments();
}

async function loadComments() {
  if (!activePostId) return;

  const list = document.getElementById("comments-list");
  list.innerHTML = "Loading...";

  const res = await fetch(`/posts/${activePostId}/comments`, {
    credentials: "include",
  });

  if (!res.ok) {
    list.innerHTML = "Failed to load comments";
    return;
  }

  const comments = await res.json();
  if (!comments.length) {
    list.innerHTML = "<p class='muted'>No comments yet</p>";
    return;
  }

  list.innerHTML = comments
    .map(c => `
      <div class="comment">
        <strong>${escapeHTML(c.author)}</strong>
        <div>${escapeHTML(c.text)}</div>
        <small>${new Date(c.created_at).toLocaleString()}</small>
      </div>
    `)
    .join("");
}

async function submitComment() {
  const textarea = document.getElementById("comment-text");
  const text = textarea.value.trim();
  if (!text || !activePostId) return;

  const res = await fetch(`/posts/${activePostId}/comment`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) return;

  textarea.value = "";
  loadComments();
}

function closeComments() {
  activePostId = null;
  document.getElementById("comment-modal").classList.add("hidden");
}

// expose
window.openComments = openComments;
window.submitComment = submitComment;
window.closeComments = closeComments;