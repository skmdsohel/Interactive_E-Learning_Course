import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import { formatDuration } from "../utils/format.js";

export default function PlaylistSidebar() {
  const { course, currentVideo, selectVideo } = useVideoPlayer();

  if (!course) return null;

  return (
    <aside className="flex h-full max-h-[80vh] flex-col overflow-hidden rounded-lg border border-slate-200 bg-white">
      <header className="border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">Course content</h3>
        <p className="text-xs text-slate-500">
          {course.sections?.length ?? 0} sections
        </p>
      </header>

      <div className="flex-1 overflow-y-auto">
        {(course.sections || []).map((section) => (
          <section key={section.id} className="border-b border-slate-100 last:border-b-0">
            <div className="bg-slate-50 px-4 py-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                {section.title}
              </p>
              <p className="text-[11px] text-slate-500">
                {section.videos?.length ?? 0} videos
              </p>
            </div>
            <ul>
              {(section.videos || []).map((video, idx) => {
                const isActive = currentVideo?.id === video.id;
                return (
                  <li key={video.id}>
                    <button
                      type="button"
                      onClick={() => selectVideo(video.id)}
                      className={`flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                        isActive
                          ? "bg-brand-50 text-brand-700"
                          : "text-slate-700 hover:bg-slate-50"
                      }`}
                    >
                      <span
                        className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
                          isActive
                            ? "bg-brand-600 text-white"
                            : "bg-slate-200 text-slate-600"
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <span className="flex-1 truncate">{video.title}</span>
                      {video.duration_seconds != null && (
                        <span className="shrink-0 text-xs text-slate-500">
                          {formatDuration(video.duration_seconds)}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </div>
    </aside>
  );
}
