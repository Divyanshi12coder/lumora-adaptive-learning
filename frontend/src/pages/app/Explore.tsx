import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { BookOpen, MessageCircleHeart, Puzzle } from "lucide-react";
import clsx from "clsx";
import { useSubjects } from "@/hooks/queries";
import { STAGE_LABEL, masteryWords } from "@/lib/format";
import { SubjectArt } from "@/components/illustrations/SubjectArt";
import { Icon } from "@/components/ui/Icon";
import { ErrorState, PageSkeleton, ProgressRing, stagger } from "@/components/ui";

export default function ExplorePage() {
  const { data, isLoading, isError, refetch } = useSubjects();
  const [active, setActive] = useState<string>("mathematics");
  useEffect(() => { document.title = "Explore · Lumora"; }, []);
  if (isLoading) return <PageSkeleton label="Loading subjects" />;
  if (isError || !data) return <ErrorState onRetry={() => refetch()} />;
  const subject = data.find((s) => s.slug === active) ?? data[0];

  return (
    <div className="space-y-8">
      <header>
        <p className="eyebrow">Explore</p>
        <h1 className="h-display mt-2 text-3xl sm:text-4xl">What would you like to learn?</h1>
        <p className="mt-2 text-cocoa-soft">Pick a subject, then a topic. Divi will shape each lesson and quiz for you.</p>
      </header>

      <div role="tablist" aria-label="Subjects" className="flex gap-2 overflow-x-auto pb-1">
        {data.map((s) => (
          <button
            key={s.slug}
            role="tab"
            id={`tab-${s.slug}`}
            aria-selected={s.slug === subject.slug}
            aria-controls="subject-panel"
            onClick={() => setActive(s.slug)}
            className={clsx(
              "btn shrink-0 border",
              s.slug === subject.slug ? "border-maroon-600 bg-maroon-600 text-cream-50" : "border-sand-200 bg-white text-maroon-800 hover:bg-cream-100",
            )}
          >
            <Icon name={s.icon} size={18} /> {s.name}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.section
          key={subject.slug}
          id="subject-panel"
          role="tabpanel"
          aria-labelledby={`tab-${subject.slug}`}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
        >
          <div className="card-sunny grid items-center gap-6 p-6 md:grid-cols-[220px_1fr]">
            <SubjectArt slug={subject.slug} className="max-w-[220px]" />
            <div>
              <h2 className="font-display text-2xl font-semibold text-maroon-800">{subject.name}</h2>
              <p className="text-cocoa-soft">{subject.description}</p>
              <p className="mt-2 text-sm text-sand-500">{subject.practiced_topics} of {subject.topic_count} topics practised</p>
            </div>
          </div>

          <motion.ul className="mt-6 grid gap-5 md:grid-cols-2 lg:grid-cols-3" variants={stagger.container} initial="hidden" animate="show">
            {subject.topics?.map((t) => (
              <motion.li key={t.id} variants={stagger.item} className="card group flex flex-col p-5 transition hover:-translate-y-1 hover:shadow-lift">
                <div className="flex items-start justify-between gap-3">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cream-200 text-maroon-600 transition-transform group-hover:-rotate-6">
                    <Icon name={t.icon} size={22} />
                  </span>
                  <ProgressRing value={t.mastery} size={58} stroke={6} label={<span className="text-xs">{Math.round(t.mastery * 100)}%</span>} />
                </div>
                <h3 className="mt-3 font-display text-lg font-semibold text-maroon-800">{t.title}</h3>
                <p className="flex-1 text-sm text-cocoa-soft">{t.summary}</p>
                <p className="mt-3 text-xs font-semibold text-maroon-600">{t.attempts ? masteryWords(t.mastery) : STAGE_LABEL[t.stage]}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {t.lesson_id && <Link to={`/app/lesson/${t.lesson_id}`} className="btn-primary px-4 py-2 text-sm"><BookOpen size={16} aria-hidden /> Lesson</Link>}
                  <Link to={`/app/quiz/${t.id}`} className="btn-secondary px-4 py-2 text-sm"><Puzzle size={16} aria-hidden /> Quiz</Link>
                  <Link to={`/app/tutor?topic=${t.id}`} className="btn-ghost px-3 py-2 text-sm" aria-label={`Ask Divi about ${t.title}`}><MessageCircleHeart size={16} aria-hidden /> Ask</Link>
                </div>
              </motion.li>
            ))}
          </motion.ul>
        </motion.section>
      </AnimatePresence>
    </div>
  );
}
