import { motion } from "framer-motion";
import { Activity, ArrowDown, BrainCircuit, Gauge, MousePointerClick, Sparkles, Timer, Type, Wand2 } from "lucide-react";
import { Reveal, SectionTitle, stagger } from "@/components/ui";

export function Problem() {
  const items = [
    { icon: Timer, title: "One speed for everyone", text: "Some children need more time to think. Others are ready to race ahead. A fixed pace fits almost nobody." },
    { icon: Type, title: "Walls of text", text: "Long paragraphs and tiny print can make learning feel heavy - especially for children who find reading tiring." },
    { icon: Sparkles, title: "The same hint, every time", text: "When a child is stuck, repeating the same explanation louder doesn't help. A different way often does." },
  ];
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <Reveal>
            <SectionTitle
              eyebrow="The problem"
              title={<>One lesson. Thirty different minds.</>}
              intro="Most learning tools teach every child the same way. But children notice patterns, read, focus and remember differently - and that's a strength, not a problem to fix."
            />
            {/* One path vs many paths */}
            <svg viewBox="0 0 420 150" className="w-full max-w-md" role="img" aria-label="Diagram: a single fixed path compared with many personalised paths">
              <text x="0" y="16" className="fill-sand-500 text-[12px] font-semibold">One-size-fits-all</text>
              <path d="M10 40H190" stroke="#CDC0AF" strokeWidth="6" strokeLinecap="round" />
              {[30, 80, 130, 170].map((x) => (
                <circle key={x} cx={x} cy="40" r="7" fill="#E5DCCF" />
              ))}
              <text x="230" y="16" className="fill-maroon-600 text-[12px] font-semibold">Lumora</text>
              <path d="M230 40C270 40 280 20 320 20S390 30 410 26" stroke="#AE4F5E" strokeWidth="5" fill="none" strokeLinecap="round" />
              <path d="M230 40C270 40 290 60 330 62S390 50 410 56" stroke="#772233" strokeWidth="5" fill="none" strokeLinecap="round" />
              <path d="M230 40C280 40 300 40 340 40S395 42 410 41" stroke="#E9B949" strokeWidth="5" fill="none" strokeLinecap="round" />
              <circle cx="230" cy="40" r="8" fill="#772233" />
              <text x="0" y="100" className="fill-cocoa text-[12px]">Same speed, same words, same hints</text>
              <text x="230" y="100" className="fill-cocoa text-[12px]">Each path adapts as the child learns</text>
            </svg>
          </Reveal>
          <motion.ul className="grid gap-4" variants={stagger.container} initial="hidden" whileInView="show" viewport={{ once: true }}>
            {items.map(({ icon: Ico, title, text }) => (
              <motion.li key={title} variants={stagger.item} className="card group flex gap-4 p-5 transition hover:-translate-y-1 hover:shadow-lift">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cream-200 text-maroon-600 transition-transform group-hover:rotate-6">
                  <Ico aria-hidden />
                </span>
                <div>
                  <h3 className="font-semibold text-maroon-800">{title}</h3>
                  <p className="mt-1 text-cocoa-soft">{text}</p>
                </div>
              </motion.li>
            ))}
          </motion.ul>
        </div>
      </div>
    </section>
  );
}

export function HowItWorks() {
  const steps = [
    { icon: MousePointerClick, title: "Student interaction", text: "Answers, hints, re-reads, skips, time spent." },
    { icon: Activity, title: "Behaviour signals", text: "Accuracy, pace, hint use, confidence, streaks." },
    { icon: BrainCircuit, title: "Learning models", text: "Mastery tracing + struggle & engagement prediction." },
    { icon: Gauge, title: "Adaptive engine", text: "Chooses difficulty, style, hints, examples, pacing." },
    { icon: Wand2, title: "Personalised lesson", text: "The same idea, explained the way this child needs." },
  ];
  return (
    <section id="how" className="scroll-mt-20 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle center eyebrow="How it works" title="A tutor that learns how you learn" intro="Every interaction is a tiny clue. Lumora turns those clues into a teaching plan - in real time, on our servers, with every decision explainable." />
        </Reveal>
        <motion.ol className="grid gap-4 md:grid-cols-5" variants={stagger.container} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-80px" }}>
          {steps.map(({ icon: Ico, title, text }, i) => (
            <motion.li key={title} variants={stagger.item} className="relative">
              <div className="card h-full p-5 text-center transition hover:-translate-y-1 hover:shadow-lift">
                <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-maroon-600 text-cream-50 shadow-soft">
                  <Ico aria-hidden />
                </span>
                <p className="mt-1 text-xs font-semibold text-sand-400">Step {i + 1}</p>
                <h3 className="mt-2 font-semibold text-maroon-800">{title}</h3>
                <p className="mt-1 text-sm text-cocoa-soft">{text}</p>
              </div>
              {i < steps.length - 1 && (
                <ArrowDown className="mx-auto my-1 text-maroon-300 md:absolute md:-right-4 md:top-1/2 md:my-0 md:-translate-y-1/2 md:-rotate-90" size={22} aria-hidden />
              )}
            </motion.li>
          ))}
        </motion.ol>
      </div>
    </section>
  );
}
