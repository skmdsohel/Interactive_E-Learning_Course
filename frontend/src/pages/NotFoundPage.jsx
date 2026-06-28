import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section className="text-center py-16">
      <p className="text-sm font-semibold text-brand-600">404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Page not found</h1>
      <p className="mt-2 text-slate-600">The page you’re looking for doesn’t exist.</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
      >
        Go home
      </Link>
    </section>
  );
}
