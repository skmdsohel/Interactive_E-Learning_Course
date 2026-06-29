import { GoogleLogin } from "@react-oauth/google";
import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, signInWithGoogle, loading } = useAuth();
  const [error, setError] = useState(null);
  const [signupRole, setSignupRole] = useState("learner");

  const from = location.state?.from?.pathname || "/";

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSuccess = async (credentialResponse) => {
    setError(null);
    if (!credentialResponse?.credential) {
      setError("No credential returned from Google.");
      return;
    }
    try {
      await signInWithGoogle(credentialResponse.credential, signupRole);
      navigate(from, { replace: true });
    } catch (err) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Sign-in failed.";
      setError(msg);
    }
  };

  const roleOptions = [
    {
      value: "learner",
      label: "Learner",
      hint: "Watch lessons, take quizzes, and earn certificates.",
    },
    {
      value: "instructor",
      label: "Instructor",
      hint: "Create courses, upload videos, and manage quizzes.",
    },
  ];

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
              <h1 className="text-2xl font-bold tracking-tight text-fg">Welcome</h1>
              <p className="text-sm text-fg-subtle">
                Sign in or create an account with Google.
              </p>
            </div>
          </div>
        </div>

        <div className="px-8 pt-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
            I'm signing up as
          </p>
          <p className="mt-1 text-xs text-fg-subtle">
            New here? Pick a role for your account. Returning users keep the
            role they already chose.
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {roleOptions.map((opt) => {
              const active = signupRole === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setSignupRole(opt.value)}
                  className={`rounded-2xl border p-3 text-left text-sm transition ${
                    active
                      ? "border-brand-500 bg-brand-soft text-brand-soft-fg shadow-sm"
                      : "border-line bg-elevated text-fg-muted hover:border-line-strong hover:text-fg"
                  }`}
                >
                  <div className="flex items-center gap-2 font-semibold text-fg">
                    <span
                      className={`inline-flex h-4 w-4 items-center justify-center rounded-full border ${
                        active
                          ? "border-brand-600 bg-brand-600"
                          : "border-line"
                      }`}
                    >
                      {active && (
                        <span className="h-1.5 w-1.5 rounded-full bg-brand-fg" />
                      )}
                    </span>
                    {opt.label}
                  </div>
                  <p className="mt-1 text-xs text-fg-subtle">{opt.hint}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Auth panel — light surface keeps Google's button visually integrated in both themes. */}
        <div className="mt-6 border-y border-line bg-[#f8fafc] px-8 py-8 dark:bg-[#e9eef5]">
          <div className="flex items-center justify-center gap-3 text-[11px] font-medium uppercase tracking-[0.18em] text-slate-500">
            <span className="h-px flex-1 bg-slate-300" />
            <span>Continue with</span>
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
                  onSuccess={handleSuccess}
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
            By signing in you agree to use this app for personal learning only.
          </p>
        </div>
      </div>
    </section>
  );
}
