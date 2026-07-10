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

  /** Register a local (email/password) account. Returns a fresh session. */
  register: ({ email, password, name, role, department, jobTitle, phone }) =>
    apiClient
      .post("/auth/register", {
        email,
        password,
        name: name || undefined,
        role: role || "learner",
        department: department || undefined,
        job_title: jobTitle || undefined,
        phone: phone || undefined,
      })
      .then((r) => r.data),

  /** Log in with email/password. Returns a fresh session. */
  login: ({ email, password }) =>
    apiClient.post("/auth/login", { email, password }).then((r) => r.data),

  /** Server-side logout hook (currently stateless — client also drops the token). */
  logout: () => apiClient.post("/auth/logout").then((r) => r.data),

  /** Change the current user's password. */
  changePassword: ({ currentPassword, newPassword }) =>
    apiClient
      .put("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      })
      .then((r) => r.data),

  /** Request a password-reset token. In dev the token is returned inline. */
  forgotPassword: (email) =>
    apiClient.post("/auth/forgot-password", { email }).then((r) => r.data),

  /** Consume a reset token and set a new password. */
  resetPassword: ({ resetToken, newPassword }) =>
    apiClient
      .post("/auth/reset-password", {
        reset_token: resetToken,
        new_password: newPassword,
      })
      .then((r) => r.data),

  /** Get the currently authenticated user. Requires the bearer token. */
  me: () => apiClient.get("/auth/me").then((r) => r.data),

  /** Pick a role after sign-in (only allowed if the account isn't already assigned). */
  chooseRole: (role) =>
    apiClient.post("/auth/me/role", { role }).then((r) => r.data),
};
