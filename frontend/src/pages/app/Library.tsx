import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { BookMarked, CheckCircle2, Database, FileText, Loader2, Search, Sparkles, Trash2, Upload, XCircle } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useDocuments, useTopics } from "@/hooks/queries";
import type { DocumentItem } from "@/lib/types";
import { EmptyState, ErrorState, PageSkeleton } from "@/components/ui";

interface SearchHit { chunk_id: number; document_id: number; document_title: string; section: string | null; text: string; score: number }

function DocRow({ d }: { d: DocumentItem }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const refresh = () => qc.invalidateQueries({ queryKey: ["documents"] });
  const detail = useQuery({ queryKey: ["document", d.id, d.chunk_count], queryFn: () => api<DocumentItem>(`/api/documents/${d.id}`), enabled: open });
  const ingest = useMutation({ mutationFn: () => api(`/api/documents/${d.id}/ingest`, { method: "POST" }), onSuccess: refresh });
  const remove = useMutation({ mutationFn: () => api(`/api/documents/${d.id}`, { method: "DELETE" }), onSuccess: refresh });
  const summary = useMutation({ mutationFn: () => api<{ summary: string; key_points: string[]; is_demo: boolean }>(`/api/documents/${d.id}/summary`, { method: "POST" }) });

  return (
    <li className="card p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className={clsx("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl", d.source === "system" ? "bg-cream-200 text-maroon-700" : "bg-maroon-600 text-cream-50")}>
            {d.source === "system" ? <BookMarked size={20} aria-hidden /> : <FileText size={20} aria-hidden />}
          </span>
          <div>
            <p className="font-semibold text-maroon-800">{d.title}</p>
            <p className="text-xs text-sand-500">
              {d.source === "system" ? "Lumora lesson" : d.filename} · {d.char_count.toLocaleString()} characters
              {d.status === "ingested" && ` · ${d.chunk_count} chunks indexed`}
            </p>
            <p className="mt-1 text-xs">
              {d.status === "ingested" && <span className="inline-flex items-center gap-1 text-maroon-700"><CheckCircle2 size={13} aria-hidden /> Ready for Divi</span>}
              {d.status === "uploaded" && <span className="text-sand-600">Uploaded - not indexed yet</span>}
              {d.status === "failed" && <span className="inline-flex items-center gap-1 text-maroon-700"><XCircle size={13} aria-hidden /> {d.error}</span>}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {d.owned && d.status !== "ingested" && (
            <button className="btn-primary px-4 py-2 text-sm" onClick={() => ingest.mutate()} disabled={ingest.isPending}>
              {ingest.isPending ? <Loader2 size={16} className="animate-spin" aria-hidden /> : <Database size={16} aria-hidden />} Index for Divi
            </button>
          )}
          <button className="btn-ghost px-3 py-2 text-sm" onClick={() => setOpen((o) => !o)} aria-expanded={open}>{open ? "Hide" : "View chunks"}</button>
          <button className="btn-ghost px-3 py-2 text-sm" onClick={() => summary.mutate()} disabled={summary.isPending}><Sparkles size={15} aria-hidden /> Summary</button>
          {d.owned && (
            <button className="btn-ghost px-3 py-2 text-sm" onClick={() => remove.mutate()} aria-label={`Delete ${d.title}`}><Trash2 size={15} aria-hidden /></button>
          )}
        </div>
      </div>
      {summary.data && (
        <div className="mt-4 rounded-2xl bg-cream-100 p-4 text-sm">
          <p>{summary.data.summary}</p>
          <ul className="mt-2 space-y-1 text-cocoa-soft">{summary.data.key_points.map((k) => <li key={k}>• {k}</li>)}</ul>
          {summary.data.is_demo && <p className="mt-2 text-xs text-sand-500">Demo mode summary (extractive)</p>}
        </div>
      )}
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            {detail.isLoading ? <p className="mt-3 text-sm text-sand-500">Loading…</p> : (
              <ol className="mt-4 grid gap-2 md:grid-cols-2">
                {detail.data?.chunks?.length ? detail.data.chunks.map((c) => (
                  <li key={c.index} className="rounded-xl border border-sand-200 bg-sand-50 p-3 text-xs">
                    <p className="font-semibold text-maroon-700">Chunk {c.index + 1}{c.section ? ` · ${c.section}` : ""} · {c.words} words</p>
                    <p className="mt-1 text-cocoa-soft">{c.text}</p>
                  </li>
                )) : <li className="text-sm text-sand-500">Not indexed yet.</li>}
              </ol>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}

export default function LibraryPage() {
  const qc = useQueryClient();
  const docs = useDocuments();
  const topics = useTopics();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [topicId, setTopicId] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => { document.title = "My library · Lumora"; }, []);

  const upload = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("file", file!);
      if (title) form.append("title", title);
      if (topicId) form.append("topic_id", topicId);
      const doc = await api<DocumentItem>("/api/documents", { method: "POST", body: form });
      return api<DocumentItem>(`/api/documents/${doc.id}/ingest`, { method: "POST" });
    },
    onSuccess: () => {
      setFile(null); setTitle(""); setTopicId("");
      if (fileRef.current) fileRef.current.value = "";
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
  const search = useMutation({ mutationFn: (q: string) => api<SearchHit[]>(`/api/documents/search?q=${encodeURIComponent(q)}`) });

  const submit = (e: FormEvent) => { e.preventDefault(); if (file) upload.mutate(); };

  if (docs.isLoading) return <PageSkeleton label="Loading your library" />;
  if (docs.isError) return <ErrorState onRetry={() => docs.refetch()} />;
  const mine = docs.data?.filter((d) => d.owned) ?? [];
  const system = docs.data?.filter((d) => !d.owned) ?? [];

  return (
    <div className="space-y-8">
      <header>
        <p className="eyebrow">Library</p>
        <h1 className="h-display mt-2 text-3xl sm:text-4xl">Learn from your own notes</h1>
        <p className="mt-2 max-w-2xl text-cocoa-soft">Add class notes or a worksheet. Lumora splits it into chunks, turns them into vectors and stores them in PostgreSQL + pgvector - so Divi can answer from <em>your</em> material and show its sources.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={submit} className="card space-y-4 p-6">
          <h2 className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><Upload size={20} aria-hidden /> Add learning material</h2>
          <div>
            <label htmlFor="file" className="mb-1.5 block text-sm font-medium">File (.txt, .md or .pdf, up to 5 MB)</label>
            <input id="file" ref={fileRef} type="file" accept=".txt,.md,.markdown,.pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="block w-full rounded-2xl border border-dashed border-maroon-200 bg-cream-50 p-4 text-sm file:mr-4 file:rounded-full file:border-0 file:bg-maroon-600 file:px-4 file:py-2 file:text-cream-50" />
          </div>
          <div>
            <label htmlFor="doc-title" className="mb-1.5 block text-sm font-medium">Title (optional)</label>
            <input id="doc-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} />
          </div>
          <div>
            <label htmlFor="doc-topic" className="mb-1.5 block text-sm font-medium">Topic (optional)</label>
            <select id="doc-topic" className="input" value={topicId} onChange={(e) => setTopicId(e.target.value)}>
              <option value="">No specific topic</option>
              {topics.data?.map((t) => <option key={t.id} value={t.id}>{t.subject.name} · {t.title}</option>)}
            </select>
          </div>
          {upload.isError && <p role="alert" className="rounded-xl bg-maroon-50 p-3 text-sm text-maroon-800">{(upload.error as Error).message}</p>}
          {upload.isSuccess && <p role="status" className="text-sm text-maroon-700">Added and indexed! Divi can now use it.</p>}
          <button className="btn-primary" disabled={!file || upload.isPending}>
            {upload.isPending ? <Loader2 size={18} className="animate-spin" aria-hidden /> : <Upload size={18} aria-hidden />} Upload & index
          </button>
        </form>

        <div className="card space-y-4 p-6">
          <h2 className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><Search size={20} aria-hidden /> Search the library</h2>
          <p className="text-sm text-cocoa-soft">See exactly which passages the retriever finds - this is the context Divi receives.</p>
          <form onSubmit={(e) => { e.preventDefault(); if (query.trim()) search.mutate(query.trim()); }} className="flex gap-2">
            <label htmlFor="lib-q" className="sr-only">Search query</label>
            <input id="lib-q" className="input" placeholder="e.g. how do plants make food?" value={query} onChange={(e) => setQuery(e.target.value)} maxLength={300} />
            <button className="btn-primary shrink-0" disabled={search.isPending}>Search</button>
          </form>
          <ol className="space-y-2" aria-live="polite">
            {search.data?.map((h) => (
              <li key={h.chunk_id} className="rounded-xl border border-cream-300 bg-cream-50 p-3 text-sm">
                <p className="flex justify-between gap-2 font-semibold text-maroon-800"><span>{h.document_title}{h.section ? ` · ${h.section}` : ""}</span><span className="text-xs font-medium text-sand-500">score {h.score.toFixed(2)}</span></p>
                <p className="mt-1 line-clamp-3 text-cocoa-soft">{h.text}</p>
              </li>
            ))}
            {search.data?.length === 0 && <li className="text-sm text-sand-500">No matching passages found.</li>}
          </ol>
        </div>
      </div>

      <section aria-labelledby="mine-title">
        <h2 id="mine-title" className="mb-3 font-display text-2xl font-semibold text-maroon-800">My documents</h2>
        {mine.length === 0 ? (
          <EmptyState title="No notes yet" message="Upload something you're studying and Divi will be able to answer questions about it." />
        ) : (
          <ul className="space-y-3">{mine.map((d) => <DocRow key={d.id} d={d} />)}</ul>
        )}
      </section>

      <section aria-labelledby="sys-title">
        <h2 id="sys-title" className="mb-3 font-display text-2xl font-semibold text-maroon-800">Lumora lesson library</h2>
        <ul className="space-y-3">{system.map((d) => <DocRow key={d.id} d={d} />)}</ul>
      </section>
    </div>
  );
}
