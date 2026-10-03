import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { BarChart3, Compass, Home, Library, LogOut, MessageCircleHeart, Settings } from "lucide-react";
import clsx from "clsx";
import { Logo } from "../brand/Logo";
import { useAuth } from "@/lib/auth";
import { usePrefs } from "@/lib/prefs";

const NAV = [
  { to: "/app", label: "Home", icon: Home, end: true },
  { to: "/app/explore", label: "Explore", icon: Compass },
  { to: "/app/tutor", label: "Ask Divi", icon: MessageCircleHeart },
  { to: "/app/library", label: "Library", icon: Library },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const { prefs } = usePrefs();
  const location = useLocation();
  const navigate = useNavigate();

  const signOut = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-cream-50 paper-texture">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-maroon-600 focus:px-4 focus:py-2 focus:text-cream-50">
        Skip to content
      </a>
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-cream-200 bg-cream-50/95 px-4 py-6 lg:flex" aria-label="App navigation">
        <NavLink to="/app" className="px-2" aria-label="Lumora home">
          <Logo size={40} />
        </NavLink>
        <nav className="mt-10 flex-1">
          <ul className="space-y-1">
            {NAV.map(({ to, label, icon: Ico, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    clsx(
                      "flex min-h-[48px] items-center gap-3 rounded-2xl px-4 text-[0.98rem] font-medium transition-colors",
                      isActive ? "bg-maroon-600 text-cream-50 shadow-soft" : "text-cocoa hover:bg-cream-200",
                    )
                  }
                >
                  <Ico size={20} aria-hidden /> {label}
                </NavLink>
              </li>
            ))}
          </ul>
          <div className="mt-8 rounded-2xl border border-cream-300 bg-cream-100 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-maroon-500">For grown-ups</p>
            <NavLink to="/app/insights" className="mt-2 flex items-center gap-2 text-sm font-medium text-maroon-700 hover:underline">
              <BarChart3 size={16} aria-hidden /> Learning insights
            </NavLink>
          </div>
        </nav>
        <div className="flex items-center justify-between gap-2 rounded-2xl bg-white px-3 py-3 shadow-soft">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{user?.display_name}</p>
            <p className="truncate text-xs text-sand-500">{user?.email}</p>
          </div>
          <button className="btn-ghost px-2" onClick={signOut} aria-label="Sign out">
            <LogOut size={18} aria-hidden />
          </button>
        </div>
      </aside>

      {/* Mobile / tablet header */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-cream-200 bg-cream-50/90 px-4 py-3 backdrop-blur lg:hidden">
        <NavLink to="/app" aria-label="Lumora home">
          <Logo size={34} />
        </NavLink>
        <div className="flex items-center gap-1">
          <NavLink to="/app/insights" className="btn-ghost px-3 text-sm" aria-label="Learning insights for grown-ups">
            <BarChart3 size={18} aria-hidden /> <span className="hidden sm:inline">Insights</span>
          </NavLink>
          <button className="btn-ghost px-3" onClick={signOut} aria-label="Sign out">
            <LogOut size={18} aria-hidden />
          </button>
        </div>
      </header>

      <main id="main" className="pb-28 lg:ml-64 lg:pb-12">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: prefs.reduced_motion ? 0 : 0.28, ease: "easeOut" }}
            className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-10"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Mobile / tablet bottom tabs - large touch targets */}
      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-cream-200 bg-white/95 backdrop-blur lg:hidden" aria-label="App navigation">
        <ul className="mx-auto grid max-w-xl grid-cols-5">
          {NAV.map(({ to, label, icon: Ico, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  clsx("flex min-h-[64px] flex-col items-center justify-center gap-1 text-[0.72rem] font-medium", isActive ? "text-maroon-700" : "text-sand-500")
                }
              >
                {({ isActive }) => (
                  <>
                    <span className={clsx("rounded-full px-4 py-1 transition-colors", isActive && "bg-cream-200")}>
                      <Ico size={22} aria-hidden />
                    </span>
                    {label}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
