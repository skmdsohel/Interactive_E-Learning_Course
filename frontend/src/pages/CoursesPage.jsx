import { useCallback } from "react";

import CourseCard from "../components/CourseCard.jsx";
import Spinner from "../components/Spinner.jsx";
import useFetch from "../hooks/useFetch.js";
import { courseService } from "../services/courseService.js";

export default function CoursesPage() {
  const fetcher = useCallback(() => courseService.list(), []);
  const { data, error, loading, refetch } = useFetch(fetcher, []);

  return (
    <section className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">All courses</h1>
          <p className="text-sm text-slate-600">Browse the catalog and pick a course to start learning.</p>
        </div>
        <button
          type="button"
          onClick={refetch}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      {loading && <Spinner label="Loading courses…" />}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load courses. Is the backend running?
        </div>
      )}

      {!loading && !error && data?.length === 0 && (
        <div className="rounded-md border border-slate-200 bg-white p-8 text-center text-slate-600">
          No courses yet. Drop videos under <code>backend/storage/videos/</code> and run the seed script.
        </div>
      )}

      {!loading && !error && data?.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((c) => (
            <CourseCard key={c.id} course={c} />
          ))}
        </div>
      )}
    </section>
  );
}
