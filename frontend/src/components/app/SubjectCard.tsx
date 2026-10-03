import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { SubjectArt } from "../illustrations/SubjectArt";
import { ProgressRing } from "../ui";
import { STAGE_LABEL, masteryWords } from "@/lib/format";
import type { SubjectSummary } from "@/lib/types";

const BLURB: Record<string, string> = {
  mathematics: "Numbers, patterns and shapes",
  science: "Living things, Earth and space",
  reading: "Stories, words and big ideas",
  history: "Travel back in time",
};

/** Subject card: hover OR keyboard focus reveals progress + the next activity. */
export function SubjectCard({ subject }: { subject: SubjectSummary }) {
  const next = subject.next_topic;
  return (
    <motion.article
      whileHover={{ y: -6 }}
      transition={{ type: "spring", stiffness: 300, damping: 22 }}
      className="group card relative flex flex-col overflow-hidden focus-within:ring-4 focus-within:ring-maroon-100"
    >
      <div className="overflow-hidden bg-cream-100 px-5 pt-5">
        <div className="transition-transform duration-500 group-hover:-translate-y-1 group-hover:scale-[1.04]">
          <SubjectArt slug={subject.slug} />
        </div>
      </div>
      <div className="flex flex-1 flex-col p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-xl font-semibold text-maroon-800">{subject.name}</h3>
            <p className="text-sm text-sand-500">{subject.description ?? BLURB[subject.slug]}</p>
          </div>
          <ProgressRing value={subject.progress} size={56} stroke={6} label={<span className="text-xs">{Math.round(subject.progress * 100)}%</span>} />
        </div>
        <div className="mt-4 grid grid-rows-[0fr] transition-all duration-300 group-hover:grid-rows-[1fr] group-focus-within:grid-rows-[1fr]">
          <div className="overflow-hidden">
            <div className="rounded-2xl bg-cream-100 p-3 text-sm">
              <p className="text-cocoa-soft">
                {subject.practiced_topics} of {subject.topic_count} topics practised
              </p>
              {next && (
                <p className="mt-1">
                  <span className="font-semibold text-maroon-700">Next: {next.title}</span>
                  <span className="text-sand-500"> · {next.attempts ? masteryWords(next.mastery) : STAGE_LABEL[next.stage]}</span>
                </p>
              )}
            </div>
          </div>
        </div>
        {next?.lesson_id && (
          <Link to={`/app/lesson/${next.lesson_id}`} className="btn-secondary mt-4 self-start text-sm">
            {next.attempts ? "Keep going" : "Start exploring"} <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" aria-hidden />
            <span className="sr-only"> with {next.title}</span>
          </Link>
        )}
      </div>
    </motion.article>
  );
}
