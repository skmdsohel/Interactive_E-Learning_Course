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
        <h1 className="text-3xl font-bold tracking-tight text-fg">Admin</h1>
        <p className="mt-1 text-sm text-fg-subtle">
          Catalog stats, content sync, and user list.
        </p>
      </header>

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-3 text-sm text-danger-soft-fg">
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

      <div className="rounded-2xl border border-line bg-surface p-5 shadow-[var(--shadow-card)]">
        <h2 className="text-sm font-semibold text-fg">Content sync</h2>
        <p className="mt-1 text-xs text-fg-subtle">
          Re-scans <code className="rounded bg-muted px-1 py-0.5 text-fg-muted">storage/videos/</code> and upserts the catalog. Stable IDs are preserved.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleSync(false)}
            disabled={syncing}
            className="rounded-full bg-brand-600 px-4 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition hover:bg-brand-700 disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync now"}
          </button>
          <button
            type="button"
            onClick={() => handleSync(true)}
            disabled={syncing}
            className="rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-medium text-fg-muted transition hover:text-fg hover:border-line-strong disabled:opacity-50"
          >
            Sync &amp; prune missing
          </button>
        </div>
        {lastSync && (
          <pre className="mt-3 overflow-x-auto rounded-xl bg-elevated p-3 text-[11px] text-fg-muted ring-1 ring-line">
            {JSON.stringify(lastSync, null, 2)}
          </pre>
        )}
      </div>

      <div className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
        <header className="border-b border-line px-5 py-4">
          <h2 className="text-sm font-semibold text-fg">
            Users <span className="text-fg-subtle">({users.length})</span>
          </h2>
        </header>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-muted/60 text-left text-xs uppercase tracking-wide text-fg-muted">
              <tr>
                <th className="px-5 py-2.5">ID</th>
                <th className="px-5 py-2.5">User</th>
                <th className="px-5 py-2.5">Email</th>
                <th className="px-5 py-2.5">Role</th>
                <th className="px-5 py-2.5">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-muted/40">
                  <td className="px-5 py-3 text-fg-subtle">{u.id}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      {u.picture_url ? (
                        <img
                          src={u.picture_url}
                          alt=""
                          referrerPolicy="no-referrer"
                          className="h-6 w-6 rounded-full"
                        />
                      ) : (
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-muted text-[11px] font-semibold text-fg-muted">
                          {(u.name || u.email || "?")[0].toUpperCase()}
                        </span>
                      )}
                      <span className="text-fg">{u.name || "—"}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-fg-muted">{u.email}</td>
                  <td className="px-5 py-3">
                    <RoleBadge role={u.role} />
                  </td>
                  <td className="px-5 py-3 text-xs text-fg-subtle">
                    {new Date(u.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-fg-subtle">
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
    <div className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]">
      <p className="text-xs uppercase tracking-wide text-fg-subtle">{label}</p>
      <p className="mt-1.5 text-2xl font-bold text-fg">{value}</p>
    </div>
  );
}

function RoleBadge({ role }) {
  const isAdmin = role === "admin";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        isAdmin
          ? "bg-accent-soft text-accent-soft-fg"
          : "bg-muted text-fg-muted"
      }`}
    >
      {role}
    </span>
  );
}
