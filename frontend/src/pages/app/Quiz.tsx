import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, BookOpen, CheckCircle2, CircleDashed, Lightbulb, MessageCircleHeart, RotateCcw, SkipForward, TrendingUp } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { DIFF_LABEL, STAGE_LABEL } from "@/lib/format";
import type { Quiz, QuizResult } from "@/lib/types";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { Celebration, ErrorState, PageSkeleton, ProgressBar, ProgressRing, ReadAloud } from "@/components/ui";

interface AnswerState {
  question_id: number;
  selected_index: number | null;
  response_ms: number;
  hints_used: number;
  answer_changes: number;
  confidence: number | null;
}

const CONFIDENCE = [
  { v: 1, label: "Not sure", emoji: "🤔" },
  { v: 2, label: "Kind of", emoji: "🙂" },
  { v: 3, label: "Sure!", emoji: "😄" },
];
const LETTERS = "ABCD";

function Results({ r, onAgain }: { r: QuizResult; onAgain: () => void }) {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Celebration show={r.celebrate} />
      <section className="card-sunny p-6 text-center sm:p-10">
        <DiviAvatar size={96} mood={r.celebrate ? "celebrating" : "encouraging"} className="mx-auto" />
        <h1 className="h-display mt-4 text-3xl">{r.headline}</h1>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-8">
          <ProgressRing value={r.score} size={120} label={`${r.correct}/${r.total}`} sublabel="correct" />
          <div className="text-left">
            <p className="text-sm font-semibold text-maroon-700">Topic mastery</p>
            <div className="mt-2 flex items-center gap-3">
              <span className="font-display text-2xl text-sand-400">{Math.round(r.mastery_before * 100)}%</span>
              <ArrowRight aria-hidden className="text-maroon-400" />
              <span className="font-display text-3xl font-semibold text-maroon-700">{Math.round(r.mastery_after * 100)}%</span>
            </div>
            <p className="mt-1 text-sm text-cocoa-soft">{STAGE_LABEL[r.stage]}</p>
          </div>
        </div>
        <p className="mx-auto mt-6 max-w-lg rounded-2xl bg-white/80 px-4 py-3 text-sm text-maroon-800">
          <TrendingUp size={16} className="mr-1.5 inline align-[-3px]" aria-hidden />
          Next time: <strong>{DIFF_LABEL[r.next_difficulty]}</strong> questions. {r.next_message}
        </p>
      </section>

      {r.revision.needed && (
        <section className="card p-6">
          <h2 className="font-display text-xl font-semibold text-maroon-800">Recommended revision</h2>
          {r.revision.tips.length > 0 && (
            <ul className="mt-3 space-y-2 text-cocoa">{r.revision.tips.map((t, i) => <li key={i}>💡 {t}</li>)}</ul>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            {r.revision.lesson_id && <Link to={`/app/lesson/${r.revision.lesson_id}`} className="btn-secondary"><BookOpen size={16} aria-hidden /> Re-read “{r.revision.lesson_title}”</Link>}
            <Link to={`/app/tutor?topic=${r.topic.id}&ask=${encodeURIComponent(r.revision.tutor_prompt)}`} className="btn-secondary"><MessageCircleHeart size={16} aria-hidden /> Ask Divi to explain differently</Link>
          </div>
        </section>
      )}

      <section className="card p-6">
        <h2 className="font-display text-xl font-semibold text-maroon-800">Let's look back</h2>
        <ol className="mt-4 space-y-4">
          {r.results.map((q, i) => (
            <li key={q.question_id} className={clsx("rounded-2xl border p-4", q.is_correct ? "border-cream-300 bg-cream-50" : "border-maroon-100 bg-maroon-50/40")}>
              <p className="font-medium">{i + 1}. {q.prompt}</p>
              <p className="mt-2 flex items-center gap-2 text-sm font-semibold text-maroon-700">
                {q.is_correct ? <CheckCircle2 size={16} aria-hidden /> : <CircleDashed size={16} aria-hidden />} {q.feedback}
              </p>
              {!q.is_correct && (
                <p className="mt-1 text-sm text-cocoa">
                  {q.your_answer && <>You chose “{q.your_answer}”. </>}The answer is <strong>“{q.correct_answer}”</strong>.
                </p>
              )}
              <p className="mt-1 text-sm text-cocoa-soft">{q.explanation}</p>
            </li>
          ))}
        </ol>
      </section>

      <div className="flex flex-wrap justify-center gap-3">
        <button className="btn-primary" onClick={onAgain}><RotateCcw size={16} aria-hidden /> Another quiz</button>
        <Link to="/app" className="btn-secondary">Back to my dashboard</Link>
      </div>
    </div>
  );
}

export default function QuizPage() {
  const topicId = Number(useParams().topicId);
  const qc = useQueryClient();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<AnswerState[]>([]);
  const [hint, setHint] = useState<string | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const shownAt = useRef(Date.now());

  const generate = useMutation({
    mutationFn: () => api<Quiz>("/api/quiz/generate", { method: "POST", json: { topic_id: topicId } }),
    onSuccess: (q) => {
      setQuiz(q);
      setIdx(0);
      setResult(null);
      setHint(null);
      setAnswers(q.questions.map((x) => ({ question_id: x.id, selected_index: null, response_ms: 0, hints_used: 0, answer_changes: 0, confidence: null })));
      shownAt.current = Date.now();
      document.title = `Quiz: ${q.topic.title} · Lumora`;
    },
  });
  const submit = useMutation({
    mutationFn: (payload: AnswerState[]) => api<QuizResult>(`/api/quiz/${quiz!.attempt_id}/submit`, { method: "POST", json: { answers: payload } }),
    onSuccess: (r) => {
      setResult(r);
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["subjects"] });
      window.scrollTo({ top: 0 });
    },
  });
  const askHint = useMutation({
    mutationFn: (qid: number) => api<{ hint: string }>(`/api/quiz/${quiz!.attempt_id}/hint/${qid}`),
    onSuccess: (h) => {
      setHint(h.hint);
      setAnswers((a) => a.map((x, i) => (i === idx ? { ...x, hints_used: x.hints_used + 1 } : x)));
    },
  });

  const startedFor = useRef<number | null>(null);
  useEffect(() => {
    if (startedFor.current === topicId) return; // StrictMode double-invoke guard: one attempt per visit
    startedFor.current = topicId;
    generate.mutate();
  }, [topicId, generate]);

  if (generate.isError) return <ErrorState message={(generate.error as Error).message} onRetry={() => generate.mutate()} />;
  if (result) return <Results r={result} onAgain={() => generate.mutate()} />;
  if (!quiz || generate.isPending) return <PageSkeleton label="Divi is choosing questions for you" />;

  const q = quiz.questions[idx];
  const a = answers[idx];
  const last = idx === quiz.questions.length - 1;

  const choose = (i: number) =>
    setAnswers((all) => all.map((x, k) => (k === idx ? { ...x, selected_index: i, answer_changes: x.selected_index !== null && x.selected_index !== i ? x.answer_changes + 1 : x.answer_changes } : x)));
  const setConfidence = (v: number) => setAnswers((all) => all.map((x, k) => (k === idx ? { ...x, confidence: v } : x)));

  const advance = (skip = false) => {
    const elapsed = Date.now() - shownAt.current;
    const updated = answers.map((x, k) => (k === idx ? { ...x, response_ms: x.response_ms + elapsed, selected_index: skip ? null : x.selected_index } : x));
    setAnswers(updated);
    setHint(null);
    if (last) submit.mutate(updated);
    else {
      setIdx(idx + 1);
      shownAt.current = Date.now();
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Quiz · {quiz.topic.title}</p>
          <p className="text-sm text-sand-500">Question {idx + 1} of {quiz.questions.length} · {DIFF_LABEL[quiz.difficulty]} level</p>
        </div>
        <DiviAvatar size={48} mood={askHint.isPending ? "thinking" : "happy"} />
      </header>
      <ProgressBar value={(idx + (a.selected_index !== null ? 1 : 0)) / quiz.questions.length} label="Quiz progress" />
      {idx === 0 && <p className="rounded-2xl bg-cream-100 px-4 py-3 text-sm text-maroon-800">{quiz.strategy.learner_message}</p>}

      <AnimatePresence mode="wait">
        <motion.section key={q.id} className="card p-6 sm:p-8" initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.25 }} aria-labelledby={`q-${q.id}`}>
          <div className="flex items-start justify-between gap-3">
            <h1 id={`q-${q.id}`} className="font-display text-2xl font-semibold leading-snug text-maroon-800">{q.prompt}</h1>
            <ReadAloud text={`${q.prompt}. ${q.options.map((o, i) => `${LETTERS[i]}: ${o}`).join(". ")}`} topicId={quiz.topic.id} className="shrink-0" />
          </div>
          <div role="radiogroup" aria-labelledby={`q-${q.id}`} className="mt-6 grid gap-3">
            {q.options.map((opt, i) => {
              const selected = a.selected_index === i;
              return (
                <motion.button
                  key={`${q.id}-${i}`}
                  role="radio"
                  aria-checked={selected}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => choose(i)}
                  className={clsx(
                    "flex min-h-[60px] items-center gap-4 rounded-2xl border-2 px-4 py-3 text-left text-lg transition-colors",
                    selected ? "border-maroon-600 bg-maroon-50 text-maroon-800" : "border-sand-200 bg-white hover:border-maroon-300 hover:bg-cream-50",
                  )}
                >
                  <span className={clsx("flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-semibold", selected ? "bg-maroon-600 text-cream-50" : "bg-cream-200 text-maroon-700")}>{LETTERS[i]}</span>
                  {opt}
                </motion.button>
              );
            })}
          </div>

          <fieldset className="mt-6">
            <legend className="text-sm font-medium text-cocoa-soft">How sure are you?</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {CONFIDENCE.map((c) => (
                <button key={c.v} type="button" onClick={() => setConfidence(c.v)} aria-pressed={a.confidence === c.v}
                  className={clsx("btn border px-4 py-2 text-sm", a.confidence === c.v ? "border-maroon-600 bg-maroon-600 text-cream-50" : "border-sand-200 bg-white text-cocoa hover:bg-cream-100")}>
                  <span aria-hidden>{c.emoji}</span> {c.label}
                </button>
              ))}
            </div>
          </fieldset>

          <AnimatePresence>
            {hint && (
              <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mt-5 flex gap-2 rounded-2xl bg-cream-100 p-4 text-maroon-800" role="status">
                <Lightbulb size={20} className="shrink-0" aria-hidden /> <span><strong>Here's a clue:</strong> {hint}</span>
              </motion.p>
            )}
          </AnimatePresence>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2">
              <button className={clsx("btn-ghost text-sm", ["guided", "full"].includes(quiz.strategy.hint_level) && "bg-cream-200")} onClick={() => askHint.mutate(q.id)} disabled={askHint.isPending}>
                <Lightbulb size={16} aria-hidden /> Hint
              </button>
              <button className="btn-ghost text-sm" onClick={() => advance(true)} disabled={submit.isPending}>
                <SkipForward size={16} aria-hidden /> Skip
              </button>
            </div>
            <button className="btn-primary" onClick={() => advance()} disabled={a.selected_index === null || submit.isPending}>
              {last ? "Finish quiz" : "Next question"} <ArrowRight size={16} aria-hidden />
            </button>
          </div>
          {submit.isError && <p role="alert" className="mt-3 text-sm text-maroon-700">{(submit.error as Error).message}</p>}
        </motion.section>
      </AnimatePresence>
      <p className="text-center text-xs text-sand-500">Skipping is always okay - Divi uses it to make the next quiz a better fit.</p>
    </div>
  );
}
