import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowRight, Check, ChevronDown, Clock, Info, MessageCircleHeart, Plus, Puzzle, Sparkles, Target, Trash2 } from "lucide-react";
import clsx from "clsx";
import { useDashboard, useTopics } from "@/hooks/queries";
import { api } from "@/lib/api";
import { masteryWords, pct, shortDate } from "@/lib/format";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { SubjectCard } from "@/components/app/SubjectCard";
import { JourneyPath } from "@/components/illustrations/JourneyPath";
import { Medal } from "@/components/illustrations/Decor";
import { Icon } from "@/components/ui/Icon";
import { EmptyState, ErrorState, PageSkeleton, ProgressBar, ProgressRing, stagger } from "@/components/ui";

const KIND_LABEL: Record<string, string> = { learn: "Discover", practice: "Practise", review: "Quick review", challenge: "Challenge" };

function GoalsCard({ goals }: { goals: { id: number; title: string; current: number | null; target: number | null; due_date: string | null }[] }) {
  const qc = useQueryClient();
  const topics = useTopics();
  const [title, setTitle] = useState("");
  const [topicId, setTopicId] = useState("");
  const [open, setOpen] = useState(false);
  const refresh = () => qc.invalidateQueries({ queryKey: ["dashboard"] });
  const add = useMutation({
    mutationFn: () => api("/api/goals", { method: "POST", json: { title, topic_id: topicId ? Number(topicId) : null } }),
    onSuccess: () => { setTitle(""); setTopicId(""); setOpen(false); refresh(); },
  });
  const done = useMutation({ mutationFn: (id: number) => api(`/api/goals/${id}`, { method: "PATCH", json: { status: "completed" } }), onSuccess: refresh });
  const remove = useMutation({ mutationFn: (id: number) => api(`/api/goals/${id}`, { method: "DELETE" }), onSuccess: refresh });
  const submit = (e: FormEvent) => { e.preventDefault(); if (title.trim().length >= 2) add.mutate(); };

  return (
    <section className="card p-6" aria-labelledby="goals-title">
      <div className="flex items-center justify-between">
        <h2 id="goals-title" className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><Target size={20} aria-hidden /> My goals</h2>
        <button className="btn-ghost px-3 text-sm" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
          <Plus size={16} aria-hidden /> Add goal
        </button>
      </div>
      {open && (
        <form onSubmit={submit} className="mt-4 space-y-3 rounded-2xl bg-cream-100 p-4">
          <label htmlFor="goal-title" className="text-sm font-medium">What would you like to get better at?</label>
          <input id="goal-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Become a fractions expert" maxLength={160} />
          <label htmlFor="goal-topic" className="text-sm font-medium">Link it to a topic (optional)</label>
          <select id="goal-topic" className="input" value={topicId} onChange={(e) => setTopicId(e.target.value)}>
            <option value="">No topic</option>
            {topics.data?.map((t) => <option key={t.id} value={t.id}>{t.subject.name} · {t.title}</option>)}
          </select>
          {add.isError && <p role="alert" className="text-sm text-maroon-700">{(add.error as Error).message}</p>}
          <button className="btn-primary" disabled={add.isPending || title.trim().length < 2}>Save goal</button>
        </form>
      )}
      {goals.length === 0 && !open ? (
        <p className="mt-4 text-cocoa-soft">No goals yet. Setting a small goal is a great way to start!</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {goals.map((g) => (
            <li key={g.id} className="rounded-2xl border border-sand-200 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium">{g.title}</p>
                  {g.due_date && <p className="text-xs text-sand-500">By {shortDate(g.due_date)}</p>}
                </div>
                <div className="flex gap-1">
                  <button className="rounded-full p-2 text-maroon-600 hover:bg-maroon-50" onClick={() => done.mutate(g.id)} aria-label={`Mark "${g.title}" as done`}><Check size={18} aria-hidden /></button>
                  <button className="rounded-full p-2 text-sand-500 hover:bg-sand-100" onClick={() => remove.mutate(g.id)} aria-label={`Remove "${g.title}"`}><Trash2 size={18} aria-hidden /></button>
                </div>
              </div>
              {g.target != null && g.current != null && (
                <div className="mt-3">
                  <ProgressBar value={g.current / g.target} label={`${g.title} progress`} />
                  <p className="mt-1 text-xs text-sand-500">{pct(g.current)} of {pct(g.target)} mastery</p>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function DashboardPage() {
  const { data: d, isLoading, isError, refetch } = useDashboard();
  const [why, setWhy] = useState(false);
  useEffect(() => { document.title = "My dashboard · Lumora"; }, []);

  if (isLoading) return <PageSkeleton label="Loading your dashboard" />;
  if (isError || !d) return <ErrorState onRetry={() => refetch()} />;

  const today = d.today;
  const learnedDays = d.week.filter((w) => w.learned).length;
  const earned = d.achievements.filter((a) => a.earned);
  const badges = [...d.achievements].sort((a, b) => Number(b.earned) - Number(a.earned) || b.progress / b.target - a.progress / a.target);
  const hasGrowth = d.growth.some((g) => g.mastery != null);

  return (
    <div className="space-y-8">
      {d.is_demo_account && (
        <p className="rounded-2xl border border-cream-300 bg-cream-100 px-4 py-3 text-sm text-maroon-800">
          <Info size={16} className="mr-1 inline" aria-hidden /> You're exploring the demo account. Its practice history was <strong>simulated</strong> to show how Lumora works.
        </p>
      )}

      {/* Welcome + today's adventure */}
      <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-cream-200 via-cream-100 to-white p-6 shadow-soft sm:p-8">
        <div className="grid grid-cols-[auto_1fr] items-center gap-4 sm:gap-6">
          <DiviAvatar size={72} className="sm:h-[104px] sm:w-[104px]" mood={d.insight.title.includes("really good") ? "celebrating" : "happy"} />
          <div>
            <h1 className="h-display text-2xl sm:text-4xl">{d.greeting}</h1>
            <p className="mt-2 text-lg font-medium text-maroon-700">{d.insight.title}</p>
            <button className="mt-1 inline-flex items-center gap-1 text-sm text-sand-500 hover:text-maroon-700" onClick={() => setWhy((w) => !w)} aria-expanded={why}>
              Why does Divi say that? <ChevronDown size={14} className={clsx("transition-transform", why && "rotate-180")} aria-hidden />
            </button>
            {why && <p className="mt-1 text-sm text-cocoa-soft">{d.insight.detail}</p>}
          </div>
        </div>
        {today?.topic && (
          <div className="mt-6 flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-soft sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-maroon-600 text-cream-50">
                <Icon name={today.topic.icon} size={26} />
              </span>
              <div>
                <p className="eyebrow">What should I learn today?</p>
                <p className="font-display text-xl font-semibold text-maroon-800">{today.topic.title}</p>
                <p className="text-sm text-cocoa-soft">{today.reason}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {today.lesson_id && <Link to={`/app/lesson/${today.lesson_id}`} className="btn-primary">Start lesson <ArrowRight size={16} aria-hidden /></Link>}
              <Link to={`/app/quiz/${today.topic.id}`} className="btn-secondary"><Puzzle size={16} aria-hidden /> Quick quiz</Link>
            </div>
          </div>
        )}
      </section>

      {/* How am I doing */}
      <motion.section className="grid gap-5 md:grid-cols-3" variants={stagger.container} initial="hidden" animate="show" aria-label="How am I doing?">
        <motion.div variants={stagger.item} className="card flex items-center gap-5 p-6">
          <ProgressRing value={d.progress.average_mastery} sublabel="mastery" />
          <div>
            <h2 className="font-semibold text-maroon-800">How am I doing?</h2>
            <p className="text-sm text-cocoa-soft">{d.progress.topics_practiced ? masteryWords(d.progress.average_mastery) : "Try your first quiz to see your progress!"}</p>
            <p className="mt-1 text-xs text-sand-500">{d.progress.topics_practiced} of {d.progress.topics_total} topics practised</p>
          </div>
        </motion.div>
        <motion.div variants={stagger.item} className="card p-6">
          <h2 className="font-semibold text-maroon-800">My learning week</h2>
          <ul className="mt-3 flex justify-between" aria-label="Days you learned this week">
            {d.week.map((w) => (
              <li key={w.date} className="flex flex-col items-center gap-1">
                <span className={clsx("flex h-9 w-9 items-center justify-center rounded-full text-xs", w.learned ? "bg-maroon-600 text-cream-50" : "bg-cream-200 text-sand-400")}>
                  {w.learned ? <Sparkles size={15} aria-hidden /> : "·"}
                </span>
                <span className="text-[0.7rem] text-sand-500">{w.label}</span>
                <span className="sr-only">{w.learned ? "learned" : "no learning"}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-cocoa-soft">
            You learned on <strong>{learnedDays}</strong> day{learnedDays === 1 ? "" : "s"} this week. {learnedDays >= d.weekly_goal_days ? "Goal reached - brilliant!" : `Your gentle goal is ${d.weekly_goal_days}.`}
          </p>
        </motion.div>
        <motion.div variants={stagger.item} className="card p-6">
          <h2 className="font-semibold text-maroon-800">What did I achieve?</h2>
          <p className="mt-2 font-display text-4xl font-semibold text-maroon-700">{earned.length}<span className="text-lg text-sand-400">/{d.achievements.length}</span></p>
          <p className="text-sm text-cocoa-soft">badges earned · {d.progress.correct_answers} correct answers</p>
          {d.learning_days_in_a_row > 1 && <p className="mt-2 text-xs text-sand-500">{d.learning_days_in_a_row} learning days in a row - nice! Breaks are always okay.</p>}
        </motion.div>
      </motion.section>

      <section className="card px-4 py-8 sm:px-8" aria-labelledby="journey-title">
        <h2 id="journey-title" className="mb-6 font-display text-xl font-semibold text-maroon-800">My learning journey</h2>
        <JourneyPath current={d.journey.current} />
      </section>

      {/* What should I practise */}
      {d.recommendations.length > 1 && (
        <section aria-labelledby="practise-title">
          <h2 id="practise-title" className="mb-4 font-display text-2xl font-semibold text-maroon-800">What can I try next?</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {d.recommendations.slice(1).map((r) => r.topic && (
              <article key={r.id} className="card group flex items-center gap-4 p-5 transition hover:-translate-y-1 hover:shadow-lift">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cream-200 text-maroon-600 transition-transform group-hover:rotate-6"><Icon name={r.topic.icon} /></span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold uppercase tracking-wider text-maroon-500">{KIND_LABEL[r.kind] ?? r.kind}</p>
                  <p className="font-semibold text-maroon-800">{r.topic.title}</p>
                  <p className="text-sm text-cocoa-soft">{r.reason}</p>
                </div>
                <Link to={r.kind === "learn" && r.lesson_id ? `/app/lesson/${r.lesson_id}` : `/app/quiz/${r.topic.id}`} className="btn-secondary shrink-0 px-4 text-sm" aria-label={`Go to ${r.topic.title}`}>
                  Go <ArrowRight size={14} aria-hidden />
                </Link>
              </article>
            ))}
          </div>
        </section>
      )}

      <section aria-labelledby="subjects-title">
        <div className="mb-4 flex items-end justify-between">
          <h2 id="subjects-title" className="font-display text-2xl font-semibold text-maroon-800">My subjects</h2>
          <Link to="/app/explore" className="text-sm font-medium text-maroon-700 hover:underline">See all topics</Link>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {d.subjects.map((s) => <SubjectCard key={s.id} subject={s} />)}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-6" aria-labelledby="growth-title">
          <h2 id="growth-title" className="font-display text-xl font-semibold text-maroon-800">My growth</h2>
          {hasGrowth ? (
            <div className="mt-4 h-48" role="img" aria-label="Chart of your average mastery over the last two weeks">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={d.growth} margin={{ left: -20, right: 8, top: 8 }}>
                  <defs>
                    <linearGradient id="growth" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#AE4F5E" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="#F8D570" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tickFormatter={shortDate} tick={{ fontSize: 11, fill: "#76695C" }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11, fill: "#76695C" }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${Math.round(v * 100)}%`, "Mastery"]} labelFormatter={shortDate} />
                  <Area type="monotone" dataKey="mastery" stroke="#772233" strokeWidth={3} fill="url(#growth)" connectNulls />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="mt-4 text-cocoa-soft">Your growth line appears after your first quiz. 🌱</p>
          )}
        </section>
        <GoalsCard goals={d.goals} />
      </div>

      <section aria-labelledby="badges-title">
        <h2 id="badges-title" className="mb-4 font-display text-2xl font-semibold text-maroon-800">My badges</h2>
        <motion.ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" variants={stagger.container} initial="hidden" whileInView="show" viewport={{ once: true }}>
          {badges.map((a) => (
            <motion.li key={a.key} variants={stagger.item} className={clsx("card flex items-center gap-4 p-4", !a.earned && "bg-sand-50")}>
              <Medal earned={a.earned}><Icon name={a.icon} size={20} /></Medal>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-maroon-800">{a.title} {a.earned && <span className="chip ml-1 bg-maroon-600 text-cream-50"><Check size={12} aria-hidden /> Earned</span>}</p>
                <p className="text-sm text-cocoa-soft">{a.description}</p>
                {!a.earned && <ProgressBar className="mt-2" value={a.progress / a.target} label={`${a.title} progress`} />}
              </div>
            </motion.li>
          ))}
        </motion.ul>
      </section>

      <section className="card p-6" aria-labelledby="recent-title">
        <h2 id="recent-title" className="font-display text-xl font-semibold text-maroon-800">Recent activity</h2>
        {d.recent_activity.length === 0 ? (
          <EmptyState
            title="Your adventure starts here"
            message="Open a lesson or ask Divi a question - your activity will show up here."
            action={<Link to="/app/tutor" className="btn-primary"><MessageCircleHeart size={18} aria-hidden /> Ask Divi</Link>}
          />
        ) : (
          <ul className="mt-4 divide-y divide-sand-100">
            {d.recent_activity.map((a, i) => (
              <li key={`${a.at}-${i}`} className="flex items-center justify-between gap-3 py-3">
                <span>{a.text}{a.score != null && <span className="text-sand-500"> · {Math.round(a.score * 100)}%</span>}</span>
                <span className="flex shrink-0 items-center gap-1 text-xs text-sand-500"><Clock size={12} aria-hidden /> {shortDate(a.at)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
