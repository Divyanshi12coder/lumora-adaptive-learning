/** Typed fetch wrapper. Converts server errors into friendly, child-safe messages. */

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";
const TOKEN_KEY = "lumora.token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string | null) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage unavailable (private mode) - session-only auth still works in memory */
    }
  },
};

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: (() => void) | null) {
  onUnauthorized = fn;
}

function friendly(status: number, detail: unknown): string {
  if (typeof detail === "string" && detail.length < 200) return detail;
  if (status === 0) return "We can't reach Lumora right now. Check your internet and try again.";
  if (status === 401) return "Please sign in to continue.";
  if (status === 404) return "We couldn't find that.";
  if (status === 413) return "That file is too big.";
  if (status === 429) return "Whoa, that's fast! Take a breath and try again in a minute.";
  if (status >= 500) return "Oops! Something went wrong on our side. Please try again.";
  return "Something didn't work. Please try again.";
}

export async function api<T>(path: string, options: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let body = options.body;
  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers, body });
  } catch {
    throw new ApiError(friendly(0, null), 0);
  }
  if (res.status === 204) return undefined as T;
  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!res.ok) {
    if (res.status === 401 && token && onUnauthorized) onUnauthorized();
    const detail = (data as { detail?: unknown } | null)?.detail;
    throw new ApiError(friendly(res.status, detail), res.status);
  }
  return data as T;
}

export const apiBase = API_BASE;
