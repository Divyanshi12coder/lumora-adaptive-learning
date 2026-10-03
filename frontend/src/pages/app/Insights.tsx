import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, CalendarDays, Clock, Gauge, Info, ListChecks, ShieldCheck, Sparkles, Target, Users } from "lucide-react";
import clsx from "clsx";
import { useAnalytics } from "@/hooks/queries";
import { api } from "@/lib/api";
import { BAND_LABEL, DIFF_LABEL, HINT_LABEL, LEVEL_LABEL, STYLE_LABEL, pct, shortDate } from "@/lib/format";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/ui";

const C = { maroon: "#772233", rose: "#AE4F5E", gold: "#E9B949", sand: "#A39584", grid: "#F2ECE3" };
const SERIES = ["#772233", "#E9B949", "#AE4F5E", "#5A4F45", "#CF8591", "#D9A93A"];
const axis = { tick: { fontSize: 11, fill: "#76695C" }, axisLine: false, tickLine: false } as const;

function Stat({ icon: Ico, label, value, sub }: { icon: typeof Clock; label: string; value: string; sub?: string }) {
  return (
    <div className="card p-5">
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-sand-500"><Ico size={14} className="text-maroon-500" aria-hidden /> {label}</p>
      <p className="mt-2 font-display text-3xl font-semibold text-maroon-800">{value}</p>
      {sub && <p className="text-xs text-sand-500">{sub}</p>}
    </div>
  );
}

function ChartCard({ title, desc, children }: { title: string; desc: string; children: React.ReactNode }) {
  return (
    <section className="card p-5 sm:p-6">
      <h2 className="font-display text-lg font-semibold text-maroon-800">{title}</h2>
      <p className="text-sm text-sand-500">{desc}</p>
      <div className="mt-4 h-64" role="img" aria-label={`${title}: ${desc}`}>{children}</div>
    </section>
  );
}

