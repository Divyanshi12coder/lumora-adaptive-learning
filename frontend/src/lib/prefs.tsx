import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { MotionConfig } from "framer-motion";
import { api } from "./api";
import { useAuth } from "./auth";
import type { Preferences, User } from "./types";

const LOCAL_KEY = "lumora.prefs";

export const DEFAULT_PREFS: Preferences = {
  explanation_length: "medium",
  prefers_visuals: true,
  prefers_examples: true,
  pace: "steady",
  read_aloud: false,
  readable_font: false,
  text_scale: 1,
  line_spacing: 1.65,
  reduced_motion: false,
  focus_mode: false,
  high_contrast: false,
};

function loadLocal(): Preferences {
  try {
    const raw = localStorage.getItem(LOCAL_KEY);
    return raw ? { ...DEFAULT_PREFS, ...JSON.parse(raw) } : DEFAULT_PREFS;
  } catch {
    return DEFAULT_PREFS;
  }
}

export function applyPreferences(p: Preferences) {
  const root = document.documentElement;
  root.style.setProperty("--text-scale", String(p.text_scale));
  root.style.setProperty("--reading-line-height", String(p.line_spacing));
  root.classList.toggle("font-readable", p.readable_font);
  root.classList.toggle("reduce-motion", p.reduced_motion);
  root.classList.toggle("high-contrast", p.high_contrast);
  root.classList.toggle("focus-mode", p.focus_mode);
}

interface PrefsState {
  prefs: Preferences;
  update: (patch: Partial<Preferences>) => Promise<void>;
  saving: boolean;
}

const PrefsContext = createContext<PrefsState | null>(null);

/** Accessibility + learning preferences. Saved to the learner's profile when signed
 *  in (so the adaptive engine can use them) and to this browser otherwise. */
export function PreferencesProvider({ children }: { children: ReactNode }) {
  const { user, setUser } = useAuth();
  const [prefs, setPrefs] = useState<Preferences>(() => loadLocal());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) setPrefs({ ...DEFAULT_PREFS, ...user.preferences });
  }, [user]);

  useEffect(() => {
    applyPreferences(prefs);
    try {
      localStorage.setItem(LOCAL_KEY, JSON.stringify(prefs));
    } catch {
      /* ignore */
    }
  }, [prefs]);

  const update = useCallback(
    async (patch: Partial<Preferences>) => {
      setPrefs((p) => ({ ...p, ...patch }));
      if (!user) return;
      setSaving(true);
      try {
        const updated = await api<User>("/api/profile", { method: "PUT", json: { preferences: patch } });
        setUser(updated);
      } finally {
        setSaving(false);
      }
    },
    [user, setUser],
  );

  return (
    <PrefsContext.Provider value={{ prefs, update, saving }}>
      <MotionConfig reducedMotion={prefs.reduced_motion ? "always" : "user"}>{children}</MotionConfig>
    </PrefsContext.Provider>
  );
}

export function usePrefs() {
  const ctx = useContext(PrefsContext);
  if (!ctx) throw new Error("usePrefs must be used inside PreferencesProvider");
  return ctx;
}
