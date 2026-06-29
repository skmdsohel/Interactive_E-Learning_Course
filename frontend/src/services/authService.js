import apiClient from "./apiClient.js";

export const authService = {
  /**
   * Exchange a Google ID token for an app-issued JWT.
   * `role` ("learner" | "instructor") is only applied for brand-new accounts.
   */
  signInWithGoogle: (idToken, role) =>
    apiClient
      .post("/auth/google", { id_token: idToken, role: role || undefined })
      .then((r) => r.data),

  /** Get the currently authenticated user. Requires the bearer token. */
  me: () => apiClient.get("/auth/me").then((r) => r.data),

  /** Pick a role after sign-in (only allowed if the account isn't already assigned). */
  chooseRole: (role) =>
    apiClient.post("/auth/me/role", { role }).then((r) => r.data),
};
