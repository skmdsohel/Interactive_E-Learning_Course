import apiClient from "./apiClient.js";

export const authService = {
  /** Exchange a Google ID token for an app-issued JWT. */
  signInWithGoogle: (idToken) =>
    apiClient.post("/auth/google", { id_token: idToken }).then((r) => r.data),

  /** Get the currently authenticated user. Requires the bearer token. */
  me: () => apiClient.get("/auth/me").then((r) => r.data),
};
