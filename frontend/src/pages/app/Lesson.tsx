import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, ChevronDown, Coffee, Lightbulb, MessageCircleHeart, Puzzle, Sparkles } from "lucide-react";
import clsx from "clsx";
import { useLesson } from "@/hooks/queries";
import { api } from "@/lib/api";
import { track } from "@/lib/tracker";
import { BAND_LABEL, LEVEL_LABEL, STYLE_LABEL } from "@/lib/format";
import type { LessonSection } from "@/lib/types";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { Celebration, ErrorState, PageSkeleton, ReadAloud } from "@/components/ui";
import { Icon } from "@/components/ui/Icon";

function sectionText(s: LessonSection): string {
  if (typeof s.content === "string") return s.content;
  return (s.content as (string | { term: string; meaning: string })[])
    .map((c) => (typeof c === "string" ? c : `${c.term}: ${c.meaning}`))
    .join(". ");
}

function SectionBody({ s }: { s: LessonSection }) {
  if (s.kind === "steps")
    return (
      <ol className="space-y-3">
        {(s.content as string[]).map((step, i) => (
          <li key={i} className="flex gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-maroon-600 font-semibold text-cream-50">{i + 1}</span>
            <span className="pt-1">{step}</span>
          </li>
        ))}
      </ol>
    );
  if (s.kind === "list")
    return (
      <ul className="space-y-3">
        {(s.content as string[]).map((e, i) => (
          <li key={i} className="flex gap-3 rounded-2xl bg-cream-100 p-4"><Sparkles size={18} className="mt-1 shrink-0 text-maroon-500" aria-hidden />{e}</li>
        ))}
      </ul>
    );
  if (s.kind === "vocabulary")
    return (
      <dl className="grid gap-3 sm:grid-cols-2">
        {(s.content as { term: string; meaning: string }[]).map((v) => (
          <div key={v.term} className="rounded-2xl border border-cream-300 bg-cream-50 p-4">
            <dt className="font-semibold text-maroon-700">{v.term}</dt>
            <dd className="text-cocoa-soft">{v.meaning}</dd>
          </div>
        ))}
      </dl>
    );
  return <p>{s.content as string}</p>;
}

