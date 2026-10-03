import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Accessibility, AlertTriangle, BookOpenCheck, Check, Trash2, UserRound } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { usePrefs } from "@/lib/prefs";
import { useSubjects } from "@/hooks/queries";
import type { Preferences, User } from "@/lib/types";
import { Toggle } from "@/components/ui";

const AVATARS = ["star", "owl", "rocket", "leaf", "book", "sun"] as const;
const AVATAR_EMOJI: Record<string, string> = { star: "⭐", owl: "🦉", rocket: "🚀", leaf: "🍃", book: "📘", sun: "🌞" };

function Choice<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: { v: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <fieldset className="py-3">
      <legend className="font-medium">{label}</legend>
      <div className="mt-2 flex flex-wrap gap-2">
        {options.map((o) => (
          <button key={o.v} type="button" onClick={() => onChange(o.v)} aria-pressed={value === o.v}
            className={clsx("btn border px-4 py-2 text-sm", value === o.v ? "border-maroon-600 bg-maroon-600 text-cream-50" : "border-sand-200 bg-white hover:bg-cream-100")}>
            {o.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export default function SettingsPage() {
  const { user, setUser, logout } = useAuth();
  const { prefs, update, saving } = usePrefs();
  const subjects = useSubjects();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.display_name ?? "");
  const [confirm, setConfirm] = useState("");
  useEffect(() => { document.title = "Settings · Lumora"; }, []);

  const saveProfile = useMutation({
    mutationFn: (patch: Record<string, unknown>) => api<User>("/api/profile", { method: "PUT", json: patch }),
    onSuccess: setUser,
  });
  const del = useMutation({
    mutationFn: () => api("/api/me", { method: "DELETE" }),
    onSuccess: async () => { await logout().catch(() => undefined); navigate("/"); },
  });
  const set = (patch: Partial<Preferences>) => void update(patch);
  const submitName = (e: FormEvent) => { e.preventDefault(); if (name.trim()) saveProfile.mutate({ display_name: name.trim() }); };
  if (!user) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <p className="eyebrow">Settings</p>
        <h1 className="h-display mt-2 text-3xl sm:text-4xl">Make Lumora feel just right</h1>
        <p className="mt-2 text-cocoa-soft">Changes save automatically and help Divi choose how to teach you. {saving && <span className="text-sand-500">Saving…</span>}</p>
      </header>

      <section className="card p-6" aria-labelledby="profile-h">
        <h2 id="profile-h" className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><UserRound size={20} aria-hidden /> Profile</h2>
        <form onSubmit={submitName} className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="display-name" className="mb-1.5 block text-sm font-medium">Display name</label>
            <input id="display-name" className="input" value={name} onChange={(e) => setName(e.target.value)} maxLength={40} />
          </div>
          <button className="btn-secondary" disabled={saveProfile.isPending}>{saveProfile.isSuccess ? <><Check size={16} aria-hidden /> Saved</> : "Save name"}</button>
        </form>
        <fieldset className="mt-5">
          <legend className="text-sm font-medium">Choose your avatar</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {AVATARS.map((a) => (
              <button key={a} type="button" onClick={() => saveProfile.mutate({ avatar: a })} aria-pressed={user.avatar === a} aria-label={a}
                className={clsx("flex h-14 w-14 items-center justify-center rounded-2xl border-2 text-2xl transition", user.avatar === a ? "border-maroon-600 bg-cream-200" : "border-sand-200 bg-white hover:border-maroon-300")}>
                <span aria-hidden>{AVATAR_EMOJI[a]}</span>
              </button>
            ))}
          </div>
        </fieldset>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="fav" className="mb-1.5 block text-sm font-medium">Favourite subject</label>
            <select id="fav" className="input" value={user.favorite_subject_id ?? ""} onChange={(e) => saveProfile.mutate({ favorite_subject_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">No favourite yet</option>
              {subjects.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="week" className="mb-1.5 block text-sm font-medium">Gentle weekly goal: {user.weekly_goal_days} days</label>
            <input id="week" type="range" min={1} max={7} value={user.weekly_goal_days} onChange={(e) => saveProfile.mutate({ weekly_goal_days: Number(e.target.value) })} className="mt-3 w-full accent-maroon-600" />
          </div>
        </div>
      </section>

      <section className="card p-6" aria-labelledby="learning-h">
        <h2 id="learning-h" className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><BookOpenCheck size={20} aria-hidden /> How I like to learn</h2>
        <div className="divide-y divide-sand-100">
          <Choice label="Explanations" value={prefs.explanation_length} onChange={(v) => set({ explanation_length: v })}
            options={[{ v: "short", label: "Short" }, { v: "medium", label: "Medium" }, { v: "detailed", label: "Detailed" }]} />
          <Choice label="Pace" value={prefs.pace} onChange={(v) => set({ pace: v })}
            options={[{ v: "relaxed", label: "Relaxed" }, { v: "steady", label: "Steady" }, { v: "quick", label: "Quick" }]} />
          <Toggle label="More examples" description="Show extra worked examples." checked={prefs.prefers_examples} onChange={(v) => set({ prefers_examples: v })} />
          <Toggle label="Pictures & analogies" description="Use visual explanations when possible." checked={prefs.prefers_visuals} onChange={(v) => set({ prefers_visuals: v })} />
        </div>
      </section>

      <section className="card p-6" aria-labelledby="a11y-h">
        <h2 id="a11y-h" className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><Accessibility size={20} aria-hidden /> Reading & accessibility</h2>
        <div className="divide-y divide-sand-100">
          <div className="py-3">
            <label htmlFor="ts" className="font-medium">Text size: {Math.round(prefs.text_scale * 100)}%</label>
            <input id="ts" type="range" min={0.9} max={1.5} step={0.05} value={prefs.text_scale} onChange={(e) => set({ text_scale: Number(e.target.value) })} className="mt-2 w-full accent-maroon-600" />
          </div>
          <div className="py-3">
            <label htmlFor="ls" className="font-medium">Line spacing: {prefs.line_spacing.toFixed(2)}</label>
            <input id="ls" type="range" min={1.4} max={2.2} step={0.05} value={prefs.line_spacing} onChange={(e) => set({ line_spacing: Number(e.target.value) })} className="mt-2 w-full accent-maroon-600" />
          </div>
          <Toggle label="Readable font" description="Atkinson Hyperlegible - designed so letters are easy to tell apart." checked={prefs.readable_font} onChange={(v) => set({ readable_font: v })} />
          <Toggle label="Suggest read-aloud" description="Divi will offer to read lessons out loud." checked={prefs.read_aloud} onChange={(v) => set({ read_aloud: v })} />
          <Toggle label="Reduce motion" description="Turn off animations and moving decorations." checked={prefs.reduced_motion} onChange={(v) => set({ reduced_motion: v })} />
          <Toggle label="Focus mode" description="Hide extra panels and decorations while learning." checked={prefs.focus_mode} onChange={(v) => set({ focus_mode: v })} />
          <Toggle label="Extra contrast" description="Stronger text and borders." checked={prefs.high_contrast} onChange={(v) => set({ high_contrast: v })} />
        </div>
        <p className="reading mt-4 rounded-2xl bg-cream-100 p-4">Preview: The water cycle is like a giant recycling machine - the same water gets used again and again!</p>
      </section>

      <section className="rounded-xl2 border border-maroon-200 bg-maroon-50/50 p-6" aria-labelledby="privacy-h">
        <h2 id="privacy-h" className="flex items-center gap-2 font-display text-xl font-semibold text-maroon-800"><AlertTriangle size={20} aria-hidden /> Privacy</h2>
        <p className="mt-2 text-sm text-cocoa-soft">Deleting the account permanently removes the profile, progress, quiz history, chats and uploaded documents.</p>
        <label htmlFor="confirm" className="mt-4 block text-sm font-medium">Type DELETE to confirm</label>
        <div className="mt-1.5 flex flex-col gap-2 sm:flex-row">
          <input id="confirm" className="input" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          <button className="btn shrink-0 bg-maroon-700 text-cream-50 hover:bg-maroon-800" disabled={confirm !== "DELETE" || del.isPending} onClick={() => del.mutate()}>
            <Trash2 size={16} aria-hidden /> Delete account
          </button>
        </div>
      </section>
    </div>
  );
}
