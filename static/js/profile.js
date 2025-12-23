// =========================
// PROFILE STATE
// =========================
let profile = null;

// =========================
// DOM REFERENCES
// =========================
let avatarEl;
let usernameEl;
let bioTextEl;

let bioInputEl;
let websiteInputEl;
let locationInputEl;
let privateCheckboxEl;

let editBtnEl;
let saveBtnEl;
let logoutBtnEl;

let followersCountEl;
let followingCountEl;

// =========================
// AUTH GUARD
// =========================
async function guardAuth() {
  const res = await fetch("/auth/me", { credentials: "include" });
  if (res.status === 401) {
    location.replace("/login");
    return false;
  }
  return true;
}

// =========================
// LOAD PROFILE
// =========================
async function loadProfile() {
  const res = await fetch("/profile/me", { credentials: "include" });
  if (!res.ok) return;

  profile = await res.json();

  usernameEl.textContent = profile.username;
  bioTextEl.textContent = profile.bio || "No bio yet";

  bioInputEl.value = profile.bio || "";
  websiteInputEl.value = profile.website || "";
  locationInputEl.value = profile.location || "";
  privateCheckboxEl.checked = !!profile.is_private;

  avatarEl.textContent =
    profile.username?.[0]?.toUpperCase() ?? "U";
}

// =========================
// LOAD FOLLOW COUNTS
// =========================
async function loadCounts() {
  try {
    const [followersRes, followingRes] = await Promise.all([
      fetch("/friends/followers", { credentials: "include" }),
      fetch("/friends/following", { credentials: "include" })
    ]);

    if (followersRes.ok) {
      const f = await followersRes.json();
      followersCountEl.textContent = f.count ?? 0;
    }

    if (followingRes.ok) {
      const f = await followingRes.json();
      followingCountEl.textContent = f.count ?? 0;
    }
  } catch (err) {
    console.error("Count load failed", err);
  }
}

// =========================
// EDIT MODE
// =========================
function enableEdit() {
  bioInputEl.readOnly = false;
  websiteInputEl.readOnly = false;
  locationInputEl.readOnly = false;
  privateCheckboxEl.disabled = false;

  editBtnEl.classList.add("hidden");
  saveBtnEl.classList.remove("hidden");
}

// =========================
// SAVE PROFILE
// =========================
async function saveProfile() {
  const payload = {
    bio: bioInputEl.value.trim(),
    website: websiteInputEl.value.trim(),
    location: locationInputEl.value.trim(),
    is_private: privateCheckboxEl.checked
  };

  const res = await fetch("/profile/me", {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) return;

  // lock fields again
  bioInputEl.readOnly = true;
  websiteInputEl.readOnly = true;
  locationInputEl.readOnly = true;
  privateCheckboxEl.disabled = true;

  editBtnEl.classList.remove("hidden");
  saveBtnEl.classList.add("hidden");

  loadProfile();
}

// =========================
// NAVIGATION
// =========================
function goToFriends(type) {
  location.href = `/friends-list?type=${type}`;
}

// =========================
// LOGOUT
// =========================
async function logout() {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "include"
    });
  } finally {
    location.replace("/login");
  }
}

// =========================
// BOOT
// =========================
document.addEventListener("DOMContentLoaded", async () => {
  const ok = await guardAuth();
  if (!ok) return;

  // DOM bindings
  avatarEl = document.getElementById("avatar");
  usernameEl = document.getElementById("username");
  bioTextEl = document.getElementById("bioText");

  bioInputEl = document.getElementById("bioInput");
  websiteInputEl = document.getElementById("website");
  locationInputEl = document.getElementById("location");
  privateCheckboxEl = document.getElementById("is_private");

  editBtnEl = document.getElementById("editBtn");
  saveBtnEl = document.getElementById("saveBtn");
  logoutBtnEl = document.getElementById("logoutBtn");

  followersCountEl = document.getElementById("followersCount");
  followingCountEl = document.getElementById("followingCount");

  // Events
  editBtnEl.addEventListener("click", enableEdit);
  saveBtnEl.addEventListener("click", saveProfile);
  logoutBtnEl.addEventListener("click", logout);

  document
    .querySelector("[data-followers]")
    ?.addEventListener("click", () => goToFriends("followers"));

  document
    .querySelector("[data-following]")
    ?.addEventListener("click", () => goToFriends("following"));

  // Initial load
  loadProfile();
  loadCounts();
});