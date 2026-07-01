import { useEffect, useState } from "react";

/**
 * Flip flashcards.
 *
 * payload shape: { cards: [{ front, back }, ...] }
 *
 * Learner clicks a card to flip front <-> back. Prev/Next moves through the
 * deck and always resets to the front face so the next card lands unflipped.
 */
export default function FlashcardsActivity({ activity }) {
  const cards = activity?.payload?.cards || [];
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState(() => new Set());

  useEffect(() => {
    setIndex(0);
    setFlipped(false);
    setKnown(new Set());
  }, [activity?.id]);

  if (cards.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-line p-6 text-sm text-fg-subtle">
        No cards in this deck yet.
      </p>
    );
  }

  const card = cards[index];
  const goto = (delta) => {
    setFlipped(false);
    setIndex((i) => (i + delta + cards.length) % cards.length);
  };

  const toggleKnown = () => {
    setKnown((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {activity.instructions && (
        <p className="text-sm text-fg-muted">{activity.instructions}</p>
      )}

      <div className="flex items-center justify-between text-xs text-fg-subtle">
        <span>
          Card <span className="font-semibold text-fg">{index + 1}</span> of{" "}
          {cards.length}
        </span>
        <span>
          {known.size} marked known
        </span>
      </div>

      <div
        className="mx-auto w-full max-w-xl"
        style={{ perspective: "1200px" }}
      >
        <button
          type="button"
          onClick={() => setFlipped((v) => !v)}
          aria-label={flipped ? "Show front of card" : "Show back of card"}
          className="relative block w-full text-left"
          style={{ minHeight: "16rem" }}
        >
          <div
            className="relative h-64 w-full transition-transform duration-500"
            style={{
              transformStyle: "preserve-3d",
              transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
            }}
          >
            <div
              className="absolute inset-0 flex items-center justify-center rounded-2xl border border-line bg-surface p-6 text-center shadow-[var(--shadow-card)]"
              style={{ backfaceVisibility: "hidden" }}
            >
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">
                  Front
                </p>
                <p className="mt-3 text-xl font-medium text-fg">{card.front}</p>
                <p className="mt-6 text-xs text-fg-subtle">Click to flip</p>
              </div>
            </div>
            <div
              className="absolute inset-0 flex items-center justify-center rounded-2xl border border-brand-500 bg-brand-50 p-6 text-center shadow-[var(--shadow-card)]"
              style={{
                backfaceVisibility: "hidden",
                transform: "rotateY(180deg)",
              }}
            >
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">
                  Back
                </p>
                <p className="mt-3 text-lg text-fg">{card.back}</p>
                <p className="mt-6 text-xs text-fg-subtle">Click to flip back</p>
              </div>
            </div>
          </div>
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => goto(-1)}
            className="rounded-full border border-line px-3 py-1.5 text-sm font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            ← Previous
          </button>
          <button
            type="button"
            onClick={() => goto(1)}
            className="rounded-full border border-line px-3 py-1.5 text-sm font-medium text-fg-muted hover:text-fg hover:border-line-strong"
          >
            Next →
          </button>
        </div>
        <button
          type="button"
          onClick={toggleKnown}
          className={`rounded-full px-4 py-1.5 text-sm font-medium shadow-sm transition ${
            known.has(index)
              ? "bg-success text-white hover:brightness-95"
              : "bg-brand-600 text-brand-fg hover:bg-brand-700"
          }`}
        >
          {known.has(index) ? "✓ I know this" : "Mark as known"}
        </button>
      </div>
    </div>
  );
}
