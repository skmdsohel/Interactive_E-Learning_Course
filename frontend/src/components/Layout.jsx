import Navbar from "./Navbar.jsx";

const currentYear = new Date().getFullYear();

export default function Layout({ children }) {
  return (
    <div className="min-h-full flex flex-col bg-bg text-fg">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">{children}</div>
      </main>
      <footer className="border-t border-line bg-surface/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-6 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2 text-sm text-fg-muted">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-brand-500 to-brand-700 text-brand-fg">
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Z" />
                <path d="M5 17h11" />
              </svg>
            </span>
            <span className="font-semibold text-fg">LearnSphere</span>
            <span className="text-fg-subtle">· Built for focused learning</span>
          </div>
          <p className="text-xs text-fg-subtle">
            © {currentYear} LearnSphere. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
