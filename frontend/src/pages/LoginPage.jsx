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
      await signInWithGoogle(credentialResponse.credential);
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

  return (
    <section className="mx-auto max-w-md py-10">
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Sign in</h1>
        <p className="mt-1 text-sm text-slate-600">
          Use your Google account to continue.
        </p>

        <div className="mt-6 flex flex-col items-center gap-3">
          {!CLIENT_ID ? (
            <div className="w-full rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              <p className="font-semibold">Google sign-in is not configured.</p>
              <p className="mt-1">
                Set <code>VITE_GOOGLE_CLIENT_ID</code> in <code>frontend/.env</code> and{" "}
                <code>GOOGLE_CLIENT_ID</code> in <code>backend/.env</code>, then restart.
              </p>
            </div>
          ) : (
            <GoogleLogin
              onSuccess={handleSuccess}
              onError={() => setError("Google sign-in was cancelled or failed.")}
              useOneTap={false}
              theme="filled_blue"
              size="large"
              shape="rectangular"
            />
          )}

          {loading && <p className="text-xs text-slate-500">Signing in…</p>}

          {error && (
            <div className="w-full rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        <p className="mt-6 text-xs text-slate-500">
          By signing in you agree to use this app for personal learning only.
        </p>
      </div>
    </section>
  );
}
