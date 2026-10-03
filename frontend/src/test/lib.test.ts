import { describe, expect, it, vi } from "vitest";
import { api, ApiError, setUnauthorizedHandler, tokenStore } from "@/lib/api";
import { applyPreferences, DEFAULT_PREFS } from "@/lib/prefs";
import { masteryWords, pct } from "@/lib/format";
import { _testing, track } from "@/lib/tracker";
import { mockFetch } from "./utils";

describe("api client", () => {
  it("sends the bearer token and JSON body", async () => {
    tokenStore.set("abc");
    const spy = mockFetch(() => ({ body: { ok: true } }));
    await api("/api/thing", { method: "POST", json: { a: 1 } });
    const [, init] = spy.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Bearer abc");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init?.body).toBe(JSON.stringify({ a: 1 }));
    tokenStore.set(null);
  });

  it("surfaces the server's friendly message", async () => {
    mockFetch(() => ({ status: 409, body: { detail: "An account with this email already exists." } }));
    await expect(api("/api/auth/register")).rejects.toMatchObject({ status: 409, message: "An account with this email already exists." });
  });

  it("never shows raw server errors to children", async () => {
    mockFetch(() => ({ status: 500, body: { trace: "Traceback..." } }));
    const err = (await api("/api/x").catch((e) => e)) as ApiError;
    expect(err.message).toMatch(/Oops/);
  });

  it("explains network failures kindly", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api("/api/x")).rejects.toMatchObject({ status: 0, message: expect.stringMatching(/can't reach/) });
  });

  it("calls the unauthorized handler when a token is rejected", async () => {
    tokenStore.set("expired");
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    mockFetch(() => ({ status: 401, body: { detail: "Please sign in to continue." } }));
    await api("/api/me").catch(() => undefined);
    expect(handler).toHaveBeenCalled();
    setUnauthorizedHandler(null);
    tokenStore.set(null);
  });
});

describe("accessibility preferences", () => {
  it("applies text scale, readable font, reduced motion and contrast to <html>", () => {
    applyPreferences({ ...DEFAULT_PREFS, text_scale: 1.25, readable_font: true, reduced_motion: true, high_contrast: true });
    const root = document.documentElement;
    expect(root.style.getPropertyValue("--text-scale")).toBe("1.25");
    expect(root).toHaveClass("font-readable", "reduce-motion", "high-contrast");
    applyPreferences(DEFAULT_PREFS);
    expect(root).not.toHaveClass("font-readable");
  });
});

describe("formatting", () => {
  it("uses encouraging words instead of raw numbers", () => {
    expect(masteryWords(0.9)).toBe("You've mastered this!");
    expect(masteryWords(0.7)).toMatch(/really good/);
    expect(pct(0.456)).toBe("46%");
    expect(pct(null)).toBe("–");
  });
});

describe("interaction tracker", () => {
  it("batches events and posts them to /api/interactions", async () => {
    tokenStore.set("tok");
    const spy = mockFetch(() => ({ status: 201, body: { recorded: 2 } }));
    track({ event_type: "section_viewed", topic_id: 1, payload: { section: "steps" } });
    track({ event_type: "read_aloud_used", topic_id: 1 });
    await _testing.flush();
    expect(spy).toHaveBeenCalledTimes(1);
    const [url, init] = spy.mock.calls[0];
    expect(String(url)).toContain("/api/interactions");
    expect(JSON.parse(String(init?.body)).events).toHaveLength(2);
    tokenStore.set(null);
  });
});
