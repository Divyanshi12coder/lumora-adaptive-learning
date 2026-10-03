import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookMarked, ChevronDown, Info, Lightbulb, MessageSquarePlus, Puzzle, Send, Shuffle, Smile, ThumbsUp, Turtle, Zap } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useTopics } from "@/hooks/queries";
import { DIFF_LABEL, STYLE_LABEL } from "@/lib/format";
import type { ChatMessage, ChatResponse, Style } from "@/lib/types";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { ReadAloud } from "@/components/ui";

const QUICK = [
  { label: "Explain this topic", text: "Can you explain this topic?", intent: "explain", icon: Lightbulb },
  { label: "Give me an easier example", text: "Can you give me an easier example?", intent: "easier", icon: Smile },
  { label: "Give me a hint", text: "Can I have a hint?", intent: "hint", icon: Zap },
  { label: "Quiz me", text: "Quiz me!", intent: "quiz", icon: Puzzle },
  { label: "I don't understand", text: "I don't understand this.", intent: "confused", icon: Turtle },
  { label: "Explain differently", text: "Can you explain it differently?", intent: "different", icon: Shuffle },
] as const;

const FEEDBACK = [
  { value: "helpful", label: "Helpful" },
  { value: "too_long", label: "Too long" },
  { value: "too_hard", label: "Too hard" },
  { value: "too_easy", label: "Too easy" },
] as const;

