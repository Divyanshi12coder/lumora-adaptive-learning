import { motion, useReducedMotion } from "framer-motion";
import clsx from "clsx";

/** Gently floating learning objects (star, pencil, bulb, book). Decorative only. */
export function FloatingShapes({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  const float = (d: number) =>
    reduce ? {} : { animate: { y: [0, -12, 0] }, transition: { duration: 6 + d, repeat: Infinity, ease: "easeInOut" as const } };
  return (
    <div className={clsx("pointer-events-none absolute inset-0", className)} aria-hidden="true" data-decorative="true">
      <motion.svg {...float(0)} className="absolute left-[6%] top-[18%] w-10" viewBox="0 0 24 24">
        <path d="M12 2l2.9 6.9L22 9.3l-5.4 4.8L18.2 21 12 17.3 5.8 21l1.6-6.9L2 9.3l7.1-.4z" fill="#F8D570" />
      </motion.svg>
      <motion.svg {...float(1.5)} className="absolute right-[8%] top-[12%] w-12" viewBox="0 0 48 48">
        <circle cx="24" cy="20" r="12" fill="#FFF2CC" stroke="#E9B949" strokeWidth="2" />
        <rect x="18" y="31" width="12" height="7" rx="2" fill="#AE4F5E" />
        <path d="M24 13v6l4 3" stroke="#772233" strokeWidth="2" strokeLinecap="round" fill="none" />
      </motion.svg>
      <motion.svg {...float(2.5)} className="absolute bottom-[14%] left-[10%] w-14" viewBox="0 0 64 24">
        <rect x="6" y="6" width="44" height="12" rx="3" fill="#F8D570" />
        <path d="M50 6l10 6-10 6Z" fill="#E6B5BC" />
        <rect x="2" y="6" width="8" height="12" rx="2" fill="#AE4F5E" />
      </motion.svg>
      <motion.svg {...float(1)} className="absolute bottom-[20%] right-[6%] w-12" viewBox="0 0 48 40">
        <path d="M23 36C17 32 9 31 3 32V8c6-1 14 0 20 4Z" fill="#772233" />
        <path d="M25 36c6-4 14-5 20-4V8c-6-1-14 0-20 4Z" fill="#8E2F3F" />
      </motion.svg>
    </div>
  );
}

export function Sparkle({ className, color = "#E9B949" }: { className?: string; color?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M12 1l2.2 8.8L23 12l-8.8 2.2L12 23l-2.2-8.8L1 12l8.8-2.2Z" fill={color} />
    </svg>
  );
}

/** Soft organic background blob. */
export function Blob({ className, color = "#FFF2CC" }: { className?: string; color?: string }) {
  return (
    <svg viewBox="0 0 400 400" className={className} aria-hidden="true">
      <path
        d="M318 79c37 37 59 94 46 143s-60 90-114 112-115 26-157-6S30 233 36 177s38-104 86-129 159-6 196 31Z"
        fill={color}
      />
    </svg>
  );
}

/** Medal used for achievements; colour never the only signal (earned shows a check + label). */
export function Medal({ earned, children }: { earned: boolean; children: React.ReactNode }) {
  return (
    <div className="relative h-16 w-16 shrink-0">
      <svg viewBox="0 0 64 64" className="absolute inset-0" aria-hidden="true">
        <path d="M20 4h10l4 14H24Z" fill={earned ? "#AE4F5E" : "#E5DCCF"} />
        <path d="M44 4H34l-4 14h10Z" fill={earned ? "#772233" : "#CDC0AF"} />
        <circle cx="32" cy="38" r="22" fill={earned ? "#F8D570" : "#F2ECE3"} stroke={earned ? "#E9B949" : "#E5DCCF"} strokeWidth="3" />
        <circle cx="32" cy="38" r="16" fill={earned ? "#FFF2CC" : "#FAF7F2"} />
      </svg>
      <div className={clsx("absolute inset-x-0 top-[22px] flex justify-center", earned ? "text-maroon-700" : "text-sand-400")}>{children}</div>
    </div>
  );
}
