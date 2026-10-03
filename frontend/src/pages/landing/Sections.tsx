import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Accessibility,
  BarChart3,
  BookMarked,
  BrainCircuit,
  Database,
  FileText,
  Focus,
  HeartHandshake,
  Keyboard,
  LineChart,
  ListChecks,
  Lock,
  MessageCircleHeart,
  Puzzle,
  ScanSearch,
  ShieldCheck,
  Sigma,
  Sparkles,
  Split,
  Target,
  TrendingUp,
  Type,
  Users,
  Volume2,
} from "lucide-react";
import { Reveal, SectionTitle, stagger } from "@/components/ui";
import { JourneyPath } from "@/components/illustrations/JourneyPath";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { LogoMark } from "@/components/brand/Logo";
import { usePrefs } from "@/lib/prefs";

export function Journey() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle center eyebrow="A learning journey" title="From first try to “I've got this!”" intro="Every topic moves through gentle stages. Signed-in learners see their real position, calculated from their own mastery data." />
        </Reveal>
        <Reveal className="card-sunny px-4 py-10 sm:px-10">
          <JourneyPath current="practice" />
          <p className="mt-6 text-center text-xs text-sand-500">Example journey shown. No streak pressure - rest days are part of learning.</p>
        </Reveal>
      </div>
    </section>
  );
}

const FEATURES = [
  { icon: MessageCircleHeart, title: "Adaptive tutoring", text: "Divi changes explanation style, length and hints for each learner." },
  { icon: Sparkles, title: "AI explanations", text: "Structured, safety-checked answers from a pluggable LLM layer (or offline demo mode)." },
  { icon: ScanSearch, title: "RAG-powered learning", text: "Answers are grounded in real lesson material and your own notes - with sources shown." },
  { icon: Puzzle, title: "Personalised quizzes", text: "Difficulty, length, answer choices and review questions picked for you." },
  { icon: BarChart3, title: "Learning analytics", text: "Mastery, accuracy and engagement trends for parents and teachers." },
  { icon: Target, title: "Smart recommendations", text: "What to learn, practise or review next - ranked and explained." },
  { icon: TrendingUp, title: "Progress tracking", text: "Progress rings, a learning journey and encouraging achievements." },
  { icon: Accessibility, title: "Accessibility first", text: "Text size, readable font, read-aloud, focus mode and reduced motion." },
];

export function Features() {
  return (
    <section id="features" className="scroll-mt-20 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle eyebrow="Features" title="Everything a curious learner needs" intro="Friendly on the surface. Serious engineering underneath." />
        </Reveal>
        <motion.ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" variants={stagger.container} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }}>
          {FEATURES.map(({ icon: Ico, title, text }) => (
            <motion.li key={title} variants={stagger.item} className="card group p-6 transition duration-300 hover:-translate-y-1.5 hover:shadow-lift">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cream-200 text-maroon-600 transition-transform duration-300 group-hover:-translate-y-1 group-hover:rotate-[-6deg]">
                <Ico aria-hidden />
              </span>
              <h3 className="mt-4 font-semibold text-maroon-800">{title}</h3>
              <p className="mt-1.5 text-sm text-cocoa-soft">{text}</p>
            </motion.li>
          ))}
        </motion.ul>
      </div>
    </section>
  );
}

