import { useState } from "react";

import { useAuth } from "../context/AuthContext.jsx";

const ROLE_OPTIONS = [
  {
    value: "learner",
    label: "Learner",
    hint: "Browse courses, watch lessons, take quizzes, and earn certificates.",
  },
  {
    value: "instructor",
    label: "Instructor",
    hint: "Create courses, upload videos, and manage quizzes for your students.",
  },
];

export default function RoleSelectionPage() {
  const { user, chooseRole, logout } = useAuth();
  const [selected, setSelected] = useState("learner");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleContinue = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await chooseRole(selected);
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to save role."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-lg py-12">
      <div className="overflow-hidden rounded-3xl border border-line bg-surface shadow-[var(--shadow-pop)]">
        <div className="px-8 pt-8">
          <h1 className="text-2xl font-bold tracking-tight text-fg">
            Welcome{user?.name ? `, ${user.name}` : ""}!
          </h1>
          <p className="mt-1 text-sm text-fg-subtle">
            One last step: choose how you'll use LearnSphere. You won't be
            asked again the next time you sign in.
          </p>
        </div>

        <div className="px-8 pt-6">
          <div className="space-y-3">
            {ROLE_OPTIONS.map((opt) => {
              const active = selected === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setSelected(opt.value)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    active
                      ? "border-brand-500 bg-brand-soft text-brand-soft-fg shadow-sm"
                      : "border-line bg-elevated text-fg-muted hover:border-line-strong hover:text-fg"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-flex h-5 w-5 items-center justify-center rounded-full border ${
                        active ? "border-brand-600 bg-brand-600" : "border-line"
                      }`}
                    >
                      {active && (
                        <span className="h-2 w-2 rounded-full bg-brand-fg" />
                      )}
                    </span>
                    <span className="text-base font-semibold text-fg">
                      {opt.label}
                    </span>
                  </div>
                  <p className="mt-2 pl-8 text-sm text-fg-subtle">{opt.hint}</p>
                </button>
              );
            })}
          </div>

          {error && (
            <div className="mt-4 rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
              {error}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 px-8 pb-8 pt-6">
          <button
            type="button"
            onClick={logout}
            className="text-xs font-medium text-fg-muted hover:text-fg"
          >
            Sign out
          </button>
          <button
            type="button"
            onClick={handleContinue}
            disabled={submitting}
            className="rounded-full bg-brand-600 px-5 py-2 text-sm font-semibold text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Saving…" : "Continue"}
          </button>
        </div>
      </div>
    </section>
  );
}