function Sources({ m }: { m: ChatMessage }) {
  const [open, setOpen] = useState(false);
  if (!m.sources.length) return null;
  const used = m.sources.filter((s) => s.used);
  const list = used.length ? used : m.sources.slice(0, 2);
  return (
    <div className="mt-3">
      <button className="inline-flex items-center gap-1.5 text-xs font-semibold text-maroon-700 hover:underline" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <BookMarked size={14} aria-hidden /> {used.length ? `Based on ${used.length} source${used.length > 1 ? "s" : ""}` : "Related material"}
        <ChevronDown size={14} className={clsx("transition-transform", open && "rotate-180")} aria-hidden />
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mt-2 space-y-2">
            {list.map((s) => (
              <li key={`${s.document_id}-${s.n}`} className="rounded-xl border border-cream-300 bg-cream-50 p-3 text-xs">
                <p className="font-semibold text-maroon-800">
                  [{s.n}] {s.title}{s.section ? ` · ${s.section}` : ""} {s.source === "upload" && <span className="chip ml-1 bg-maroon-50 text-maroon-700">your notes</span>}
                </p>
                <p className="mt-1 text-cocoa-soft">“{s.excerpt}{s.excerpt.length >= 280 ? "…" : ""}”</p>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

function AssistantBubble({ m, onFollowUp }: { m: ChatMessage; onFollowUp: (text: string) => void }) {
  const qc = useQueryClient();
  const [feedback, setFeedback] = useState(m.feedback);
  const fb = useMutation({
    mutationFn: (value: string) => api(`/api/tutor/messages/${m.id}/feedback`, { method: "POST", json: { value } }),
    onSuccess: (_d, value) => { setFeedback(value); qc.invalidateQueries({ queryKey: ["dashboard"] }); },
  });
  const p = m.payload;
  const speech = [m.content, ...(p.steps ?? []), ...(p.examples ?? []), p.check_question ?? ""].join(". ");
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-3">
      <DiviAvatar size={44} mood={m.intent === "safety" ? "encouraging" : "happy"} />
      <div className="min-w-0 max-w-[44rem] flex-1 rounded-3xl rounded-tl-md bg-white p-4 shadow-soft sm:p-5">
        {m.strategy?.explanation_style && (
          <p className="mb-2 flex flex-wrap gap-1.5 text-[0.7rem]" aria-label="How Divi adapted this answer">
            <span className="chip bg-cream-200 text-maroon-800">{STYLE_LABEL[m.strategy.explanation_style as Style]}</span>
            {m.strategy.difficulty && <span className="chip bg-cream-200 text-maroon-800">{DIFF_LABEL[m.strategy.difficulty]}</span>}
            {m.is_demo && <span className="chip bg-sand-100 text-sand-600">Demo mode</span>}
          </p>
        )}
        <p className="reading text-cocoa">{m.content}</p>
        {!!p.steps?.length && (
          <ol className="mt-3 space-y-2">
            {p.steps.map((s, i) => (
              <li key={i} className="flex gap-3 rounded-xl bg-cream-50 p-2.5 text-[0.95rem]">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-maroon-600 text-xs font-bold text-cream-50">{i + 1}</span>{s}
              </li>
            ))}
          </ol>
        )}
        {!!p.examples?.length && (
          <div className="mt-3">
            <p className="text-sm font-semibold text-maroon-700">Example{p.examples.length > 1 ? "s" : ""}</p>
            <ul className="mt-1 space-y-1 text-[0.95rem]">{p.examples.map((e, i) => <li key={i}>✨ {e}</li>)}</ul>
          </div>
        )}
        {p.check_question && (
          <p className="mt-3 rounded-xl border border-maroon-100 bg-maroon-50/50 p-3 text-[0.95rem]"><strong className="text-maroon-700">Try this:</strong> {p.check_question}</p>
        )}
        {p.encouragement && <p className="mt-3 text-sm italic text-maroon-600">{p.encouragement}</p>}
        <Sources m={m} />
        <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-sand-100 pt-3">
          <ReadAloud text={speech} className="min-h-[36px] px-2 text-xs" />
          {m.intent !== "safety" && (
            <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Was this answer helpful?">
              {FEEDBACK.map((f) => (
                <button key={f.value} onClick={() => fb.mutate(f.value)} aria-pressed={feedback === f.value}
                  className={clsx("rounded-full px-3 py-1.5 text-xs font-medium transition-colors", feedback === f.value ? "bg-maroon-600 text-cream-50" : "bg-sand-100 text-sand-600 hover:bg-cream-200")}>
                  {f.value === "helpful" && <ThumbsUp size={12} className="mr-1 inline" aria-hidden />}{f.label}
                </button>
              ))}
            </div>
          )}
        </div>
        {!!p.follow_ups?.length && (
          <div className="mt-3 flex flex-wrap gap-2">
            {p.follow_ups.map((f, i) => (
              <button key={i} className="rounded-full border border-maroon-200 px-3 py-1.5 text-xs font-medium text-maroon-700 hover:bg-maroon-50" onClick={() => onFollowUp(f)}>
                {f}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function TutorPage() {
  const [params] = useSearchParams();
  const qc = useQueryClient();
  const topics = useTopics();
  const [topicId, setTopicId] = useState<number | null>(params.get("topic") ? Number(params.get("topic")) : null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState(params.get("ask") ?? "");
  const [notice, setNotice] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { document.title = "Ask Divi · Lumora"; }, []);

  const history = useQuery({ queryKey: ["conversations"], queryFn: () => api<{ id: number; title: string; topic_id: number | null; updated_at: string }[]>("/api/tutor/history") });

  const send = useMutation({
    mutationFn: (v: { message: string; intent?: string }) =>
      api<ChatResponse>("/api/tutor/chat", { method: "POST", json: { message: v.message, intent: v.intent, topic_id: topicId, conversation_id: conversationId } }),
    onSuccess: (r) => {
      setConversationId(r.conversation_id);
      if (r.topic_id && !topicId) setTopicId(r.topic_id);
      setMessages((m) => [...m.filter((x) => x.id > 0), r.user_message, r.message]);
      setNotice(r.notice);
      qc.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: () => setMessages((m) => m.filter((x) => x.id > 0)),
  });

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, send.isPending]);

  const ask = (message: string, intent?: string) => {
    const text = message.trim();
    if (!text || send.isPending) return;
    setMessages((m) => [...m, { id: -Date.now(), role: "user", content: text, intent: null, payload: {}, sources: [], strategy: null, provider: null, is_demo: false, feedback: null, created_at: null }]);
    setInput("");
    send.mutate({ message: text, intent });
  };
  const submit = (e: FormEvent) => { e.preventDefault(); ask(input); };

  const openConversation = async (id: number) => {
    const c = await api<{ id: number; topic_id: number | null; messages: ChatMessage[] }>(`/api/tutor/history?conversation_id=${id}`);
    setConversationId(c.id);
    setTopicId(c.topic_id);
    setMessages(c.messages);
    setNotice(null);
  };
  const newChat = () => { setConversationId(null); setMessages([]); setNotice(null); };
  const topicTitle = topics.data?.find((t) => t.id === topicId)?.title;

  return (
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <aside className="hidden lg:block" aria-label="Past conversations" data-decorative="true">
        <button className="btn-primary w-full" onClick={newChat}><MessageSquarePlus size={18} aria-hidden /> New chat</button>
        <h2 className="mb-2 mt-6 text-xs font-semibold uppercase tracking-wider text-sand-500">Recent chats</h2>
        <ul className="space-y-1">
          {history.data?.map((c) => (
            <li key={c.id}>
              <button onClick={() => openConversation(c.id)} className={clsx("w-full truncate rounded-xl px-3 py-2 text-left text-sm", c.id === conversationId ? "bg-cream-200 font-medium text-maroon-800" : "hover:bg-cream-100")}>
                {c.title}
              </button>
            </li>
          ))}
          {history.data?.length === 0 && <li className="px-3 text-sm text-sand-500">No chats yet</li>}
        </ul>
      </aside>

      <section className="flex min-h-[70vh] flex-col" aria-label="Chat with Divi">
        <header className="card-sunny flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <DiviAvatar size={52} mood={send.isPending ? "thinking" : "happy"} />
            <div>
              <h1 className="font-display text-xl font-semibold text-maroon-800">Ask Divi</h1>
              <p className="text-xs text-sand-500">Your AI learning guide · I'm an AI, not a person</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="topic" className="sr-only">Topic</label>
            <select id="topic" className="input min-h-[42px] py-2 text-sm sm:w-56" value={topicId ?? ""} onChange={(e) => setTopicId(e.target.value ? Number(e.target.value) : null)}>
              <option value="">Any topic</option>
              {topics.data?.map((t) => <option key={t.id} value={t.id}>{t.subject.name} · {t.title}</option>)}
            </select>
            <button className="btn-ghost px-3 lg:hidden" onClick={newChat} aria-label="New chat"><MessageSquarePlus size={18} aria-hidden /></button>
          </div>
        </header>

        {notice && (
          <p className="mt-3 flex items-center gap-2 rounded-2xl bg-sand-100 px-4 py-2 text-xs text-sand-600"><Info size={14} aria-hidden /> {notice}</p>
        )}

        <div className="flex-1 space-y-5 py-6" aria-live="polite" aria-busy={send.isPending}>
          {messages.length === 0 && (
            <div className="flex flex-col items-center py-8 text-center">
              <DiviAvatar size={96} mood="happy" />
              <p className="mt-4 font-display text-2xl font-semibold text-maroon-800">Hi! What shall we learn{topicTitle ? ` about ${topicTitle}` : ""}?</p>
              <p className="mt-1 max-w-md text-cocoa-soft">Ask me anything about your lessons. I'll explain it the way that works best for you, and show where my answer comes from.</p>
            </div>
          )}
          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="flex justify-end">
                <p className="max-w-[36rem] rounded-3xl rounded-tr-md bg-maroon-600 px-4 py-3 text-cream-50">{m.content}</p>
              </div>
            ) : (
              <AssistantBubble key={m.id} m={m} onFollowUp={(t) => ask(t)} />
            ),
          )}
          {send.isPending && (
            <div className="flex items-center gap-3" role="status">
              <DiviAvatar size={44} mood="thinking" />
              <span className="flex gap-1 rounded-full bg-white px-4 py-3 shadow-soft" aria-label="Divi is thinking">
                {[0, 1, 2].map((i) => (
                  <motion.span key={i} className="h-2 w-2 rounded-full bg-maroon-400" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }} />
                ))}
              </span>
            </div>
          )}
          {send.isError && <p role="alert" className="rounded-2xl bg-maroon-50 p-3 text-sm text-maroon-800">{(send.error as Error).message}</p>}
          <div ref={endRef} />
        </div>

        <div className="sticky bottom-20 space-y-3 rounded-3xl bg-cream-50/95 pb-2 pt-1 backdrop-blur lg:bottom-4">
          <div className="flex gap-2 overflow-x-auto pb-1" aria-label="Suggested questions">
            {QUICK.map(({ label, text, intent, icon: Ico }) => (
              <button key={label} onClick={() => ask(text, intent)} disabled={send.isPending} className="flex shrink-0 items-center gap-1.5 rounded-full border border-sand-200 bg-white px-3.5 py-2 text-sm font-medium text-maroon-800 transition hover:-translate-y-0.5 hover:border-maroon-300">
                <Ico size={15} aria-hidden /> {label}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="flex items-end gap-2">
            <label htmlFor="chat-input" className="sr-only">Your question for Divi</label>
            <textarea
              id="chat-input"
              rows={1}
              className="input max-h-40 min-h-[52px] resize-none"
              placeholder="Type your question…"
              value={input}
              maxLength={800}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(input); } }}
            />
            <button type="submit" className="btn-primary h-[52px] w-[52px] shrink-0 p-0" disabled={!input.trim() || send.isPending} aria-label="Send">
              <Send size={20} aria-hidden />
            </button>
          </form>
          <p className="text-center text-[0.7rem] text-sand-500">Please don't share personal details like your address or phone number. Divi is an AI and can make mistakes.</p>
        </div>
      </section>
    </div>
  );
}
