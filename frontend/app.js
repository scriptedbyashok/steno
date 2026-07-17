function showToast(message, type = "info") {
  const container =
    document.getElementById("toast-container") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.classList.add("toast-visible"), 10);
  setTimeout(() => {
    toast.classList.remove("toast-visible");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toast-container";
  document.body.appendChild(container);
  return container;
}

function setLoading(el, isLoading) {
  el.classList.toggle("loading", isLoading);
}

function spinnerHtml(label = "Loading…") {
  return `<div class="spinner-row"><span class="spinner"></span> ${label}</div>`;
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/**
 * Gate a page behind login (and optionally the admin role). Redirects and
 * returns null if the check fails; otherwise returns the current user.
 * Every protected page should `await requireAuth()` before doing anything else.
 */
async function requireAuth({ adminOnly = false } = {}) {
  const token = getToken();
  if (!token) {
    window.location.href = "login.html";
    return null;
  }
  try {
    const user = await apiGetMe();
    setSession(token, user);
    if (adminOnly && user.role !== "admin") {
      window.location.href = "index.html";
      return null;
    }
    return user;
  } catch (err) {
    clearSession();
    window.location.href = "login.html";
    return null;
  }
}

function renderNavbar(user, activePage) {
  const root = document.getElementById("navbar-root");
  if (!root) return;

  const adminLinks =
    user.role === "admin"
      ? `<a href="admin.html" class="${activePage === "admin" ? "active" : ""}">Users</a>
         <a href="config.html" class="${activePage === "config" ? "active" : ""}">Upload</a>`
      : "";

  root.innerHTML = `
    <div class="navbar-left">
      <a href="index.html" class="wordmark">Steno</a>
      <nav class="navbar-links">
        <a href="index.html" class="${activePage === "home" ? "active" : ""}">Home</a>
        ${adminLinks}
      </nav>
    </div>
    <div class="navbar-user">
      <span class="navbar-username" title="Click to edit your display name">${user.display_name}</span>
      <span class="role-badge role-${user.role}">${user.role}</span>
      <button id="navbar-logout" class="secondary">Log Out</button>
    </div>
  `;
  document.getElementById("navbar-logout").addEventListener("click", () => {
    clearSession();
    window.location.href = "login.html";
  });

  const usernameEl = root.querySelector(".navbar-username");
  usernameEl.addEventListener("click", async () => {
    const currentName = usernameEl.textContent;
    const newName = prompt("Update your display name:", currentName);
    if (newName === null) return;
    const trimmed = newName.trim();
    if (!trimmed || trimmed === currentName) return;
    try {
      const updatedUser = await apiUpdateMyName(trimmed);
      setSession(getToken(), updatedUser);
      usernameEl.textContent = updatedUser.display_name;
      showToast("Name updated", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}
