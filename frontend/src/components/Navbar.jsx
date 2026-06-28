import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

const linkBase =
  "px-3 py-2 rounded-md text-sm font-medium transition-colors";
const linkInactive = "text-slate-600 hover:text-slate-900 hover:bg-slate-100";
const linkActive = "bg-brand-50 text-brand-700";

export default function Navbar() {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <header className="bg-white border-b border-slate-200">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between gap-4">
        <NavLink to="/" className="flex items-center gap-2 shrink-0">
          <span className="inline-block h-6 w-6 rounded bg-brand-600" />
          <span className="font-semibold text-slate-900">LMS</span>
        </NavLink>

        <nav className="flex flex-1 items-center gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `${linkBase} ${isActive ? linkActive : linkInactive}`
            }
          >
            Home
          </NavLink>
          <NavLink
            to="/courses"
            className={({ isActive }) =>
              `${linkBase} ${isActive ? linkActive : linkInactive}`
            }
          >
            Courses
          </NavLink>
          {isAdmin && (
            <>
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `${linkBase} ${isActive ? linkActive : linkInactive}`
                }
              >
                Admin
              </NavLink>
              <NavLink
                to="/health"
                className={({ isActive }) =>
                  `${linkBase} ${isActive ? linkActive : linkInactive}`
                }
              >
                Health
              </NavLink>
            </>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 rounded-md border border-slate-200 bg-white px-2 py-1">
                {user?.picture_url ? (
                  <img
                    src={user.picture_url}
                    alt=""
                    referrerPolicy="no-referrer"
                    className="h-6 w-6 rounded-full"
                  />
                ) : (
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-[11px] font-semibold text-white">
                    {(user?.name || user?.email || "?")[0].toUpperCase()}
                  </span>
                )}
                <span className="max-w-[140px] truncate text-sm text-slate-700">
                  {user?.name || user?.email}
                </span>
                {isAdmin && (
                  <span className="rounded-full bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-purple-700">
                    admin
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Sign out
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Sign in
            </NavLink>
          )}
        </div>
      </div>
    </header>
  );
}
