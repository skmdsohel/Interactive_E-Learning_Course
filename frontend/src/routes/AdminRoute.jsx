import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

/**
 * Gate a route behind the admin role. Non-admins get a 403-style page.
 * Anonymous users are bounced to /login first.
 */
export default function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!isAdmin) {
    return (
      <section className="mx-auto max-w-md py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <h1 className="text-lg font-semibold text-red-800">Admins only</h1>
          <p className="mt-2 text-sm text-red-700">
            This page requires the admin role on your account.
          </p>
        </div>
      </section>
    );
  }

  return children;
}