export function RagSection() {
  const steps = [
    { icon: FileText, label: "Learning material", sub: "Lessons, notes, PDFs" },
    { icon: Split, label: "Chunking", sub: "Section-aware, overlapping" },
    { icon: Sigma, label: "Embeddings", sub: "384-dim vectors" },
    { icon: Database, label: "pgvector", sub: "HNSW cosine index" },
    { icon: ScanSearch, label: "Retrieval", sub: "Hybrid re-ranking" },
    { icon: MessageCircleHeart, label: "Grounded answer", sub: "With cited sources" },
  ];
  return (
    <section className="bg-maroon-800 py-20 text-cream-50 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <p className="eyebrow text-cream-300">Retrieval-augmented generation</p>
          <h2 className="mt-3 max-w-2xl font-display text-3xl font-semibold sm:text-4xl">Answers that come from real lessons - not guesses</h2>
          <p className="mt-4 max-w-2xl text-lg text-maroon-100">
            Before Divi answers, Lumora searches the learning library (and any notes the learner uploads) in PostgreSQL with pgvector, then
            hands the most relevant passages to the AI. The sources are shown right under the answer.
          </p>
        </Reveal>
        <motion.ol className="mt-12 grid gap-3 sm:grid-cols-3 lg:grid-cols-6" variants={stagger.container} initial="hidden" whileInView="show" viewport={{ once: true }}>
          {steps.map(({ icon: Ico, label, sub }, i) => (
            <motion.li key={label} variants={stagger.item} className="relative rounded-2xl border border-maroon-600 bg-maroon-700/60 p-4">
              <span className="text-xs font-semibold text-cream-400">0{i + 1}</span>
              <Ico className="mt-2 text-cream-300" aria-hidden />
              <p className="mt-2 font-semibold">{label}</p>
              <p className="text-xs text-maroon-200">{sub}</p>
            </motion.li>
          ))}
        </motion.ol>
        <Reveal className="mt-10 max-w-xl rounded-2xl bg-cream-50 p-5 text-cocoa">
          <div className="flex items-start gap-3">
            <DiviAvatar size={44} />
            <div>
              <p>Plants make food using sunlight, water and carbon dioxide - the green chlorophyll in leaves catches the light!</p>
              <p className="mt-3 flex flex-wrap gap-2 text-xs">
                <span className="chip bg-cream-200 text-maroon-800"><BookMarked size={12} aria-hidden /> Photosynthesis: A Plant's Kitchen · Key idea</span>
                <span className="chip bg-cream-200 text-maroon-800"><BookMarked size={12} aria-hidden /> Step by step</span>
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export function MLSection() {
  const models = [
    { icon: Target, title: "Mastery tracing", model: "Bayesian Knowledge Tracing", text: "Estimates how well each topic is known after every answer - hints and guess chance included." },
    { icon: BrainCircuit, title: "Struggle prediction", model: "Logistic regression", text: "Predicts when the next question may feel tricky, using mastery, pace, hints and confidence." },
    { icon: LineChart, title: "Engagement", model: "Model selected on validation data", text: "Spots when a brain break might help, so sessions stay comfortable." },
    { icon: Users, title: "Learning profiles", model: "K-means clustering", text: "Groups behaviour patterns (e.g. “Careful Thinker”) for grown-ups - never shown as labels to children." },
    { icon: TrendingUp, title: "Trend analysis", model: "Least-squares slope", text: "Detects improving or dipping accuracy to adjust challenge." },
    { icon: ListChecks, title: "Recommendations", model: "Interpretable ranking", text: "Balances mastery gaps, spaced repetition and readiness." },
  ];
  return (
    <section className="py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle
            eyebrow="Machine learning"
            title="Interpretable models, honest about their limits"
            intro="Lumora uses simple, explainable models trained on its own interaction data. On a fresh install they start from clearly-labelled synthetic data, then retrain on real interactions - and every metric is reported next to a baseline."
          />
        </Reveal>
        <motion.ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" variants={stagger.container} initial="hidden" whileInView="show" viewport={{ once: true }}>
          {models.map(({ icon: Ico, title, model, text }) => (
            <motion.li key={title} variants={stagger.item} className="card p-6 transition hover:-translate-y-1 hover:shadow-lift">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-maroon-600 text-cream-50"><Ico size={20} aria-hidden /></span>
                <div>
                  <h3 className="font-semibold text-maroon-800">{title}</h3>
                  <p className="text-xs font-medium text-sand-500">{model}</p>
                </div>
              </div>
              <p className="mt-3 text-sm text-cocoa-soft">{text}</p>
            </motion.li>
          ))}
        </motion.ul>
      </div>
    </section>
  );
}

export function AnalyticsSection() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-2">
        <Reveal>
          <SectionTitle
            eyebrow="Two views, one platform"
            title="Simple for children. Detailed for grown-ups."
            intro="Children see encouragement and what to do next. Parents and teachers get a separate Insights view with mastery curves, accuracy trends, engine decisions and model transparency."
          />
        </Reveal>
        <Reveal className="grid gap-4 sm:grid-cols-2" aria-label="Illustration of the child view and the grown-up view">
          <div className="card-sunny p-5" role="img" aria-label="Child view illustration">
            <p className="text-xs font-semibold uppercase tracking-wider text-maroon-500">Child view</p>
            <div className="mt-3 flex items-center gap-3">
              <DiviAvatar size={44} mood="celebrating" />
              <p className="font-semibold text-maroon-800">You're getting really good at this!</p>
            </div>
            <div className="mt-4 h-3 rounded-full bg-white"><div className="h-full w-2/3 rounded-full bg-maroon-500" /></div>
            <p className="mt-2 text-xs text-sand-500">Next: practise fractions ✨</p>
          </div>
          <div className="card p-5" role="img" aria-label="Grown-up view illustration">
            <p className="text-xs font-semibold uppercase tracking-wider text-maroon-500">Grown-up view</p>
            <svg viewBox="0 0 200 90" className="mt-3 w-full" aria-hidden="true">
              <path d="M0 80H200" stroke="#E5DCCF" />
              <path d="M0 70C30 66 50 58 80 52S140 30 200 18" stroke="#772233" strokeWidth="3" fill="none" />
              <path d="M0 76C40 72 70 70 100 62S160 50 200 44" stroke="#E9B949" strokeWidth="3" fill="none" strokeDasharray="5 4" />
            </svg>
            <p className="mt-2 text-xs text-sand-500">Mastery & accuracy trends · engine decisions · model card</p>
          </div>
          <p className="text-xs text-sand-500 sm:col-span-2">Illustration only - real dashboards show each learner's own data.</p>
        </Reveal>
      </div>
    </section>
  );
}

