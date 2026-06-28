import { useCallback } from "react";

import Spinner from "../components/Spinner.jsx";
import useFetch from "../hooks/useFetch.js";
import { healthService } from "../services/healthService.js";

export default function HealthPage() {
  const fetcher = useCallback(() => healthService.status(), []);
  const { data, error, loading, refetch } = useFetch(fetcher, []);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">API health</h1>
        <button
          type="button"
          onClick={refetch}
          className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
        >
          Refresh
        </button>
      </div>

      {loading && <Spinner />}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to reach the API.
          <pre className="mt-2 whitespace-pre-wrap text-xs">
            {error?.message || String(error)}
          </pre>
        </div>
      )}

      {data && (
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Status" value={data.status} highlight={data.status === "ok"} />
          <Field label="Database" value={data.database} highlight={data.database === "ok"} />
          <Field label="App" value={data.app} />
          <Field label="Version" value={data.version} />
          <Field label="Environment" value={data.environment} />
        </dl>
      )}
    </section>
  );
}

function Field({ label, value, highlight }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd
        className={`mt-1 text-sm font-medium ${
          highlight ? "text-emerald-700" : "text-slate-900"
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
