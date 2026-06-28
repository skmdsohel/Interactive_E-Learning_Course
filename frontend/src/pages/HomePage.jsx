import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">LMS</h1>
        <p className="mt-2 text-slate-600">
          Phase 1 scaffold — backend architecture is in place. Authentication, courses,
          and learner features will be added in later phases.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card title="Backend" body="FastAPI + SQLAlchemy 2.0 + Alembic + MySQL." />
        <Card title="Frontend" body="React 19 + Vite + Tailwind v4 + React Router." />
        <Card
          title="Health"
          body="Verify the API is reachable from the browser."
          action={
            <Link
              to="/health"
              className="text-sm font-medium text-brand-700 hover:text-brand-600"
            >
              Open health page →
            </Link>
          }
        />
      </div>
    </section>
  );
}

function Card({ title, body, action }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-900">{title}</h2>
      <p className="mt-1 text-sm text-slate-600">{body}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
