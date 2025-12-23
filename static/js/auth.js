// =========================
// AUTH
// =========================
async function loadCurrentUser() {
  const res = await fetch("/auth/me", { credentials: "include" });

  if (!res.ok) {
    location.replace("/login");
    return;
  }

  const user = await res.json();
  const avatar = document.getElementById("avatar-letter");
  if (avatar) {
    avatar.innerText = user.username[0].toUpperCase();
  }
}

// expose globally (used on load)
window.loadCurrentUser = loadCurrentUser;