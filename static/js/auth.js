// =========================
// AUTH (GLOBAL)
// =========================
async function loadCurrentUser() {
  try {
    const res = await fetch("/auth/me", {
      credentials: "include",
    });

    if (res.status === 401) {
      location.replace("/login");
      return;
    }

    if (!res.ok) return;

    const user = await res.json();

    // ----- Avatar letter -----
    const avatar = document.getElementById("avatar-letter");
    if (avatar && user?.username) {
      avatar.textContent = user.username[0].toUpperCase();
    }

    // ----- Cache username (read-only usage) -----
    window.currentUsername = user.username;

  } catch (err) {
    console.error("Auth error:", err);
  }
}

// =========================
// NAVIGATION
// =========================
function goToProfile() {
  location.href = "/profile";
}

function goToNotifications() {
  location.href = "/notifications";
}

function goToUsers() {
  location.href = "/users";
}

// =========================
// LOGOUT
// =========================
async function logout() {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // ignore
  } finally {
    location.replace("/login");
  }
}

// =========================
// EVENT BINDINGS (SAFE)
// =========================
document.addEventListener("DOMContentLoaded", () => {
  loadCurrentUser();

  const avatar = document.getElementById("avatar-letter");
  if (avatar) {
    avatar.addEventListener("click", goToProfile);
  }

  const notifBtn = document.getElementById("notif-btn");
  if (notifBtn) {
    notifBtn.addEventListener("click", goToNotifications);
  }

  const usersBtn = document.getElementById("friends-btn");
  if (usersBtn) {
    usersBtn.addEventListener("click", goToUsers);
  }
});

// =========================
// EXPOSE ONLY WHAT HTML NEEDS
// =========================
window.logout = logout;