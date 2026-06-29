import { useCallback, useEffect, useMemo } from "react";
import { Link, useParams } from "react-router-dom";

import CertificateBanner from "../components/CertificateBanner.jsx";
import PlaylistSidebar from "../components/PlaylistSidebar.jsx";
import QuizPanel from "../components/QuizPanel.jsx";
import Spinner from "../components/Spinner.jsx";
import VideoPlayer from "../components/VideoPlayer.jsx";
import { useProgress } from "../context/ProgressContext.jsx";
import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import useFetch from "../hooks/useFetch.js";
import { courseService } from "../services/courseService.js";

export default function CourseDetailPage() {
  const { id } = useParams();
  const courseId = Number(id);
  const {
    loadCourse,
    reset,
    course: ctxCourse,
    currentQuiz,
  } = useVideoPlayer();
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

  const activeQuizSectionTitle = useMemo(() => {
    if (!currentQuiz || !ctxCourse) return null;
    const sec = ctxCourse.sections?.find((s) => s.id === currentQuiz.sectionId);
    return sec?.title || null;
  }, [currentQuiz, ctxCourse]);

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
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
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
      <div className="flex items-center gap-2 text-sm text-fg-subtle">
        <Link to="/courses" className="hover:text-fg">
          Courses
        </Link>
        <span className="text-line-strong">/</span>
        <span className="truncate text-fg">{course.title}</span>
      </div>

      <header className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-fg">{course.title}</h1>
        {course.instructor && (
          <p className="text-sm text-fg-subtle">by {course.instructor}</p>
        )}
        {course.description && (
          <p className="mt-2 max-w-3xl text-sm text-fg-muted">{course.description}</p>
        )}

        {summary && total > 0 && (
          <div className="mt-4 max-w-md">
            <div className="flex items-center justify-between text-xs text-fg-muted">
              <span>
                <span className="font-semibold text-fg">{percent}%</span> complete
              </span>
              <span>
                {completed} / {total} videos
              </span>
            </div>
            <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-success transition-all duration-500"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        )}

        {summary && total > 0 && (
          <CertificateBanner
            courseId={courseId}
            courseTitle={course.title}
            percentComplete={percent}
          />
        )}
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0">
          {currentQuiz ? (
            <QuizPanel
              key={currentQuiz.quizId}
              quizId={currentQuiz.quizId}
              sectionTitle={activeQuizSectionTitle}
            />
          ) : (
            <VideoPlayer />
          )}
        </div>
        <div className="lg:sticky lg:top-20 lg:self-start">
          <PlaylistSidebar />
        </div>
      </div>
    </section>
  );
}