export default function LessonPage() {
  const id = Number(useParams().id);
  const { data: lesson, isLoading, isError, refetch } = useLesson(id);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [done, setDone] = useState(false);
  const [breakDismissed, setBreakDismissed] = useState(false);
  const started = useRef(Date.now());
  const qc = useQueryClient();
  const navigate = useNavigate();

  useEffect(() => {
    if (lesson) {
      document.title = `${lesson.title} · Lumora`;
      setOpen(Object.fromEntries(lesson.sections.map((s) => [s.key, s.shown])));
      started.current = Date.now();
    }
  }, [lesson]);

  const complete = useMutation({
    mutationFn: () => api(`/api/lessons/${id}/complete`, { method: "POST", json: { seconds: Math.round((Date.now() - started.current) / 1000), progress: 1 } }),
    onSuccess: () => { setDone(true); qc.invalidateQueries({ queryKey: ["dashboard"] }); },
  });

  if (isLoading) return <PageSkeleton label="Preparing your lesson" />;
  if (isError || !lesson) return <ErrorState onRetry={() => refetch()} />;

  const st = lesson.strategy;
  const toggle = (s: LessonSection) => {
    setOpen((o) => ({ ...o, [s.key]: !o[s.key] }));
    if (!open[s.key]) track({ event_type: "section_viewed", topic_id: lesson.topic.id, lesson_id: lesson.id, payload: { section: s.key } });
  };
  const fullText = lesson.sections.filter((s) => open[s.key]).map((s) => `${s.title}. ${sectionText(s)}`).join(" ");

  return (
    <article className="mx-auto max-w-3xl space-y-6">
      <Celebration show={done} />
      <Link to="/app/explore" className="inline-flex items-center gap-1 text-sm font-medium text-maroon-700 hover:underline">
        <ArrowLeft size={16} aria-hidden /> Back to topics
      </Link>

      <header className="card-sunny p-6 sm:p-8">
        <div className="flex items-center gap-2 text-sm font-medium text-maroon-600">
          <Icon name={lesson.topic.icon} size={18} /> {lesson.topic.subject.name} · {lesson.topic.title}
        </div>
        <h1 className="h-display mt-2 text-3xl sm:text-4xl">{lesson.title}</h1>
        <div className="mt-4 flex items-start gap-3 rounded-2xl bg-white/80 p-4">
          <DiviAvatar size={48} mood="encouraging" />
          <div>
            <p className="text-cocoa">{st.learner_message}</p>
            <p className="mt-2 flex flex-wrap gap-1.5 text-xs" aria-label="How this lesson was adapted for you">
              <span className="chip bg-cream-200 text-maroon-800">{BAND_LABEL[st.band]}</span>
              <span className="chip bg-cream-200 text-maroon-800">{STYLE_LABEL[st.explanation_style]}</span>
              <span className="chip bg-cream-200 text-maroon-800">{LEVEL_LABEL[st.content_density]} reading</span>
              <span className="chip bg-cream-200 text-maroon-800">~{lesson.estimated_minutes} min</span>
            </p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <ReadAloud text={`${lesson.title}. ${fullText}`} topicId={lesson.topic.id} lessonId={lesson.id} className={clsx(st.read_aloud_suggested && "bg-cream-200")} />
          {st.read_aloud_suggested && <span className="text-xs text-sand-500">Tip: listening along can make reading easier.</span>}
        </div>
      </header>

      {st.suggest_break && !breakDismissed && (
        <div className="flex flex-col gap-3 rounded-2xl border border-cream-300 bg-cream-100 p-4 sm:flex-row sm:items-center sm:justify-between" role="status">
          <p className="flex items-center gap-2 text-maroon-800"><Coffee size={18} aria-hidden /> You've been working hard! A short brain break can help ideas stick.</p>
          <button className="btn-secondary text-sm" onClick={() => { setBreakDismissed(true); track({ event_type: "break_taken", topic_id: lesson.topic.id }); }}>
            Thanks, Divi
          </button>
        </div>
      )}

      <div className="reading max-w-none space-y-4 text-[1.06rem]">
        {lesson.sections.map((s) => (
          <section key={s.key} className={clsx("card overflow-hidden", s.key === "key_idea" && "border-maroon-200")}>
            <h2>
              <button
                className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left font-display text-xl font-semibold text-maroon-800 hover:bg-cream-50"
                aria-expanded={!!open[s.key]}
                aria-controls={`sec-${s.key}`}
                onClick={() => toggle(s)}
              >
                <span className="flex items-center gap-2">
                  {s.key === "key_idea" && <Lightbulb size={20} className="text-maroon-500" aria-hidden />}
                  {s.title}
                </span>
                <ChevronDown className={clsx("shrink-0 transition-transform", open[s.key] && "rotate-180")} size={20} aria-hidden />
              </button>
            </h2>
            <AnimatePresence initial={false}>
              {open[s.key] && (
                <motion.div id={`sec-${s.key}`} initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}>
                  <div className="px-5 pb-5 text-cocoa"><SectionBody s={s} /></div>
                </motion.div>
              )}
            </AnimatePresence>
          </section>
        ))}
      </div>

      <footer className="card flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        {done ? (
          <>
            <p className="flex items-center gap-2 font-semibold text-maroon-700"><CheckCircle2 aria-hidden /> Lesson complete - fantastic reading!</p>
            <button className="btn-primary" onClick={() => navigate(`/app/quiz/${lesson.topic.id}`)}><Puzzle size={18} aria-hidden /> Try a quiz</button>
          </>
        ) : (
          <>
            <Link to={`/app/tutor?topic=${lesson.topic.id}`} className="btn-secondary"><MessageCircleHeart size={18} aria-hidden /> Ask Divi about this</Link>
            <button className="btn-primary" onClick={() => complete.mutate()} disabled={complete.isPending}>
              <CheckCircle2 size={18} aria-hidden /> I've finished reading
            </button>
          </>
        )}
      </footer>
    </article>
  );
}
