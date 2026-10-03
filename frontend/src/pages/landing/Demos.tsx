import { useEffect, useId, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useMutation, useQuery } from "@tanstack/react-query";
import { BookOpen, Eye, HelpCircle, Layers, Lightbulb, ListOrdered, RefreshCcw, Server, Shuffle, ThumbsUp, Timer } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import type { TeachingStrategy, TutorPayload } from "@/lib/types";
import { BAND_LABEL, DIFF_LABEL, HINT_LABEL, LEVEL_LABEL, STYLE_HELP, STYLE_LABEL } from "@/lib/format";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { ErrorState, Reveal, SectionTitle, Skeleton } from "@/components/ui";

function useDebounced<T>(value: T, ms = 220) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

function StrategyTile({ icon: Ico, label, value, hint }: { icon: typeof Eye; label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-2xl border border-sand-200 bg-white p-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-sand-500">
        <Ico size={14} className="text-maroon-500" aria-hidden /> {label}
      </div>
      <AnimatePresence mode="wait">
        <motion.p
          key={value}
          className="mt-1.5 font-display text-lg font-semibold text-maroon-800"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.2 }}
        >
          {value}
        </motion.p>
      </AnimatePresence>
      {hint && <p className="text-xs text-sand-500">{hint}</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ slider */
export function AdaptSlider() {
  const [level, setLevel] = useState(25);
  const debounced = useDebounced(level);
  const id = useId();
  const q = useQuery({
    queryKey: ["preview", debounced],
    queryFn: () => api<{ strategy: TeachingStrategy }>("/api/adaptive/preview", { method: "POST", json: { level: debounced } }),
    placeholderData: (prev) => prev,
    staleTime: Infinity,
  });
  const s = q.data?.strategy;
  const mood = level < 34 ? "Finding it tricky" : level < 70 ? "Improving" : "Mastering it";

  return (
    <section id="adapt" className="scroll-mt-20 bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle
            eyebrow="Interactive demo"
            title="See how learning adapts"
            intro="Move the slider to change how a learner is doing. Every value is computed live by Lumora's real adaptive engine on the server - the same code that teaches signed-in learners."
          />
        </Reveal>
        <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr]">
          <Reveal className="card-sunny p-6 sm:p-8">
            <label htmlFor={id} className="font-semibold text-maroon-800">
              How is the learner doing?
            </label>
            <p className="mt-1 text-sm text-cocoa-soft">Simulates accuracy, hint use, pace and mastery signals.</p>
            <input
              id={id}
              type="range"
              min={0}
              max={100}
              value={level}
              onChange={(e) => setLevel(Number(e.target.value))}
              className="mt-6 h-3 w-full cursor-pointer accent-maroon-600"
              aria-valuetext={`${mood}, level ${level} of 100`}
            />
            <div className="mt-2 flex justify-between text-xs font-medium text-sand-500">
              <span>Struggling</span>
              <span>Improving</span>
              <span>Mastered</span>
            </div>
            <div className="mt-8 flex items-center gap-4">
              <DiviAvatar size={72} mood={level < 34 ? "encouraging" : level < 70 ? "happy" : "celebrating"} />
              <div>
                <p className="text-sm font-semibold text-maroon-600">{mood}</p>
                <AnimatePresence mode="wait">
                  <motion.p key={s?.learner_message} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-cocoa">
                    {s?.learner_message ?? "…"}
                  </motion.p>
                </AnimatePresence>
              </div>
            </div>
            {s && (
              <div className="mt-6">
                <div className="flex justify-between text-xs font-medium text-sand-500">
                  <span>Support level</span>
                  <span>{BAND_LABEL[s.band]}</span>
                </div>
                <div className="mt-1.5 h-3 overflow-hidden rounded-full bg-white" aria-hidden="true">
                  <motion.div className="h-full rounded-full bg-maroon-500" animate={{ width: `${s.support_score * 100}%` }} transition={{ type: "spring", stiffness: 120, damping: 20 }} />
                </div>
              </div>
            )}
          </Reveal>
          <div aria-live="polite">
            {q.isError && !s ? (
              <ErrorState message="The live engine isn't reachable right now. Start the API (see README) to see it adapt." onRetry={() => q.refetch()} />
            ) : !s ? (
              <div className="grid grid-cols-2 gap-3">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-24" />)}</div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <StrategyTile icon={Layers} label="Difficulty" value={DIFF_LABEL[s.difficulty]} />
                  <StrategyTile icon={ListOrdered} label="Explanation" value={STYLE_LABEL[s.explanation_style]} hint={STYLE_HELP[s.explanation_style]} />
                  <StrategyTile icon={BookOpen} label="Examples" value={`${s.example_count} example${s.example_count === 1 ? "" : "s"}`} />
                  <StrategyTile icon={HelpCircle} label="Hints" value={HINT_LABEL[s.hint_level]} />
                  <StrategyTile icon={Eye} label="Visual support" value={LEVEL_LABEL[s.visual_support]} />
                  <StrategyTile icon={Timer} label="Pacing" value={s.pacing[0].toUpperCase() + s.pacing.slice(1)} hint={`${s.question_count} questions · ${s.option_count} choices`} />
                </div>
                <div className="mt-4 rounded-2xl border border-sand-200 bg-sand-50 p-4">
                  <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-sand-500">
                    <Server size={14} aria-hidden /> Why the engine chose this
                  </p>
                  <ul className="mt-2 space-y-1 text-sm text-cocoa">
                    {s.rationale.slice(0, 3).map((r, i) => (
                      <li key={i}>• {r}</li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------- tutor demo */
interface DemoResponse {
  level: number;
  explanation: string;
  question: string;
  strategy: TeachingStrategy;
  reply: TutorPayload;
  sources: { title: string; section: string | null }[];
}

const ACTIONS = [
  { key: "understand", label: "I understand", icon: ThumbsUp },
  { key: "confused", label: "I'm confused", icon: HelpCircle },
  { key: "hint", label: "I need a hint", icon: Lightbulb },
  { key: "different", label: "Explain differently", icon: Shuffle },
] as const;

export function TutorDemo() {
  const [state, setState] = useState<DemoResponse | null>(null);
  const [last, setLast] = useState<string | null>(null);
  const m = useMutation({
    mutationFn: (action: string) =>
      api<DemoResponse>("/api/demo/tutor", {
        method: "POST",
        json: { action, level: state?.level ?? 45, last_style: state?.strategy.explanation_style ?? null },
      }),
    onSuccess: (d, action) => {
      setState(d);
      setLast(action);
    },
  });
  const reply = state?.reply;
  return (
    <section id="tutor-demo" className="scroll-mt-20 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle
            eyebrow="Watch the tutor adapt"
            title={<>Meet Divi, your patient AI guide</>}
            intro="Pick how you feel about the question. Divi's teaching strategy changes - and so does the explanation. (This public demo runs on Lumora's offline demo AI, grounded in the real lesson material.)"
          />
        </Reveal>
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <Reveal className="card p-6 sm:p-8">
            <p className="eyebrow">Fractions · Challenge question</p>
            <p className="mt-3 font-display text-2xl font-semibold text-maroon-800">Can you solve this?</p>
            <p className="mt-2 text-xl text-cocoa">Which is bigger: 1/3 or 1/5?</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {ACTIONS.map(({ key, label, icon: Ico }) => (
                <button
                  key={key}
                  onClick={() => m.mutate(key)}
                  disabled={m.isPending}
                  className={clsx(
                    "btn min-h-[56px] rounded-2xl border text-left",
                    last === key ? "border-maroon-600 bg-maroon-600 text-cream-50" : "border-sand-200 bg-cream-50 text-maroon-800 hover:border-maroon-300 hover:bg-cream-100",
                  )}
                  aria-pressed={last === key}
                >
                  <Ico size={18} aria-hidden /> {label}
                </button>
              ))}
            </div>
            {state && (
              <div className="mt-6 flex flex-wrap gap-2" aria-label="Current teaching strategy">
                <span className="chip bg-cream-200 text-maroon-800">{BAND_LABEL[state.strategy.band]}</span>
                <span className="chip bg-cream-200 text-maroon-800">{STYLE_LABEL[state.strategy.explanation_style]}</span>
                <span className="chip bg-cream-200 text-maroon-800">{DIFF_LABEL[state.strategy.difficulty]}</span>
                <span className="chip bg-cream-200 text-maroon-800">Hints: {HINT_LABEL[state.strategy.hint_level]}</span>
              </div>
            )}
            {state && (
              <button className="btn-ghost mt-4 text-sm" onClick={() => { setState(null); setLast(null); }}>
                <RefreshCcw size={16} aria-hidden /> Reset demo
              </button>
            )}
          </Reveal>
          <div className="card-sunny relative min-h-[360px] p-6 sm:p-8" aria-live="polite">
            <div className="flex items-center gap-3">
              <DiviAvatar size={56} mood={m.isPending ? "thinking" : last === "understand" ? "celebrating" : last ? "encouraging" : "happy"} />
              <div>
                <p className="font-semibold text-maroon-800">Divi</p>
                <p className="text-xs text-sand-500">AI learning guide · demo mode</p>
              </div>
            </div>
            {m.isError && <p className="mt-6 text-maroon-700">Divi can't connect right now - please make sure the Lumora API is running.</p>}
            {!state && !m.isPending && !m.isError && (
              <p className="mt-6 text-lg text-cocoa">Hi! Choose one of the buttons and I'll show you how I change the way I teach. 🌱</p>
            )}
            {m.isPending && (
              <div className="mt-6 space-y-2">
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/5" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            )}
            <AnimatePresence mode="wait">
              {reply && !m.isPending && (
                <motion.div key={`${last}-${state?.level}-${state?.strategy.explanation_style}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mt-5 space-y-4">
                  <p className="rounded-2xl bg-white p-4 text-cocoa shadow-soft">{reply.message}</p>
                  {reply.steps.length > 0 && (
                    <ol className="space-y-2">
                      {reply.steps.map((st, i) => (
                        <li key={i} className="flex gap-3 rounded-xl bg-white/70 p-3 text-sm">
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-maroon-600 text-xs font-bold text-cream-50">{i + 1}</span>
                          {st}
                        </li>
                      ))}
                    </ol>
                  )}
                  {reply.examples.length > 0 && (
                    <div className="text-sm">
                      <p className="font-semibold text-maroon-700">Example{reply.examples.length > 1 ? "s" : ""}</p>
                      <ul className="mt-1 space-y-1">{reply.examples.map((e, i) => <li key={i}>• {e}</li>)}</ul>
                    </div>
                  )}
                  <p className="text-sm italic text-maroon-600">{reply.encouragement}</p>
                  <div className="rounded-xl border border-cream-300 bg-white/60 p-3 text-xs text-cocoa-soft">
                    <strong className="text-maroon-700">What changed:</strong> {state?.explanation}
                    {state?.sources.length ? <> · Grounded in “{state.sources[0].title}”</> : null}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
