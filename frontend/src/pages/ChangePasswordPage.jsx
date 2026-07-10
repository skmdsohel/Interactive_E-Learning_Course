import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

function extractError(err, fallback) {
  return (
    err?.response?.data?.error?.message ||
    err?.response?.data?.detail ||
    err?.message ||
    fallback
  );
}

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const { user, hasLocalPassword, changePassword } = useAuth();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSuccess(false);
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await changePassword({ currentPassword, newPassword });
      setSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(extractError(err, "Password change failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-md py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <h1 className="text-2xl font-bold tracking-tight text-fg">Change password</h1>
          <p className="mt-1 text-sm text-fg-subtle">
            Signed in as <span className="font-medium text-fg">{user?.email}</span>
          </p>
        </div>

        {!hasLocalPassword ? (
          <div className="m-8 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Password change is not available.</p>
            <p className="mt-1">
              This account signs in with Google. Manage your credentials in your
              Google account settings.
            </p>
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="mt-3 rounded-full border border-amber-400 bg-white px-4 py-1.5 text-xs font-semibold text-amber-900 hover:bg-amber-100"
            >
              Go back
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 px-8 pb-8 pt-6">
            <label className="block">
              <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
                Current password
              </span>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
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
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
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
                Password updated.
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Updating…" : "Update password"}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
