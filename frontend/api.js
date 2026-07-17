const COLD_START_MESSAGE =
  "Server is waking up (this can take up to 30 seconds on the free tier). Retrying…";

const TOKEN_KEY = "steno_token";
const USER_KEY = "steno_user";

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function getStoredUser() {
  const raw = sessionStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

function setSession(token, user) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchWithColdStartRetry(url, options) {
  try {
    return await fetch(url, options);
  } catch (err) {
    // A network-level failure (not an HTTP error status) usually means the
    // backend is cold-starting on Render's free tier — wait and retry once.
    showToast(COLD_START_MESSAGE, "info");
    await new Promise((resolve) => setTimeout(resolve, 4000));
    return fetch(url, options);
  }
}

async function apiLogin(username, password) {
  const res = await fetchWithColdStartRetry(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Login failed");
  return data;
}

async function apiGetMe() {
  const res = await fetchWithColdStartRetry(`${API_BASE_URL}/api/auth/me`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Session expired");
  return res.json();
}

async function apiGetDictations() {
  const res = await fetchWithColdStartRetry(`${API_BASE_URL}/api/dictations`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load dictations");
  return res.json();
}

async function apiGetDictation(id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/dictations/${id}`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw new Error("Failed to load dictation");
  return res.json();
}

async function apiGetAttempts(id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/dictations/${id}/attempts`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw new Error("Failed to load attempts");
  return res.json();
}

async function apiSubmitAttempt(id, typedText, timeTakenSeconds) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/dictations/${id}/submit`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        typed_text: typedText,
        time_taken_seconds: timeTakenSeconds,
      }),
    }
  );
  if (!res.ok) throw new Error("Failed to submit attempt");
  return res.json();
}

async function apiUploadDictation(formData) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/admin/dictations`,
    {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}

async function apiDeleteDictation(id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/admin/dictations/${id}`,
    { method: "DELETE", headers: authHeaders() }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Delete failed");
  }
}

async function apiListUsers() {
  const res = await fetchWithColdStartRetry(`${API_BASE_URL}/api/admin/users`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}

async function apiCreateUser(body) {
  const res = await fetchWithColdStartRetry(`${API_BASE_URL}/api/admin/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Failed to create user");
  return data;
}

async function apiUpdateUser(id, body) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/admin/users/${id}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body),
    }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Failed to update user");
  return data;
}

async function apiDeleteUser(id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/admin/users/${id}`,
    { method: "DELETE", headers: authHeaders() }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to delete user");
  }
}
