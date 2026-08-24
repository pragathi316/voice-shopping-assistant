const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  processVoice: (text, userId) =>
    request("/api/voice/process", {
      method: "POST",
      body: JSON.stringify({ text, user_id: userId }),
    }),
  getList: (userId) => request(`/api/shopping/list?user_id=${encodeURIComponent(userId)}`),
  addItem: (userId, product, quantity) =>
    request("/api/shopping/add", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, product, quantity }),
    }),
  removeItem: (userId, product) =>
    request("/api/shopping/remove", {
      method: "DELETE",
      body: JSON.stringify({ user_id: userId, product }),
    }),
  updateItem: (userId, product, quantity) =>
    request("/api/shopping/update", {
      method: "PUT",
      body: JSON.stringify({ user_id: userId, product, quantity }),
    }),
  getRecommendations: (userId) =>
    request(`/api/recommendations?user_id=${encodeURIComponent(userId)}`),
  search: (q, priceMax) =>
    request(`/api/search?q=${encodeURIComponent(q)}${priceMax ? `&price_max=${priceMax}` : ""}`),
};