function StudyPlan() {
  const plan = useMutation({
    mutationFn: () => api<{ title: string; items: { day: string; focus: string; activity: string; minutes: number }[]; note: string; is_demo: boolean }>("/api/study-plan", { method: "POST", json: { minutes_per_day: 15, days: 5 } }),
  });
  return (
    <section className="card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-maroon-800"><CalendarDays size={18} aria-hidden /> Suggested study plan</h2>
          <p className="text-sm text-sand-500">Built from the recommendation ranking, then written by the AI layer.</p>
        </div>
        <button className="btn-secondary text-sm" onClick={() => plan.mutate()} disabled={plan.isPending}>{plan.data ? "Make a new plan" : "Create plan"}</button>
      </div>
      {plan.isError && <p role="alert" className="mt-3 text-sm text-maroon-700">{(plan.error as Error).message}</p>}
      {plan.data && (
        <div className="mt-4">
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
            {plan.data.items.map((i) => (
              <li key={i.day} className="rounded-2xl bg-cream-100 p-3 text-sm">
                <p className="font-semibold text-maroon-800">{i.day}</p>
                <p className="font-medium">{i.focus}</p>
                <p className="text-cocoa-soft">{i.activity}</p>
                <p className="mt-1 text-xs text-sand-500">{i.minutes} min</p>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-cocoa-soft">{plan.data.note} {plan.data.is_demo && <span className="chip bg-sand-100 text-sand-600">Demo mode</span>}</p>
        </div>
      )}
    </section>
  );
}

export default function InsightsPage() {
  const [days, setDays] = useState(30);
  const { data: a, isLoading, isError, refetch } = useAnalytics(days);
  useEffect(() => { document.title = "Learning insights · Lumora"; }, []);
  if (isLoading) return <PageSkeleton label="Loading insights" />;
  if (isError || !a) return <ErrorState onRetry={() => refetch()} />;

  const s = a.summary;
  const strat = a.current_strategy;
  const topicKeys = Object.keys(a.mastery_topics).slice(0, 6);
  const factors = (strat.factors ?? []).map((f) => ({ name: f.family.replace("_", " "), contribution: +(f.need * f.weight).toFixed(3), need: f.need, note: f.note }));
  const hasData = s.questions_answered > 0;

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">For parents & teachers</p>
          <h1 className="h-display mt-2 text-3xl sm:text-4xl">Learning insights</h1>
          <p className="mt-2 max-w-2xl text-cocoa-soft">The detailed view behind the child's friendly dashboard: progress, behaviour signals, adaptive-engine decisions and model transparency.</p>
        </div>
        <div className="flex gap-1 rounded-full bg-white p-1 shadow-soft" role="group" aria-label="Time range">
          {[7, 30, 90].map((d) => (
            <button key={d} onClick={() => setDays(d)} aria-pressed={days === d} className={clsx("rounded-full px-4 py-2 text-sm font-medium", days === d ? "bg-maroon-600 text-cream-50" : "text-cocoa hover:bg-cream-100")}>
              {d} days
            </button>
          ))}
        </div>
      </header>

      <p className="flex items-start gap-2 rounded-2xl border border-cream-300 bg-cream-100 p-4 text-sm text-maroon-800">
        <ShieldCheck size={18} className="mt-0.5 shrink-0" aria-hidden />
        These insights describe learning behaviour only. Lumora does not diagnose ADHD, dyslexia, autism or any other condition, and learning profiles are not labels for a child.
      </p>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat icon={Clock} label="Time learning" value={`${Math.round(s.minutes)} min`} sub={`${s.sessions} sessions`} />
        <Stat icon={ListChecks} label="Questions" value={String(s.questions_answered)} sub={`Accuracy ${pct(s.accuracy)}`} />
        <Stat icon={Target} label="Avg. mastery" value={pct(s.average_mastery)} sub={`${s.topics_practiced} topics practised`} />
        <Stat icon={Sparkles} label="Trend" value={s.trend.replace(/_/g, " ")} sub={`${s.hint_rate} hints / question`} />
      </div>

      {!hasData ? (
        <EmptyState title="No learning data yet" message="Once the learner completes a quiz, charts and model insights will appear here." />
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-2">
            <ChartCard title="Mastery over time" desc="Bayesian Knowledge Tracing estimate per topic and overall average">
              <ResponsiveContainer>
                <LineChart data={a.mastery_trend} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} />
                  <XAxis dataKey="date" tickFormatter={shortDate} {...axis} minTickGap={24} />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} {...axis} />
                  <Tooltip formatter={(v: number) => `${Math.round(v * 100)}%`} labelFormatter={shortDate} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="average_mastery" name="Average" stroke={C.maroon} strokeWidth={3} dot={false} connectNulls />
                  {topicKeys.map((k, i) => (
                    <Line key={k} type="monotone" dataKey={k} name={a.mastery_topics[k]} stroke={SERIES[(i + 1) % SERIES.length]} strokeWidth={1.5} strokeDasharray="4 3" dot={false} connectNulls />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard title="Accuracy trend" desc="Share of questions answered correctly each day">
              <ResponsiveContainer>
                <BarChart data={a.accuracy_trend} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} />
                  <XAxis dataKey="date" tickFormatter={shortDate} {...axis} minTickGap={24} />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} {...axis} />
                  <Tooltip formatter={(v: number, n) => (n === "accuracy" ? `${Math.round(v * 100)}%` : v)} labelFormatter={shortDate} />
                  <Bar dataKey="accuracy" name="accuracy" fill={C.rose} radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard title="Engagement" desc="Minutes of learning and interaction events per day">
              <ResponsiveContainer>
                <BarChart data={a.engagement_trend} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} />
                  <XAxis dataKey="date" tickFormatter={shortDate} {...axis} minTickGap={24} />
                  <YAxis {...axis} />
                  <Tooltip labelFormatter={shortDate} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="minutes" name="Minutes" fill={C.maroon} radius={[6, 6, 0, 0]} />
                  <Bar dataKey="events" name="Events" fill={C.gold} radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard title="Topic performance" desc="Accuracy and mastery by topic (lowest mastery first)">
              <ResponsiveContainer>
                <BarChart data={a.topic_performance} layout="vertical" margin={{ left: 30, right: 8 }}>
                  <CartesianGrid stroke={C.grid} horizontal={false} />
                  <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} {...axis} />
                  <YAxis type="category" dataKey="topic" width={110} {...axis} />
                  <Tooltip formatter={(v: number) => `${Math.round(v * 100)}%`} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="mastery" name="Mastery" fill={C.maroon} radius={[0, 6, 6, 0]} />
                  <Bar dataKey="accuracy" name="Accuracy" fill={C.gold} radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <section className="card overflow-x-auto p-5 sm:p-6">
            <h2 className="font-display text-lg font-semibold text-maroon-800">Topic details</h2>
            <table className="mt-3 w-full min-w-[560px] text-left text-sm">
              <caption className="sr-only">Per-topic learning signals</caption>
              <thead className="text-xs uppercase tracking-wider text-sand-500">
                <tr><th className="py-2">Topic</th><th>Answered</th><th>Accuracy</th><th>Mastery</th><th>Avg. time</th><th>Hints / q</th><th>Skips</th></tr>
              </thead>
              <tbody className="divide-y divide-sand-100">
                {a.topic_performance.map((t) => (
                  <tr key={t.topic_id}>
                    <td className="py-2 font-medium">{t.topic}</td><td>{t.answered}</td><td>{pct(t.accuracy)}</td><td>{pct(t.mastery)}</td>
                    <td>{t.avg_response_seconds}s</td><td>{t.hints_per_question}</td><td>{pct(t.skip_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}

      <section className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <div className="card p-5 sm:p-6">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-maroon-800"><Gauge size={18} aria-hidden /> Current adaptive strategy</h2>
          <p className="text-sm text-sand-500">What the engine would choose right now (engine v{strat.engine_version ?? "1"})</p>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            {[
              ["Band", BAND_LABEL[strat.band]],
              ["Difficulty", DIFF_LABEL[strat.difficulty]],
              ["Style", STYLE_LABEL[strat.explanation_style]],
              ["Density", LEVEL_LABEL[strat.content_density]],
              ["Hints", HINT_LABEL[strat.hint_level]],
              ["Examples", String(strat.example_count)],
              ["Support score", strat.support_score.toFixed(2)],
              ["Data confidence", pct(strat.data_confidence)],
              ["Review needed", strat.review_required ? "Yes" : "No"],
            ].map(([k, v]) => (
              <div key={k} className="rounded-xl bg-cream-50 p-3"><dt className="text-xs text-sand-500">{k}</dt><dd className="font-semibold text-maroon-800">{v}</dd></div>
            ))}
          </dl>
          <ul className="mt-4 space-y-1 text-sm text-cocoa">{strat.rationale.map((r) => <li key={r}>• {r}</li>)}</ul>
        </div>
        <ChartCard title="Why: factor contributions" desc="Support need × weight for each signal family (higher = more scaffolding)">
          <ResponsiveContainer>
            <BarChart data={factors} layout="vertical" margin={{ left: 20, right: 8 }}>
              <CartesianGrid stroke={C.grid} horizontal={false} />
              <XAxis type="number" {...axis} />
              <YAxis type="category" dataKey="name" width={90} {...axis} />
              <Tooltip formatter={(v: number, _n, p) => [v, (p?.payload as { note?: string })?.note ?? ""]} />
              <Bar dataKey="contribution" fill={C.rose} radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      {a.strategy_history.length > 1 && (
        <ChartCard title="Adaptive decisions over time" desc="Support score chosen by the engine for each lesson, quiz and tutor turn">
          <ResponsiveContainer>
            <LineChart data={a.strategy_history} margin={{ left: -16, right: 8 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="at" tickFormatter={shortDate} {...axis} minTickGap={30} />
              <YAxis domain={[0, 1]} {...axis} />
              <Tooltip labelFormatter={(v) => new Date(v).toLocaleString()} formatter={(v: number, _n, p) => [v.toFixed(2), `${(p?.payload as { context: string }).context} · ${(p?.payload as { difficulty: string }).difficulty}`]} />
              <Line type="stepAfter" dataKey="support_score" stroke={C.maroon} strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="card p-6">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-maroon-800"><BrainCircuit size={18} aria-hidden /> Model predictions</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div><dt className="text-sand-500">Chance next question feels tricky</dt><dd className="font-display text-2xl font-semibold text-maroon-800">{pct(a.ml.struggle_probability)}</dd><dd className="text-xs text-sand-500">{a.ml.struggle_source === "model" ? "logistic regression" : "heuristic fallback"} · {a.ml.struggle_version}</dd></div>
            <div><dt className="text-sand-500">Chance of staying engaged (5+ min)</dt><dd className="font-display text-2xl font-semibold text-maroon-800">{pct(a.ml.engagement_probability)}</dd><dd className="text-xs text-sand-500">{a.ml.engagement_source}</dd></div>
          </dl>
        </div>
        <div className="card p-6">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-maroon-800"><Users size={18} aria-hidden /> Learning-behaviour profile</h2>
          {a.ml.learner_profile ? (
            <>
              <p className="mt-3 font-display text-2xl font-semibold text-maroon-700">{a.ml.learner_profile.name}</p>
              <p className="text-sm text-cocoa-soft">{a.ml.learner_profile.description}</p>
              <p className="mt-2 text-xs text-sand-500">K-means cluster · separation confidence {pct(a.ml.learner_profile.confidence)}. Describes recent behaviour only - it changes as the learner does.</p>
            </>
          ) : (
            <p className="mt-3 text-sm text-cocoa-soft">Needs at least 10 answered questions.</p>
          )}
        </div>
        <div className="card p-6">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-maroon-800"><Info size={18} aria-hidden /> Model card</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-3"><dt className="text-sand-500">Training data</dt><dd className="text-right font-medium">{a.ml.model_card.data_provenance ? Object.entries(a.ml.model_card.data_provenance).map(([k, v]) => `${k}: ${v}`).join(", ") : "–"}</dd></div>
            <div className="flex justify-between"><dt className="text-sand-500">Struggle ROC-AUC</dt><dd className="font-medium">{a.ml.model_card.struggle_roc_auc ?? "–"}</dd></div>
            <div className="flex justify-between"><dt className="text-sand-500">Engagement ROC-AUC</dt><dd className="font-medium">{a.ml.model_card.engagement_roc_auc ?? "–"}</dd></div>
          </dl>
          {a.ml.model_card.note && <p className="mt-3 rounded-xl bg-cream-100 p-3 text-xs text-maroon-800">{a.ml.model_card.note}</p>}
        </div>
      </section>

      <StudyPlan />

      <p className="flex items-center gap-2 text-xs text-sand-500">
        <ShieldCheck size={14} aria-hidden /> Safety: {a.safety.redirected_or_supported_messages} chat message(s) were redirected or answered with a "talk to a trusted adult" response. Message contents are not shown here.
      </p>
    </div>
  );
}
