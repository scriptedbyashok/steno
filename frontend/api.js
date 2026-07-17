const COLD_START_MESSAGE =
  "Server is waking up (this can take up to 30 seconds on the free tier). Retrying…";

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

async function apiGetDictations() {
  const res = await fetchWithColdStartRetry(`${API_BASE_URL}/api/dictations`);
  if (!res.ok) throw new Error("Failed to load dictations");
  return res.json();
}

async function apiGetDictation(id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/dictations/${id}`
  );
  if (!res.ok) throw new Error("Failed to load dictation");
  return res.json();
}

async function apiGetAttempts(id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/dictations/${id}/attempts`
  );
  if (!res.ok) throw new Error("Failed to load attempts");
  return res.json();
}

async function apiSubmitAttempt(id, typedText, timeTakenSeconds) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/dictations/${id}/submit`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        typed_text: typedText,
        time_taken_seconds: timeTakenSeconds,
      }),
    }
  );
  if (!res.ok) throw new Error("Failed to submit attempt");
  return res.json();
}

async function supabaseLogin(email, password) {
  const res = await fetch(
    `${SUPABASE_URL}/auth/v1/token?grant_type=password`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: SUPABASE_ANON_KEY,
      },
      body: JSON.stringify({ email, password }),
    }
  );
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error_description || data.msg || "Login failed");
  }
  return data.access_token;
}

async function apiUploadDictation(token, formData) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/admin/dictations`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}

async function apiDeleteDictation(token, id) {
  const res = await fetchWithColdStartRetry(
    `${API_BASE_URL}/api/admin/dictations/${id}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Delete failed");
  }
}
