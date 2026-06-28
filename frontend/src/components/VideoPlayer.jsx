import { useEffect, useRef } from "react";

import { useProgress } from "../context/ProgressContext.jsx";
import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import { videoService } from "../services/videoService.js";

export default function VideoPlayer() {
  const { currentVideo, playNext, hasNext, hasPrevious, playPrevious } =
    useVideoPlayer();
  const { byVideoId, recordPosition, markComplete } = useProgress();
  const videoRef = useRef(null);
  const resumedRef = useRef(null); // video id we already attempted to resume

  // When the selected video changes, reload the <video> element so the
  // browser issues a fresh Range request against the new stream URL.
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
      resumedRef.current = null;
    }
  }, [currentVideo?.id]);

  if (!currentVideo) {
    return (
      <div className="flex aspect-video w-full items-center justify-center rounded-2xl border border-line bg-black/95 text-sm text-fg-subtle">
        Select a video to start playing
      </div>
    );
  }

  const handleLoadedMetadata = () => {
    const el = videoRef.current;
    if (!el || resumedRef.current === currentVideo.id) return;
    resumedRef.current = currentVideo.id;
    const saved = byVideoId?.[currentVideo.id];
    if (!saved) return;
    // Skip resume if already completed or essentially at the end.
    const duration = el.duration || saved.position_seconds + 10;
    if (saved.completed) return;
    if (saved.position_seconds > 2 && saved.position_seconds < duration - 5) {
      try {
        el.currentTime = saved.position_seconds;
      } catch {
        /* ignore — some sources disallow seeking before play */
      }
    }
  };

  const handleTimeUpdate = () => {
    const el = videoRef.current;
    if (!el) return;
    recordPosition(currentVideo.id, el.currentTime, el.duration || null);
  };

  const handleEnded = async () => {
    await markComplete(currentVideo.id);
    if (hasNext) playNext();
  };

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-2xl bg-black shadow-[var(--shadow-pop)] ring-1 ring-line">
        <video
          ref={videoRef}
          key={currentVideo.id}
          className="aspect-video w-full bg-black"
          controls
          preload="metadata"
          playsInline
          onLoadedMetadata={handleLoadedMetadata}
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleEnded}
        >
          <source src={videoService.streamUrl(currentVideo.id)} />
          Your browser does not support the video tag.
        </video>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-fg-subtle">
            {currentVideo.sectionTitle}
          </p>
          <h2 className="truncate text-lg font-semibold text-fg">
            {currentVideo.title}
          </h2>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={playPrevious}
            disabled={!hasPrevious}
            className="rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong disabled:cursor-not-allowed disabled:opacity-50"
          >
            ← Previous
          </button>
          <button
            type="button"
            onClick={playNext}
            disabled={!hasNext}
            className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      </div>

      {currentVideo.description && (
        <p className="text-sm text-fg-muted">{currentVideo.description}</p>
      )}
    </div>
  );
}
