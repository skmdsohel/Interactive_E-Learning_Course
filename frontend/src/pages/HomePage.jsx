import { useCallback } from "react";
import { Link } from "react-router-dom";

import CourseCard from "../components/CourseCard.jsx";
import Spinner from "../components/Spinner.jsx";
import useFetch from "../hooks/useFetch.js";
import { courseService } from "../services/courseService.js";

export default function HomePage() {
  const fetcher = useCallback(() => courseService.list(), []);
  const { data, error, loading } = useFetch(fetcher, []);

  const featured = (data || []).slice(0, 6);

  return (
    <section className="space-y-8">
      <div className="rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 p-8 text-white shadow-sm">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Learn at your own pace</h1>
        <p className="mt-2 max-w-2xl text-brand-50">
          Browse the catalog, pick a course, and start watching. Lessons resume seamlessly with HTTP range streaming.
        </p>
        <Link
          to="/courses"
          className="mt-5 inline-block rounded-md bg-white px-4 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50"
        >
          Browse all courses
        </Link>
      </div>

      <div>
        <div className="mb-3 flex items-end justify-between">
          <h2 className="text-xl font-semibold">Featured courses</h2>
          <Link to="/courses" className="text-sm font-medium text-brand-700 hover:text-brand-600">
            See all →
          </Link>
        </div>

        {loading && <Spinner label="Loading courses…" />}

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            Failed to load courses. Is the backend running?
          </div>
        )}

        {!loading && !error && featured.length === 0 && (
          <div className="rounded-md border border-slate-200 bg-white p-8 text-center text-slate-600">
            No courses yet. Drop videos under <code>backend/storage/videos/</code> and run the seed script.
          </div>
        )}

        {!loading && !error && featured.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((c) => (
              <CourseCard key={c.id} course={c} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
