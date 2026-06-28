import { Link } from "react-router-dom";

import { formatTotalDuration } from "../utils/format.js";

export default function CourseCard({ course }) {
  return (
    <Link
      to={`/courses/${course.id}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition hover:shadow-md hover:border-brand-500"
    >
      <div className="aspect-video bg-slate-100 overflow-hidden">
        {course.thumbnail_url ? (
          <img
            src={course.thumbnail_url}
            alt={course.title}
            className="h-full w-full object-cover transition-transform group-hover:scale-[1.02]"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand-500 to-brand-700 text-white text-lg font-semibold">
            {course.title?.[0] ?? "?"}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-2 p-4">
        <h3 className="font-semibold text-slate-900 line-clamp-2 group-hover:text-brand-700">
          {course.title}
        </h3>
        {course.instructor && (
          <p className="text-xs text-slate-500">by {course.instructor}</p>
        )}
        {course.description && (
          <p className="text-sm text-slate-600 line-clamp-2">{course.description}</p>
        )}
        <div className="mt-auto flex items-center gap-3 pt-2 text-xs text-slate-500">
          <span>{course.section_count} sections</span>
          <span>·</span>
          <span>{course.video_count} videos</span>
          <span>·</span>
          <span>{formatTotalDuration(course.total_duration_seconds)}</span>
        </div>
      </div>
    </Link>
  );
}
