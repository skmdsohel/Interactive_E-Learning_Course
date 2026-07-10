import { GoogleLogin } from "@react-oauth/google";
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function extractError(err, fallback) {
  return (
    err?.response?.data?.error?.message ||
    err?.response?.data?.detail ||
    err?.message ||
    fallback
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, signInWithGoogle, signInWithEmail, loading } = useAuth();
  const [error, setError] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const from = location.state?.from?.pathname || "/";

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    setError(null);
    if (!credentialResponse?.credential) {
      setError("No credential returned from Google.");
      return;
    }
    try {
      await signInWithGoogle(credentialResponse.credential);
      navigate(from, { replace: true });
    } catch (err) {
      setError(extractError(err, "Sign-in failed."));
    }
  };

  const handleEmailSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    if (!email || !password) {
      setError("Enter both email and password.");
      return;
    }
    setSubmitting(true);
    try {
      await signInWithEmail({ email, password });
      navigate(from, { replace: true });
    } catch (err) {
      setError(extractError(err, "Login failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-md py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-brand-fg shadow-sm">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Z" />
                <path d="M5 17h11" />
              </svg>
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-fg">Welcome back</h1>
              <p className="text-sm text-fg-subtle">Sign in to continue learning.</p>
            </div>
          </div>
        </div>

        {/* Email + password form */}
        <form onSubmit={handleEmailSubmit} className="mt-8 space-y-4 px-8">
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
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
              Password
            </span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
              placeholder="••••••••"
            />
          </label>
          <button
            type="submit"
            disabled={submitting || loading}
            className="w-full rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-60"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
          <div className="flex items-center justify-between text-xs">
            <Link to="/forgot-password" className="text-brand-700 hover:underline">
              Forgot password?
            </Link>
            <Link to="/register" className="text-brand-700 hover:underline">
              Create an account
            </Link>
          </div>
        </form>

        {/* Google sign-in panel */}
        <div className="mt-8 border-y border-line bg-[#f8fafc] px-8 py-8 dark:bg-[#e9eef5]">
          <div className="flex items-center justify-center gap-3 text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">
            <span className="h-px flex-1 bg-slate-300" />
            <span>Or continue with</span>
            <span className="h-px flex-1 bg-slate-300" />
          </div>

          <div className="mt-5 flex flex-col items-center gap-3">
            {!CLIENT_ID ? (
              <div className="w-full rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
                <p className="font-semibold">Google sign-in is not configured.</p>
                <p className="mt-1">
                  Set <code>VITE_GOOGLE_CLIENT_ID</code> in <code>frontend/.env</code> and{" "}
                  <code>GOOGLE_CLIENT_ID</code> in <code>backend/.env</code>, then restart.
                </p>
              </div>
            ) : (
              <div className="w-full overflow-hidden rounded-full ring-1 ring-slate-300/70 [color-scheme:light]">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError("Google sign-in was cancelled or failed.")}
                  useOneTap={false}
                  theme="outline"
                  size="large"
                  shape="pill"
                  width="320"
                  text="continue_with"
                />
              </div>
            )}

            {loading && <p className="text-xs text-slate-600">Signing in…</p>}
          </div>
        </div>

        <div className="px-8 pb-8 pt-6">
          {error && (
            <div className="mb-4 w-full rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
              {error}
            </div>
          )}
          <p className="text-xs text-fg-subtle">
            New here? You'll pick your role (Learner or Instructor) right after
            signing in.
          </p>
        </div>
      </div>
    </section>
  );
}
