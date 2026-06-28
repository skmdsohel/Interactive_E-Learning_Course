import { useCallback, useEffect, useState } from "react";

import Spinner from "../components/Spinner.jsx";
import { adminService } from "../services/adminService.js";

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, u] = await Promise.all([
        adminService.getStats(),
        adminService.listUsers(),
      ]);
      setStats(s);
      setUsers(u);
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Failed to load admin data."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSync = async (prune) => {
    setSyncing(true);
    try {
      const res = await adminService.triggerSync({ prune });
      setLastSync(res);
      await refresh();
    } catch (e) {
      setError(
        e?.response?.data?.error?.message ||
          e?.response?.data?.detail ||
          e?.message ||
          "Sync failed."
      );
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="py-12">
        <Spinner label="Loading admin…" />
      </div>
    );
  }

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Admin</h1>
        <p className="mt-1 text-sm text-slate-600">
          Catalog stats, content sync, and user list.
        </p>
      </header>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <StatCard label="Users" value={stats.users} />
          <StatCard label="Courses" value={stats.courses} />
          <StatCard label="Sections" value={stats.sections} />
          <StatCard label="Videos" value={stats.videos} />
          <StatCard label="Progress rows" value={stats.progress_rows} />
        </div>
      )}

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-900">Content sync</h2>
        <p className="mt-1 text-xs text-slate-600">
          Re-scans <code>storage/videos/</code> and upserts the catalog. Stable
          IDs are preserved.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleSync(false)}
            disabled={syncing}
            className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync now"}
          </button>
          <button
            type="button"
            onClick={() => handleSync(true)}
            disabled={syncing}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Sync &amp; prune missing
          </button>
        </div>
        {lastSync && (
          <pre className="mt-3 overflow-x-auto rounded bg-slate-900 p-3 text-[11px] text-slate-100">
            {JSON.stringify(lastSync, null, 2)}
          </pre>
        )}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <header className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-900">
            Users ({users.length})
          </h2>
        </header>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-600">
              <tr>
                <th className="px-4 py-2">ID</th>
                <th className="px-4 py-2">User</th>
                <th className="px-4 py-2">Email</th>
                <th className="px-4 py-2">Role</th>
                <th className="px-4 py-2">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-2 text-slate-500">{u.id}</td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      {u.picture_url ? (
                        <img
                          src={u.picture_url}
                          alt=""
                          referrerPolicy="no-referrer"
                          className="h-6 w-6 rounded-full"
                        />
                      ) : (
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-slate-300 text-[11px] font-semibold text-white">
                          {(u.name || u.email || "?")[0].toUpperCase()}
                        </span>
                      )}
                      <span className="text-slate-900">{u.name || "—"}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-slate-700">{u.email}</td>
                  <td className="px-4 py-2">
                    <RoleBadge role={u.role} />
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500">
                    {new Date(u.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    No users yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function RoleBadge({ role }) {
  const isAdmin = role === "admin";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        isAdmin
          ? "bg-purple-100 text-purple-700"
          : "bg-slate-100 text-slate-600"
      }`}
    >
      {role}
    </span>
  );
}
