/**
 * Real-time interaction tracking. Events are batched and flushed every few
 * seconds (and when the tab is hidden) to POST /api/interactions, where they
 * feed the adaptive engine. Only learning signals are sent - never free text.
 */
import { api, tokenStore } from "./api";

export type TrackedEvent =
  | "section_viewed"
  | "read_aloud_used"
  | "break_taken"
  | "answer_changed"
  | "explanation_requested";

interface QueuedEvent {
  event_type: TrackedEvent;
  topic_id?: number | null;
  lesson_id?: number | null;
  question_id?: number | null;
  payload?: Record<string, string | number | boolean>;
}

const queue: QueuedEvent[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;

async function flush() {
  timer = null;
  if (!queue.length || !tokenStore.get()) {
    queue.length = 0;
    return;
  }
  const events = queue.splice(0, 50);
  try {
    await api("/api/interactions", { method: "POST", json: { events } });
  } catch {
    /* tracking must never interrupt learning */
  }
}

export function track(event: QueuedEvent) {
  queue.push(event);
  if (!timer) timer = setTimeout(flush, 4000);
}

if (typeof document !== "undefined") {
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") void flush();
  });
}

export const _testing = { queue, flush };
