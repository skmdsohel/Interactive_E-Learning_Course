import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

const VideoPlayerContext = createContext(null);

/**
 * Flatten a course's nested sections → videos into a single ordered playlist.
 */
function buildPlaylist(course) {
  if (!course?.sections) return [];
  const items = [];
  for (const section of course.sections) {
    for (const video of section.videos || []) {
      items.push({
        ...video,
        sectionId: section.id,
        sectionTitle: section.title,
      });
    }
  }
  return items;
}

export function VideoPlayerProvider({ children }) {
  const [course, setCourse] = useState(null);
  const [currentVideoId, setCurrentVideoId] = useState(null);

  const playlist = useMemo(() => buildPlaylist(course), [course]);

  const currentIndex = useMemo(
    () => playlist.findIndex((v) => v.id === currentVideoId),
    [playlist, currentVideoId]
  );

  const currentVideo = currentIndex >= 0 ? playlist[currentIndex] : null;
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < playlist.length - 1;

  const loadCourse = useCallback((nextCourse, initialVideoId = null) => {
    setCourse(nextCourse);
    const firstId =
      initialVideoId ??
      nextCourse?.sections?.flatMap((s) => s.videos || [])?.[0]?.id ??
      null;
    setCurrentVideoId(firstId);
  }, []);

  const selectVideo = useCallback(
    (videoId) => {
      if (playlist.some((v) => v.id === videoId)) {
        setCurrentVideoId(videoId);
      }
    },
    [playlist]
  );

  const playNext = useCallback(() => {
    if (hasNext) setCurrentVideoId(playlist[currentIndex + 1].id);
  }, [hasNext, playlist, currentIndex]);

  const playPrevious = useCallback(() => {
    if (hasPrevious) setCurrentVideoId(playlist[currentIndex - 1].id);
  }, [hasPrevious, playlist, currentIndex]);

  const reset = useCallback(() => {
    setCourse(null);
    setCurrentVideoId(null);
  }, []);

  const value = useMemo(
    () => ({
      course,
      playlist,
      currentVideo,
      currentIndex,
      hasPrevious,
      hasNext,
      loadCourse,
      selectVideo,
      playNext,
      playPrevious,
      reset,
    }),
    [
      course,
      playlist,
      currentVideo,
      currentIndex,
      hasPrevious,
      hasNext,
      loadCourse,
      selectVideo,
      playNext,
      playPrevious,
      reset,
    ]
  );

  return (
    <VideoPlayerContext.Provider value={value}>
      {children}
    </VideoPlayerContext.Provider>
  );
}

export function useVideoPlayer() {
  const ctx = useContext(VideoPlayerContext);
  if (!ctx) {
    throw new Error("useVideoPlayer must be used inside <VideoPlayerProvider>");
  }
  return ctx;
}
