import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { authService } from "../services/authService.js";

function extractError(err, fallback) {
  return (
    err?.response?.data?.error?.message ||
    err?.response?.data?.detail ||
    err?.message ||
    fallback
  );
}

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialToken = searchParams.get("token") || "";

  const [token, setToken] = useState(initialToken);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await authService.resetPassword({ resetToken: token, newPassword: password });
      setSuccess(true);
      setTimeout(() => navigate("/login", { replace: true }), 1500);
    } catch (err) {
      setError(extractError(err, "Reset failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-md py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <h1 className="text-2xl font-bold tracking-tight text-fg">Choose a new password</h1>
          <p className="mt-1 text-sm text-fg-subtle">
            Paste the reset token from your email and set a new password.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-8 pb-8 pt-6">
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
              Reset token
            </span>
            <input
              type="text"
              required
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm font-mono text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
              New password
            </span>
            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
              placeholder="Min. 8 characters"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
              Confirm new password
            </span>
            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
            />
          </label>

          {error && (
            <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-2xl border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-900">
              Password updated. Redirecting to sign in…
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || success}
            className="w-full rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-60"
          >
            {submitting ? "Updating…" : "Update password"}
          </button>

          <p className="text-center text-xs text-fg-subtle">
            <Link to="/login" className="text-brand-700 hover:underline">
              Back to sign in
            </Link>
          </p>
        </form>
      </div>
    </section>
  );
}
