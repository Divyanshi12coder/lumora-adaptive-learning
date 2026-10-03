import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useSpring } from "framer-motion";
import { Menu, X } from "lucide-react";
import clsx from "clsx";
import { Logo } from "../brand/Logo";
import { useAuth } from "@/lib/auth";

const LINKS = [
  { id: "how", label: "How it works" },
  { id: "adapt", label: "See it adapt" },
  { id: "tutor-demo", label: "Meet Divi" },
  { id: "features", label: "Features" },
  { id: "technology", label: "Technology" },
];

export function PublicNav() {
  const { user } = useAuth();
  const [active, setActive] = useState<string>("");
  const [open, setOpen] = useState(false);
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 30, restDelta: 0.001 });

  useEffect(() => {
    const els = LINKS.map((l) => document.getElementById(l.id)).filter(Boolean) as HTMLElement[];
    if (!els.length || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive(visible.target.id);
      },
      { rootMargin: "-40% 0px -50% 0px", threshold: [0, 0.25, 0.5] },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-cream-200/80 bg-cream-50/85 backdrop-blur-md">
      <motion.div className="absolute inset-x-0 top-0 h-[3px] origin-left bg-maroon-500" style={{ scaleX: progress }} aria-hidden="true" />
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6" aria-label="Main">
        <Link to="/" aria-label="Lumora home">
          <Logo size={38} />
        </Link>
        <ul className="hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => (
            <li key={l.id}>
              <a
                href={`#${l.id}`}
                className={clsx(
                  "relative rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                  active === l.id ? "text-maroon-700" : "text-cocoa-soft hover:text-maroon-700",
                )}
                aria-current={active === l.id ? "true" : undefined}
              >
                {active === l.id && (
                  <motion.span layoutId="nav-pill" className="absolute inset-0 -z-10 rounded-full bg-cream-200" transition={{ type: "spring", stiffness: 380, damping: 32 }} />
                )}
                {l.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="hidden items-center gap-2 sm:flex">
          {user ? (
            <Link to="/app" className="btn-primary">
              Go to my dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">
                Sign in
              </Link>
              <Link to="/signup" className="btn-primary">
                Start learning
              </Link>
            </>
          )}
        </div>
        <button className="btn-ghost px-3 sm:hidden" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="mobile-menu" aria-label={open ? "Close menu" : "Open menu"}>
          {open ? <X aria-hidden /> : <Menu aria-hidden />}
        </button>
      </nav>
      {open && (
        <div id="mobile-menu" className="border-t border-cream-200 bg-cream-50 px-4 pb-4 sm:hidden">
          <ul className="flex flex-col py-2">
            {LINKS.map((l) => (
              <li key={l.id}>
                <a href={`#${l.id}`} onClick={() => setOpen(false)} className="block rounded-xl px-3 py-3 font-medium text-cocoa hover:bg-cream-200">
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            {user ? (
              <Link to="/app" className="btn-primary flex-1">My dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="btn-secondary flex-1">Sign in</Link>
                <Link to="/signup" className="btn-primary flex-1">Start learning</Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
