import { NavLink } from "react-router-dom";

const linkBase =
  "px-3 py-2 rounded-md text-sm font-medium transition-colors";
const linkInactive = "text-slate-600 hover:text-slate-900 hover:bg-slate-100";
const linkActive = "bg-brand-50 text-brand-700";

export default function Navbar() {
  return (
    <header className="bg-white border-b border-slate-200">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2">
          <span className="inline-block h-6 w-6 rounded bg-brand-600" />
          <span className="font-semibold text-slate-900">LMS</span>
        </NavLink>
        <nav className="flex items-center gap-1">
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
            to="/health"
            className={({ isActive }) =>
              `${linkBase} ${isActive ? linkActive : linkInactive}`
            }
          >
            Health
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