export function AccessibilitySection() {
  const { prefs, update } = usePrefs();
  const items = [
    { icon: Type, text: "Adjustable text size and line spacing" },
    { icon: BookMarked, text: "Highly readable font option (Atkinson Hyperlegible)" },
    { icon: Volume2, text: "Read-aloud for lessons and answers" },
    { icon: Focus, text: "Focus mode hides distractions" },
    { icon: Sparkles, text: "Reduced motion, respecting system settings" },
    { icon: Keyboard, text: "Full keyboard navigation and visible focus" },
  ];
  return (
    <section className="py-20 sm:py-24">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-2">
        <Reveal>
          <SectionTitle eyebrow="Accessibility" title="Designed so every child can take part" intro="Accessibility isn't a setting buried in a menu - it shapes every screen. Try it right here:" />
          <ul className="grid gap-3 sm:grid-cols-2">
            {items.map(({ icon: Ico, text }) => (
              <li key={text} className="flex items-start gap-3 text-cocoa">
                <Ico className="mt-0.5 shrink-0 text-maroon-500" size={20} aria-hidden /> {text}
              </li>
            ))}
          </ul>
        </Reveal>
        <Reveal className="card p-6 sm:p-8">
          <p className="font-semibold text-maroon-800">Try it: personalise this page</p>
          <div className="mt-5 space-y-5">
            <div>
              <label htmlFor="demo-text-size" className="text-sm font-medium">Text size: {Math.round(prefs.text_scale * 100)}%</label>
              <input id="demo-text-size" type="range" min={0.9} max={1.4} step={0.05} value={prefs.text_scale} onChange={(e) => update({ text_scale: Number(e.target.value) })} className="mt-2 w-full accent-maroon-600" />
            </div>
            <div className="flex flex-wrap gap-2">
              <button className={prefs.readable_font ? "btn-primary" : "btn-secondary"} aria-pressed={prefs.readable_font} onClick={() => update({ readable_font: !prefs.readable_font })}>
                Readable font
              </button>
              <button className={prefs.reduced_motion ? "btn-primary" : "btn-secondary"} aria-pressed={prefs.reduced_motion} onClick={() => update({ reduced_motion: !prefs.reduced_motion })}>
                Reduce motion
              </button>
              <button className={prefs.high_contrast ? "btn-primary" : "btn-secondary"} aria-pressed={prefs.high_contrast} onClick={() => update({ high_contrast: !prefs.high_contrast })}>
                Extra contrast
              </button>
            </div>
            <p className="reading rounded-2xl bg-cream-100 p-4 text-cocoa">
              A fraction shows how many equal parts of a whole you have. The bottom number tells how many equal parts there are.
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export function Responsible() {
  const items = [
    { icon: ShieldCheck, title: "Not a diagnostic tool", text: "Lumora supports learning preferences. It never diagnoses ADHD, dyslexia, autism or any condition, and the tutor won't either." },
    { icon: HeartHandshake, title: "Safe AI for children", text: "Inputs and outputs are safety-screened. Divi stays on learning, refuses unsafe topics and points to trusted adults when a child seems upset." },
    { icon: Lock, title: "Private by design", text: "No birthdays, schools or locations collected. Personal details typed into chat are removed before reaching the AI. Accounts can be deleted anytime." },
  ];
  return (
    <section className="bg-cream-100 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle center eyebrow="Responsible by design" title="Kind, safe and honest" />
        </Reveal>
        <div className="grid gap-4 md:grid-cols-3">
          {items.map(({ icon: Ico, title, text }, i) => (
            <Reveal key={title} delay={i * 0.08} className="card h-full p-6">
              <Ico className="text-maroon-600" aria-hidden />
              <h3 className="mt-3 font-semibold text-maroon-800">{title}</h3>
              <p className="mt-1.5 text-sm text-cocoa-soft">{text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Technology() {
  const groups = [
    { title: "Frontend", items: ["React 18", "TypeScript", "Vite", "Tailwind CSS", "TanStack Query", "Recharts", "Framer Motion"] },
    { title: "Backend", items: ["Python", "FastAPI", "Pydantic", "SQLAlchemy 2", "Alembic", "JWT + bcrypt"] },
    { title: "Data & AI", items: ["PostgreSQL", "pgvector (HNSW)", "RAG", "OpenAI / Anthropic / Demo", "Structured outputs"] },
    { title: "ML & Ops", items: ["scikit-learn", "pandas", "NumPy", "Pytest", "Docker", "GitHub Actions"] },
  ];
  return (
    <section id="technology" className="scroll-mt-20 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal>
          <SectionTitle center eyebrow="Technology" title="AI + ML + RAG, built on a real full-stack foundation" />
        </Reveal>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {groups.map((g, i) => (
            <Reveal key={g.title} delay={i * 0.06} className="card h-full p-6">
              <h3 className="font-semibold text-maroon-800">{g.title}</h3>
              <ul className="mt-3 flex flex-wrap gap-2">
                {g.items.map((t) => (
                  <li key={t} className="chip bg-sand-100 text-sand-600">{t}</li>
                ))}
              </ul>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function CTA() {
  return (
    <section className="px-4 pb-24 sm:px-6">
      <Reveal className="relative mx-auto max-w-5xl overflow-hidden rounded-[2rem] bg-maroon-700 px-6 py-14 text-center text-cream-50 shadow-lift sm:px-12">
        <div className="absolute -left-10 -top-10 opacity-20" aria-hidden="true"><LogoMark size={220} /></div>
        <DiviAvatar size={80} mood="celebrating" className="mx-auto" />
        <h2 className="mt-4 font-display text-3xl font-semibold sm:text-4xl">Ready to learn your way?</h2>
        <p className="mx-auto mt-3 max-w-xl text-maroon-100">Create a free account, pick a subject and let Divi figure out how to help you shine.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/signup" className="btn-sunny px-7 py-3 text-base">Start learning</Link>
          <Link to="/login" className="btn border border-maroon-400 px-7 py-3 text-base text-cream-50 hover:bg-maroon-600">I already have an account</Link>
        </div>
      </Reveal>
    </section>
  );
}
