import { useEffect, useRef } from "react";

import { useVideoPlayer } from "../context/VideoPlayerContext.jsx";
import { videoService } from "../services/videoService.js";

export default function VideoPlayer() {
  const { currentVideo, playNext, hasNext, hasPrevious, playPrevious } =
    useVideoPlayer();
  const videoRef = useRef(null);

  // When the selected video changes, reload the <video> element so the
  // browser issues a fresh Range request against the new stream URL.
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
    }
  }, [currentVideo?.id]);

  if (!currentVideo) {
    return (
      <div className="flex aspect-video w-full items-center justify-center rounded-lg bg-slate-900 text-slate-400">
        Select a video to start playing
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-lg bg-black shadow">
        <video
          ref={videoRef}
          key={currentVideo.id}
          className="aspect-video w-full bg-black"
          controls
          preload="metadata"
          playsInline
          onEnded={() => {
            if (hasNext) playNext();
          }}
        >
          <source src={videoService.streamUrl(currentVideo.id)} />
          Your browser does not support the video tag.
        </video>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            {currentVideo.sectionTitle}
          </p>
          <h2 className="truncate text-lg font-semibold text-slate-900">
            {currentVideo.title}
          </h2>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={playPrevious}
            disabled={!hasPrevious}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            ← Previous
          </button>
          <button
            type="button"
            onClick={playNext}
            disabled={!hasNext}
            className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      </div>

      {currentVideo.description && (
        <p className="text-sm text-slate-600">{currentVideo.description}</p>
      )}
    </div>
  );
}
