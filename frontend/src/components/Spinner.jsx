export default function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-sm">
      <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      <span>{label}</span>
    </div>
  );
}
