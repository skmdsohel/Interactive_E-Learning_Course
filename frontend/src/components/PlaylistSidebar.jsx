import { useProgress } from "../context/ProgressContext.jsx";
import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import { formatDuration } from "../utils/format.js";

function statusFor(progress) {
  if (!progress) return "none";
  if (progress.completed) return "done";
  if ((progress.position_seconds || 0) > 0) return "partial";
  return "none";
}

export default function PlaylistSidebar() {
  const { course, currentVideo, currentQuiz, selectVideo, selectQuiz } =
    useVideoPlayer();
  const { byVideoId } = useProgress();

  if (!course) return null;

  return (
    <aside className="flex h-full max-h-[80vh] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
      <header className="border-b border-line px-4 py-3">
        <h3 className="text-sm font-semibold text-fg">Course content</h3>
        <p className="text-xs text-fg-subtle">
          {course.sections?.length ?? 0} sections
        </p>
      </header>

      <div className="flex-1 overflow-y-auto">
        {(course.sections || []).map((section) => (
          <section key={section.id} className="border-b border-line last:border-b-0">
            <div className="bg-muted/60 px-4 py-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
                {section.title}
              </p>
              <p className="text-[11px] text-fg-subtle">
                {section.videos?.length ?? 0} videos
                {section.quiz ? " · quiz" : ""}
              </p>
            </div>
            <ul>
              {(section.videos || []).map((video, idx) => {
                const isActive =
                  currentQuiz == null && currentVideo?.id === video.id;
                const status = statusFor(byVideoId?.[video.id]);
                return (
                  <li key={video.id}>
                    <button
                      type="button"
                      onClick={() => selectVideo(video.id)}
                      className={`flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                        isActive
                          ? "bg-brand-50 text-brand-700"
                          : "text-fg-muted hover:bg-muted hover:text-fg"
                      }`}
                    >
                      <StatusBadge status={status} isActive={isActive} index={idx + 1} />
                      <span
                        className={`flex-1 truncate ${
                          status === "done" && !isActive ? "text-fg-subtle" : ""
                        }`}
                      >
                        {video.title}
                      </span>
                      {video.duration_seconds != null && (
                        <span className="shrink-0 text-xs text-fg-subtle">
                          {formatDuration(video.duration_seconds)}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
              {section.quiz && (
                <li>
                  <button
                    type="button"
                    onClick={() => selectQuiz(section.id, section.quiz.id)}
                    className={`flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                      currentQuiz?.quizId === section.quiz.id
                        ? "bg-brand-50 text-brand-700"
                        : "text-fg-muted hover:bg-muted hover:text-fg"
                    }`}
                  >
                    <span
                      className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                        currentQuiz?.quizId === section.quiz.id
                          ? "bg-brand-600 text-brand-fg"
                          : "bg-accent-soft text-accent-soft-fg"
                      }`}
                      title="Section quiz"
                    >
                      <svg viewBox="0 0 20 20" className="h-3 w-3" fill="currentColor" aria-hidden="true">
                        <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm.75 12.5h-1.5v-1.5h1.5v1.5zM12 8.5c0 .9-.4 1.4-1.1 1.9-.6.4-.9.6-.9 1.1H8.5c0-1 .5-1.4 1.2-1.9.5-.4.8-.6.8-1.1 0-.5-.4-.9-1-.9s-1 .4-1.1.9H7c.1-1.3 1.1-2.3 2.5-2.3S12 7.2 12 8.5z" />
                      </svg>
                    </span>
                    <span className="flex-1 truncate font-medium">
                      Section quiz
                    </span>
                    <span className="shrink-0 text-xs text-fg-subtle">
                      {section.quiz.question_count} Qs
                    </span>
                  </button>
                </li>
              )}
            </ul>
          </section>
        ))}
      </div>
    </aside>
  );
}

function StatusBadge({ status, isActive, index }) {
  if (status === "done") {
    return (
      <span
        title="Completed"
        className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-success text-white"
      >
        <svg viewBox="0 0 20 20" className="h-3 w-3" fill="currentColor" aria-hidden="true">
          <path
            fillRule="evenodd"
            d="M16.704 5.29a1 1 0 010 1.42l-7.5 7.5a1 1 0 01-1.414 0l-3.5-3.5a1 1 0 111.414-1.414l2.793 2.793 6.793-6.793a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    );
  }
  return (
    <span
      className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
        isActive
          ? "bg-brand-600 text-brand-fg"
          : status === "partial"
          ? "bg-warning-soft text-warning-soft-fg ring-1 ring-warning/40"
          : "bg-muted text-fg-subtle"
      }`}
      title={status === "partial" ? "In progress" : undefined}
    >
      {index}
    </span>
  );
}
