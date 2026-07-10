import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

function extractError(err, fallback) {
  return (
    err?.response?.data?.error?.message ||
    err?.response?.data?.detail ||
    err?.message ||
    fallback
  );
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, registerWithEmail, loading } = useAuth();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: "learner",
    department: "",
    jobTitle: "",
    phone: "",
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const from = location.state?.from?.pathname || "/";

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const update = (key) => (event) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await registerWithEmail({
        email: form.email,
        password: form.password,
        name: form.name,
        role: form.role,
        department: form.department,
        jobTitle: form.jobTitle,
        phone: form.phone,
      });
      navigate(from, { replace: true });
    } catch (err) {
      setError(extractError(err, "Registration failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-lg py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <h1 className="text-2xl font-bold tracking-tight text-fg">Create your account</h1>
          <p className="mt-1 text-sm text-fg-subtle">
            Sign up with your work email to get started.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4 px-8 pb-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Full name">
              <input
                type="text"
                autoComplete="name"
                value={form.name}
                onChange={update("name")}
                className={inputClass}
                placeholder="Jane Doe"
              />
            </Field>
            <Field label="Email" required>
              <input
                type="email"
                autoComplete="email"
                required
                value={form.email}
                onChange={update("email")}
                className={inputClass}
                placeholder="you@example.com"
              />
            </Field>
            <Field label="Password" required>
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={form.password}
                onChange={update("password")}
                className={inputClass}
                placeholder="Min. 8 characters"
              />
            </Field>
            <Field label="Confirm password" required>
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={form.confirmPassword}
                onChange={update("confirmPassword")}
                className={inputClass}
              />
            </Field>
            <Field label="Role" required>
              <select
                value={form.role}
                onChange={update("role")}
                className={inputClass}
              >
                <option value="learner">Employee (Learner)</option>
                <option value="instructor">Trainer (Instructor)</option>
              </select>
            </Field>
            <Field label="Department">
              <input
                type="text"
                value={form.department}
                onChange={update("department")}
                className={inputClass}
                placeholder="Engineering"
              />
            </Field>
            <Field label="Job title">
              <input
                type="text"
                value={form.jobTitle}
                onChange={update("jobTitle")}
                className={inputClass}
                placeholder="Software Engineer"
              />
            </Field>
            <Field label="Phone">
              <input
                type="tel"
                value={form.phone}
                onChange={update("phone")}
                className={inputClass}
                placeholder="+1 555 123 4567"
              />
            </Field>
          </div>

          {error && (
            <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || loading}
            className="w-full rounded-full bg-brand-600 px-4 py-2 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-60"
          >
            {submitting ? "Creating account…" : "Create account"}
          </button>

          <p className="text-center text-xs text-fg-subtle">
            Already have an account?{" "}
            <Link to="/login" className="text-brand-700 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </section>
  );
}

const inputClass =
  "w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-fg outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

function Field({ label, required, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-fg-subtle">
        {label}
        {required ? <span className="text-danger"> *</span> : null}
      </span>
      {children}
    </label>
  );
}
