import Navbar from "./Navbar.jsx";

export default function Layout({ children }) {
  return (
    <div className="min-h-full flex flex-col bg-bg text-fg">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">{children}</div>
      </main>
      <footer className="border-t border-line bg-surface/60 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-5 text-xs text-fg-subtle sm:px-6">
          LMS · Built for focused learning
        </div>
      </footer>
    </div>
  );
}
