import { motion } from "framer-motion";
import clsx from "clsx";
import { Check, Compass, Flag, Footprints, Lightbulb, Sparkles, Trophy } from "lucide-react";

const STAGES = [
  { key: "start", label: "Start", icon: Flag, blurb: "Say hello to Divi" },
  { key: "discover", label: "Discover", icon: Footprints, blurb: "Explore new ideas" },
  { key: "practice", label: "Practise", icon: Sparkles, blurb: "Try questions" },
  { key: "understand", label: "Understand", icon: Lightbulb, blurb: "It clicks!" },
  { key: "master", label: "Master", icon: Trophy, blurb: "You know it well" },
  { key: "explore", label: "Explore", icon: Compass, blurb: "Go further" },
];

/** The learning journey. `current` is computed by the backend from real mastery data. */
export function JourneyPath({ current, compact = false }: { current: string; compact?: boolean }) {
  const idx = Math.max(0, STAGES.findIndex((s) => s.key === current));
  return (
    <nav aria-label="Your learning journey" className="w-full">
      <ol className={clsx("relative grid gap-3", compact ? "grid-cols-6" : "grid-cols-3 sm:grid-cols-6")}>
        <div className="absolute left-[8%] right-[8%] top-7 hidden h-1 rounded-full bg-cream-200 sm:block" aria-hidden="true">
          <motion.div
            className="h-full rounded-full bg-maroon-500"
            initial={{ width: 0 }}
            whileInView={{ width: `${(idx / (STAGES.length - 1)) * 100}%` }}
            viewport={{ once: true }}
            transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
        {STAGES.map((s, i) => {
          const done = i < idx;
          const here = i === idx;
          const Ico = done ? Check : s.icon;
          return (
            <motion.li
              key={s.key}
              className="relative z-10 flex flex-col items-center text-center"
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              aria-current={here ? "step" : undefined}
            >
              <motion.span
                className={clsx(
                  "flex h-14 w-14 items-center justify-center rounded-full border-2",
                  done && "border-maroon-600 bg-maroon-600 text-cream-50",
                  here && "border-maroon-600 bg-cream-300 text-maroon-800 shadow-glow",
                  !done && !here && "border-sand-200 bg-white text-sand-400",
                )}
                animate={here ? { scale: [1, 1.07, 1] } : undefined}
                transition={{ duration: 2.2, repeat: Infinity }}
              >
                <Ico size={22} aria-hidden />
              </motion.span>
              <span className={clsx("mt-2 text-sm font-semibold", here ? "text-maroon-700" : "text-cocoa")}>{s.label}</span>
              {!compact && <span className="text-xs text-sand-500">{here ? "You are here" : s.blurb}</span>}
              <span className="sr-only">{done ? "completed" : here ? "current stage" : "not reached yet"}</span>
            </motion.li>
          );
        })}
      </ol>
    </nav>
  );
}
