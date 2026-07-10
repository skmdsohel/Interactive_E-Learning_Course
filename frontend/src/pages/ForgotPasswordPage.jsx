import { useState } from "react";
import { Link } from "react-router-dom";

import { authService } from "../services/authService.js";

function extractError(err, fallback) {
  return (
    err?.response?.data?.error?.message ||
    err?.response?.data?.detail ||
    err?.message ||
    fallback
  );
}

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  // In non-production the API returns the token inline. We surface it so
  // the reset flow can be tested end-to-end without email delivery wired.
  const [devToken, setDevToken] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await authService.forgotPassword(email);
      setSubmitted(true);
      setDevToken(res?.reset_token || null);
    } catch (err) {
      setError(extractError(err, "Request failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-md py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <h1 className="text-2xl font-bold tracking-tight text-fg">Reset your password</h1>
          <p className="mt-1 text-sm text-fg-subtle">
            Enter the email associated with your account. If it exists, we'll
            send you a reset link.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-8 pb-8 pt-6">
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
              Email
            </span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
              placeholder="you@example.com"
            />
          </label>

          {error && (
            <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
              {error}
            </div>
          )}

          {submitted ? (
            <div className="rounded-2xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-900">
              <p className="font-semibold">Check your email</p>
              <p className="mt-1">
                If an account exists for {email}, a reset link has been sent.
              </p>
              {devToken && (
                <div className="mt-3 rounded-lg bg-white/70 p-3 text-xs text-brand-900">
                  <p className="font-semibold">Dev-only reset token:</p>
                  <code className="mt-1 block break-all">{devToken}</code>
                  <Link
                    to={`/reset-password?token=${encodeURIComponent(devToken)}`}
                    className="mt-2 inline-block font-semibold text-brand-700 hover:underline"
                  >
                    Continue to reset →
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Sending…" : "Send reset link"}
            </button>
          )}

          <p className="text-center text-xs text-fg-subtle">
            Remembered it?{" "}
            <Link to="/login" className="text-brand-700 hover:underline">
              Back to sign in
            </Link>
          </p>
        </form>
      </div>
    </section>
  );
}
