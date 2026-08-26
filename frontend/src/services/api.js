/**
 * Authenticated fetch wrapper — replaces Axios.
 *
 * Replaces the original api.js which used Axios.
 * Provides the same interface: get, post, put, delete.
 *
 * Changes from original:
 *   - Native fetch() instead of axios
 *   - JWT token read from localStorage
 *   - Unified error handling with error.message from server
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Read the JWT token from localStorage (set by useAuthStore on login).
 */
function getToken() {
  try {
    const auth = JSON.parse(localStorage.getItem("auth-storage") || "{}");
    return auth?.state?.token || null;
  } catch {
    return null;
  }
}

/**
 * Build headers for a request.
 * @param {boolean} includeAuth - whether to include Authorization header
 * @param {boolean} isJson - whether to set Content-Type: application/json
 */
function buildHeaders(includeAuth = true, isJson = true) {
  const headers = {};
  if (isJson) headers["Content-Type"] = "application/json";
  if (includeAuth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Core fetch wrapper.
 * Returns parsed JSON on success, throws Error with server message on failure.
 */
async function request(method, path, { body, params, auth = true } = {}) {
  let url = `${BASE_URL}${path}`;

  // Append query string params
  if (params) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    );
    if (query.toString()) url += `?${query.toString()}`;
  }

  const isFormData = body instanceof FormData;
  const options = {
    method,
    headers: buildHeaders(auth, !isFormData),
    ...(body !== undefined ? { body: isFormData ? body : JSON.stringify(body) } : {}),
  };

  const response = await fetch(url, options);

  // 204 No Content — return null
  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data?.error || data?.detail || `Request failed with status ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return { data };
}

const api = {
  get:    (path, options = {}) => request("GET",    path, options),
  post:   (path, body, options = {}) => request("POST",   path, { ...options, body }),
  put:    (path, body, options = {}) => request("PUT",    path, { ...options, body }),
  delete: (path, options = {}) => request("DELETE",  path, options),
  patch:  (path, body, options = {}) => request("PATCH",  path, { ...options, body }),
};

export default api;
