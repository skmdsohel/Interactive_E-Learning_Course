import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  setAuthToken,
  setUnauthorizedHandler,
} from "../services/apiClient.js";
import { authService } from "../services/authService.js";

const STORAGE_KEY = "learnsphere.auth";

const AuthContext = createContext(null);

function readStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.token || !parsed?.user) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeStored(value) {
  if (value) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export function AuthProvider({ children }) {
  const initial = readStored();
  const [token, setToken] = useState(initial?.token || null);
  const [user, setUser] = useState(initial?.user || null);
  const [loading, setLoading] = useState(false);
  const refreshedRef = useRef(false);

  // Keep axios in sync with the active token.
  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const logout = useCallback(() => {
    // Fire-and-forget server-side logout hook. Errors are ignored — the
    // client-side session is the source of truth today (JWTs are stateless).
    authService.logout().catch(() => {});
    setToken(null);
    setUser(null);
    writeStored(null);
  }, []);

  // Wire 401 handler once.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
    });
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  // After a fresh page load with a stored token, validate it against /auth/me.
  // If the server rejects it, the 401 handler clears auth automatically.
  useEffect(() => {
    if (!token || refreshedRef.current) return;
    refreshedRef.current = true;
    authService
      .me()
      .then((freshUser) => {
        setUser(freshUser);
        writeStored({ token, user: freshUser });
      })
      .catch(() => {
        /* handled by 401 interceptor */
      });
  }, [token]);

  const signInWithGoogle = useCallback(async (googleIdToken, role) => {
    setLoading(true);
    try {
      const res = await authService.signInWithGoogle(googleIdToken, role);
      setToken(res.access_token);
      setUser(res.user);
      writeStored({ token: res.access_token, user: res.user });
      return res.user;
    } finally {
      setLoading(false);
    }
  }, []);

  const signInWithEmail = useCallback(async ({ email, password }) => {
    setLoading(true);
    try {
      const res = await authService.login({ email, password });
      setToken(res.access_token);
      setUser(res.user);
      writeStored({ token: res.access_token, user: res.user });
      return res.user;
    } finally {
      setLoading(false);
    }
  }, []);

  const registerWithEmail = useCallback(async (payload) => {
    setLoading(true);
    try {
      const res = await authService.register(payload);
      setToken(res.access_token);
      setUser(res.user);
      writeStored({ token: res.access_token, user: res.user });
      return res.user;
    } finally {
      setLoading(false);
    }
  }, []);

  const changePassword = useCallback(
    async ({ currentPassword, newPassword }) => {
      await authService.changePassword({ currentPassword, newPassword });
    },
    []
  );

  const chooseRole = useCallback(
    async (role) => {
      const updated = await authService.chooseRole(role);
      setUser(updated);
      if (token) writeStored({ token, user: updated });
      return updated;
    },
    [token]
  );

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      isAdmin: user?.role === "admin",
      isInstructor: user?.role === "instructor",
      canManageCourses: user?.role === "admin" || user?.role === "instructor",
      needsRoleSelection: Boolean(token && user && user.role === "pending"),
      hasLocalPassword: Boolean(user?.has_local_password),
      loading,
      signInWithGoogle,
      signInWithEmail,
      registerWithEmail,
      changePassword,
      chooseRole,
      logout,
    }),
    [
      token,
      user,
      loading,
      signInWithGoogle,
      signInWithEmail,
      registerWithEmail,
      changePassword,
      chooseRole,
      logout,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
