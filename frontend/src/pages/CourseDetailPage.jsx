import { useCallback, useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import PlaylistSidebar from "../components/PlaylistSidebar.jsx";
import Spinner from "../components/Spinner.jsx";
import VideoPlayer from "../components/VideoPlayer.jsx";
import { useProgress } from "../context/ProgressContext.jsx";
import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import useFetch from "../hooks/useFetch.js";
import { courseService } from "../services/courseService.js";

export default function CourseDetailPage() {
  const { id } = useParams();
  const courseId = Number(id);
  const { loadCourse, reset, course: ctxCourse } = useVideoPlayer();
  const { loadCourseProgress, summary } = useProgress();

  const fetcher = useCallback(() => courseService.get(courseId), [courseId]);
  const { data: course, error, loading } = useFetch(fetcher, [courseId]);

  // Load course-progress in parallel with the course payload.
  useEffect(() => {
    if (!Number.isFinite(courseId)) return;
    loadCourseProgress(courseId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  // When both the course and its progress are loaded, mount the player and
  // jump to the user's last-watched video (if any).
  useEffect(() => {
    if (!course) return;
    const initialVideoId = summary?.last_video_id || null;
    loadCourse(course, initialVideoId);
    return () => reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [course, summary?.last_video_id]);

  if (loading) {
    return (
      <div className="py-12">
        <Spinner label="Loading course…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load course.
        </div>
        <Link to="/courses" className="text-sm font-medium text-brand-700 hover:text-brand-600">
          ← Back to courses
        </Link>
      </div>
    );
  }

  if (!course || !ctxCourse) return null;

  const percent = summary?.percent_complete ?? 0;
  const completed = summary?.completed_videos ?? 0;
  const total = summary?.total_videos ?? 0;

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <Link to="/courses" className="hover:text-slate-900">
          Courses
        </Link>
        <span>/</span>
        <span className="truncate text-slate-900">{course.title}</span>
      </div>

      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">{course.title}</h1>
        {course.instructor && (
          <p className="text-sm text-slate-500">by {course.instructor}</p>
        )}
        {course.description && (
          <p className="mt-2 text-sm text-slate-700">{course.description}</p>
        )}

        {summary && total > 0 && (
          <div className="mt-3 max-w-md">
            <div className="flex items-center justify-between text-xs text-slate-600">
              <span>
                <span className="font-semibold text-slate-900">{percent}%</span> complete
              </span>
              <span>
                {completed} / {total} videos
              </span>
            </div>
            <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full bg-emerald-500 transition-all"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        )}
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0">
          <VideoPlayer />
        </div>
        <div className="lg:sticky lg:top-4 lg:self-start">
          <PlaylistSidebar />
        </div>
      </div>
    </section>
  );
}
