import { useEffect, useId, useState, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import clsx from "clsx";
import { RefreshCw, Volume2, VolumeX } from "lucide-react";
import { DiviAvatar } from "../brand/DiviAvatar";
import { track } from "@/lib/tracker";

/* ---------------------------------------------------------------- Reveal */
export function Reveal({ children, delay = 0, className, y = 24 }: { children: ReactNode; delay?: number; className?: string; y?: number }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export const stagger = {
  container: { hidden: {}, show: { transition: { staggerChildren: 0.08 } } },
  item: { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] } } },
};

/* ---------------------------------------------------------- ProgressRing */
export function ProgressRing({
  value,
  size = 96,
  stroke = 10,
  label,
  sublabel,
  tone = "maroon",
}: {
  value: number; // 0..1
  size?: number;
  stroke?: number;
  label?: ReactNode;
  sublabel?: string;
  tone?: "maroon" | "sunny";
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value || 0));
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={tone === "maroon" ? "#F4DCE0" : "#FFF2CC"} strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={tone === "maroon" ? "#772233" : "#E9B949"}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - pct) }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="font-display text-lg font-semibold text-maroon-800">{label ?? `${Math.round(pct * 100)}%`}</span>
        {sublabel && <span className="text-[0.7rem] text-sand-500">{sublabel}</span>}
      </div>
      <span className="sr-only">{`${Math.round(pct * 100)} percent${sublabel ? ` ${sublabel}` : ""}`}</span>
    </div>
  );
}

/* --------------------------------------------------------------- Bar */
export function ProgressBar({ value, label, className }: { value: number; label: string; className?: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className={className}>
      <div
        className="h-3 w-full overflow-hidden rounded-full bg-cream-200"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-maroon-500 to-maroon-600"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
    </div>
  );
}

/* ----------------------------------------------------------- Skeletons */
export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton", className)} aria-hidden="true" />;
}

export function PageSkeleton({ label = "Loading" }: { label?: string }) {
  return (
    <div className="space-y-5" role="status" aria-live="polite">
      <span className="sr-only">{label}…</span>
      <Skeleton className="h-28 w-full" />
      <div className="grid gap-5 md:grid-cols-3">
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

/* --------------------------------------------------- Empty / error states */
export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return (
    <div className="card-sunny flex flex-col items-center gap-3 px-6 py-10 text-center">
      <DiviAvatar size={72} mood="encouraging" />
      <h3 className="h-display text-xl">{title}</h3>
      <p className="max-w-md text-cocoa-soft">{message}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 rounded-xl2 border border-maroon-100 bg-maroon-50/60 px-6 py-10 text-center">
      <DiviAvatar size={64} mood="thinking" />
      <h3 className="h-display text-xl">Hmm, that didn't load.</h3>
      <p className="max-w-md text-cocoa-soft">{message ?? "Something went a little wobbly. Let's try again!"}</p>
      {onRetry && (
        <button className="btn-secondary" onClick={onRetry}>
          <RefreshCw size={18} aria-hidden /> Try again
        </button>
      )}
    </div>
  );
}

/* ---------------------------------------------------------- Celebration */
export function Celebration({ show }: { show: boolean }) {
  const reduce = useReducedMotion();
  const pieces = Array.from({ length: 18 }, (_, i) => i);
  if (reduce) return null;
  return (
    <AnimatePresence>
      {show && (
        <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden" aria-hidden="true">
          {pieces.map((i) => {
            const left = 10 + ((i * 47) % 80);
            const color = ["#F8D570", "#772233", "#AE4F5E", "#E9B949"][i % 4];
            return (
              <motion.svg
                key={i}
                width="22"
                height="22"
                viewBox="0 0 24 24"
                className="absolute"
                style={{ left: `${left}%`, top: "-30px" }}
                initial={{ y: 0, opacity: 1, rotate: 0 }}
                animate={{ y: "105vh", opacity: [1, 1, 0], rotate: 240 + i * 20 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 2.4 + (i % 5) * 0.25, delay: (i % 6) * 0.08, ease: "easeIn" }}
              >
                <path d="M12 2l2.9 6.9L22 9.3l-5.4 4.8L18.2 21 12 17.3 5.8 21l1.6-6.9L2 9.3l7.1-.4z" fill={color} />
              </motion.svg>
            );
          })}
        </div>
      )}
    </AnimatePresence>
  );
}

/* --------------------------------------------------------------- Toggle */
export function Toggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  description?: string;
}) {
  const id = useId();
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div>
        <label htmlFor={id} className="font-medium text-cocoa">
          {label}
        </label>
        {description && <p className="text-sm text-sand-500">{description}</p>}
      </div>
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={clsx(
          "relative h-8 w-14 shrink-0 rounded-full transition-colors",
          checked ? "bg-maroon-600" : "bg-sand-200",
        )}
      >
        <span
          className={clsx(
            "absolute top-1 h-6 w-6 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-7" : "translate-x-1",
          )}
        />
        <span className="sr-only">{checked ? "On" : "Off"}</span>
      </button>
    </div>
  );
}

/* ------------------------------------------------------------ ReadAloud */
export function ReadAloud({ text, topicId, lessonId, className }: { text: string; topicId?: number; lessonId?: number; className?: string }) {
  const [speaking, setSpeaking] = useState(false);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;
  useEffect(() => () => { if (supported) window.speechSynthesis.cancel(); }, [supported]);
  if (!supported) return null;
  const toggle = () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.92;
    u.onend = () => setSpeaking(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    setSpeaking(true);
    track({ event_type: "read_aloud_used", topic_id: topicId, lesson_id: lessonId });
  };
  return (
    <button type="button" onClick={toggle} className={clsx("btn-ghost min-h-[40px] px-3 py-1.5 text-sm", className)} aria-pressed={speaking}>
      {speaking ? <VolumeX size={18} aria-hidden /> : <Volume2 size={18} aria-hidden />}
      {speaking ? "Stop reading" : "Read aloud"}
    </button>
  );
}

/* --------------------------------------------------------- SectionTitle */
export function SectionTitle({ eyebrow, title, intro, center = false }: { eyebrow?: string; title: ReactNode; intro?: ReactNode; center?: boolean }) {
  return (
    <div className={clsx("mb-10 max-w-2xl", center && "mx-auto text-center")}>
      {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
      <h2 className="h-display text-3xl sm:text-4xl">{title}</h2>
      {intro && <p className="mt-4 text-lg text-cocoa-soft">{intro}</p>}
    </div>
  );
}

export function Pill({ children, tone = "cream" }: { children: ReactNode; tone?: "cream" | "maroon" | "sand" }) {
  return (
    <span
      className={clsx(
        "chip",
        tone === "cream" && "bg-cream-200 text-maroon-800",
        tone === "maroon" && "bg-maroon-600 text-cream-50",
        tone === "sand" && "bg-sand-100 text-sand-600",
      )}
    >
      {children}
    </span>
  );
}
