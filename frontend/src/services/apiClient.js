import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const apiClient = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Phase 2: handle 401 / token refresh here.
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error("[api]", error?.response?.status, error?.config?.url, error?.response?.data);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
