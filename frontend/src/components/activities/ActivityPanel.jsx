import { useCallback, useEffect, useState } from "react";

import Spinner from "../Spinner.jsx";
import { activityService } from "../../services/activityService.js";
import FlashcardsActivity from "./FlashcardsActivity.jsx";
import MatchingActivity from "./MatchingActivity.jsx";
import OrderingActivity from "./OrderingActivity.jsx";

/** Renders one activity (fetched by id) using the component for its kind. */
export default function ActivityPanel({ activityId, sectionTitle }) {
  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setActivity(await activityService.get(activityId));
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load activity."
      );
    } finally {
      setLoading(false);
    }
  }, [activityId]);

  useEffect(() => {
    if (Number.isFinite(activityId)) load();
  }, [activityId, load]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-line bg-surface p-6">
        <Spinner label="Loading activity…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger-soft p-4 text-sm text-danger-soft-fg">
        {error}
      </div>
    );
  }

  if (!activity) return null;

  return (
    <section className="rounded-2xl border border-line bg-surface p-5 shadow-[var(--shadow-card)]">
      <header className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-700">
            {kindLabel(activity.kind)}
            {sectionTitle ? ` · ${sectionTitle}` : ""}
          </p>
          <h2 className="text-lg font-semibold text-fg">{activity.title}</h2>
        </div>
      </header>
      <ActivityBody activity={activity} />
    </section>
  );
}

function ActivityBody({ activity }) {
  if (activity.kind === "matching") return <MatchingActivity activity={activity} />;
  if (activity.kind === "flashcards") return <FlashcardsActivity activity={activity} />;
  if (activity.kind === "ordering") return <OrderingActivity activity={activity} />;
  return (
    <p className="text-sm text-fg-subtle">
      Unsupported activity type: <code>{activity.kind}</code>
    </p>
  );
}

function kindLabel(kind) {
  if (kind === "matching") return "Drag & Drop Matching";
  if (kind === "flashcards") return "Flip Flashcards";
  if (kind === "ordering") return "Sequence / Ordering";
  return "Activity";
}
