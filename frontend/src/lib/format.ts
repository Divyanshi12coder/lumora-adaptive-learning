import type { Band, Difficulty, Style } from "./types";

export const STYLE_LABEL: Record<Style, string> = {
  step_by_step: "Step-by-step",
  worked_example: "Worked example",
  guided_discovery: "Guided discovery",
  concise: "Short & sharp",
};

export const STYLE_HELP: Record<Style, string> = {
  step_by_step: "Tiny steps, one idea at a time",
  worked_example: "See one solved, then try",
  guided_discovery: "A nudge to figure it out",
  concise: "Quick explanation + challenge",
};

export const DIFF_LABEL: Record<Difficulty, string> = { easy: "Gentle", medium: "Just right", hard: "Challenge" };

export const BAND_LABEL: Record<Band, string> = {
  high_support: "Extra support",
  guided: "Guided practice",
  balanced: "Balanced",
  stretch: "Stretch challenge",
};

export const HINT_LABEL: Record<string, string> = {
  none: "Only if asked",
  light: "Small nudges",
  guided: "Guided clues",
  full: "Full walkthrough",
};

export const LEVEL_LABEL: Record<string, string> = { low: "Light", medium: "Medium", high: "Rich" };

export const STAGE_LABEL: Record<string, string> = {
  discover: "Ready to discover",
  practice: "Practising",
  understand: "Understanding",
  master: "Mastered!",
};

export const pct = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}%`);

export function masteryWords(p: number): string {
  if (p >= 0.85) return "You've mastered this!";
  if (p >= 0.6) return "You're getting really good at this!";
  if (p >= 0.35) return "You're making great progress.";
  if (p > 0) return "You're just getting started.";
  return "Not started yet";
}

export function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
