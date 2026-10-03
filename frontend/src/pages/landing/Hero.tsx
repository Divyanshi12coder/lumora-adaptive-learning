import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Lightbulb, PlayCircle, Sparkles } from "lucide-react";
import { DiviAvatar, type DiviMood } from "@/components/brand/DiviAvatar";
import { Blob, FloatingShapes, Sparkle } from "@/components/illustrations/Decor";

const SCENES: { mood: DiviMood; state: string; chips: string[]; line: string; tone: string }[] = [
  {
    mood: "encouraging",
    state: "Finding it tricky",
    chips: ["Step-by-step", "3 examples", "Full hints", "Easy start"],
    line: "Let's take this one small step at a time.",
    tone: "bg-maroon-50 text-maroon-700",
  },
  {
    mood: "happy",
    state: "Getting the hang of it",
    chips: ["Worked example", "2 examples", "Guided hints", "Medium"],
    line: "You're building great understanding!",
    tone: "bg-cream-200 text-maroon-800",
  },
  {
    mood: "celebrating",
    state: "Mastering it",
    chips: ["Short & sharp", "Challenge mode", "No hints", "Hard"],
    line: "Wow - ready for a bigger challenge?",
    tone: "bg-maroon-600 text-cream-50",
  },
];

function HeroScene() {
  const [i, setI] = useState(0);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce) return;
    const t = setInterval(() => setI((x) => (x + 1) % SCENES.length), 3200);
    return () => clearInterval(t);
  }, [reduce]);
  const scene = SCENES[i];
  return (
    <div className="relative mx-auto aspect-[5/4] w-full max-w-[520px]" aria-label="Animated example of Divi adapting a lesson" role="img">
      <Blob className="absolute inset-0 h-full w-full" color="#FFF2CC" />
      <Blob className="absolute -right-6 bottom-0 h-2/3 w-2/3 opacity-70" color="#F4DCE0" />
      <Sparkle className="absolute left-[12%] top-[10%] w-8 animate-float" />
      <Sparkle className="absolute bottom-[16%] right-[8%] w-6 animate-float-slow" color="#AE4F5E" />

      {/* Lesson card */}
      <motion.div
        className="absolute left-[8%] top-[14%] w-[64%] rounded-3xl border border-cream-300 bg-white p-5 shadow-lift"
        animate={reduce ? undefined : { y: [0, -6, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-sand-500">
          <Lightbulb size={14} className="text-maroon-500" aria-hidden /> Fractions
        </div>
        <p className="mt-2 font-display text-lg font-semibold text-maroon-800">Which is bigger: 1/3 or 1/5?</p>
        <AnimatePresence mode="wait">
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35 }}
          >
            <span className={`mt-3 inline-block rounded-full px-3 py-1 text-xs font-semibold ${scene.tone}`}>{scene.state}</span>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {scene.chips.map((c) => (
                <span key={c} className="rounded-full border border-sand-200 bg-cream-50 px-2.5 py-1 text-[0.72rem] font-medium text-cocoa">
                  {c}
                </span>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* Divi + speech */}
      <div className="absolute bottom-[8%] right-[6%] flex w-[62%] items-end gap-2">
        <AnimatePresence mode="wait">
          <motion.div
            key={`b${i}`}
            className="mb-10 flex-1 rounded-2xl rounded-br-sm bg-maroon-700 px-4 py-3 text-sm text-cream-50 shadow-lift"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
          >
            {scene.line}
          </motion.div>
        </AnimatePresence>
        <DiviAvatar size={96} mood={scene.mood} />
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <FloatingShapes />
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-12 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:pb-28 lg:pt-20">
        <div>
          <motion.p
            className="chip mb-5 bg-cream-200 text-maroon-700"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Sparkles size={14} aria-hidden /> Adaptive AI tutor for young learners
          </motion.p>
          <motion.h1
            className="h-display text-[2.6rem] leading-[1.06] sm:text-6xl"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05, duration: 0.6 }}
          >
            Learning that <span className="relative whitespace-nowrap text-maroon-600">
              listens
              <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 200 12" aria-hidden="true">
                <path d="M3 9C50 3 150 3 197 8" stroke="#F8D570" strokeWidth="6" fill="none" strokeLinecap="round" />
              </svg>
            </span>
            <br /> to every child.
          </motion.h1>
          <motion.p
            className="mt-6 max-w-xl text-lg text-cocoa-soft"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.6 }}
          >
            Lumora notices how a child is learning - which questions feel tricky, when hints help, when it's time for a challenge - and
            gently changes <strong className="font-semibold text-maroon-700">how it teaches</strong>: shorter steps, more examples,
            read-aloud, or a bigger challenge.
          </motion.p>
          <motion.div
            className="mt-8 flex flex-wrap gap-3"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.6 }}
          >
            <Link to="/signup" className="btn-primary group px-6 py-3 text-base">
              Start learning free <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" aria-hidden />
            </Link>
            <a href="#tutor-demo" className="btn-secondary px-6 py-3 text-base">
              <PlayCircle size={18} aria-hidden /> Watch the tutor adapt
            </a>
          </motion.div>
          <p className="mt-5 text-sm text-sand-500">
            Built for different learning preferences, including learners with ADHD or dyslexia. Not a diagnostic tool.
          </p>
        </div>
        <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2, duration: 0.7 }}>
          <HeroScene />
        </motion.div>
      </div>
    </section>
  );
}
