import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LogoMark } from "@/components/brand/Logo";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { ProgressRing, Toggle } from "@/components/ui";
import { JourneyPath } from "@/components/illustrations/JourneyPath";
import { AdaptSlider } from "@/pages/landing/Demos";
import { LoginPage } from "@/pages/auth/AuthPages";
import { mockFetch, renderWithProviders } from "./utils";

const strategy = (band: string, difficulty: string, style: string) => ({
  difficulty,
  explanation_style: style,
  content_density: "low",
  hint_level: "full",
  example_count: 3,
  review_required: true,
  pacing: "slow",
  visual_support: "high",
  option_count: 3,
  question_count: 4,
  suggest_break: false,
  read_aloud_suggested: false,
  tone: "gentle",
  support_score: 0.8,
  data_confidence: 1,
  band,
  rationale: ["Main factor - mastery: estimated mastery 10%."],
  learner_message: "Let's take this one small step at a time. You've got this!",
  factors: [],
});

describe("brand", () => {
  it("logo can be labelled for screen readers", () => {
    render(<LogoMark title="Lumora" />);
    expect(screen.getByRole("img", { name: "Lumora" })).toBeInTheDocument();
  });
  it("Divi identifies as an AI guide", () => {
    render(<DiviAvatar />);
    expect(screen.getByRole("img", { name: /AI learning guide/i })).toBeInTheDocument();
  });
});

describe("ui", () => {
  it("progress ring announces its value", () => {
    render(<ProgressRing value={0.42} sublabel="mastery" />);
    expect(screen.getByText("42 percent mastery")).toBeInTheDocument();
  });

  it("toggle is an accessible switch", async () => {
    let value = false;
    render(<Toggle label="Readable font" checked={value} onChange={(v) => (value = v)} />);
    const sw = screen.getByRole("switch", { name: "Readable font" });
    expect(sw).toHaveAttribute("aria-checked", "false");
    await userEvent.click(sw);
    expect(value).toBe(true);
  });

  it("journey marks the learner's current stage", () => {
    render(<JourneyPath current="understand" />);
    const current = screen.getByText("Understand").closest("li");
    expect(current).toHaveAttribute("aria-current", "step");
  });
});

describe("landing: adaptive slider", () => {
  it("renders the strategy returned by the real engine endpoint and re-queries on change", async () => {
    const levels: number[] = [];
    mockFetch((url, init) => {
      if (url.includes("/api/adaptive/preview")) {
        const level = JSON.parse(String(init?.body)).level as number;
        levels.push(level);
        return { body: { strategy: level > 50 ? strategy("stretch", "hard", "concise") : strategy("high_support", "easy", "step_by_step") } };
      }
      return { status: 404 };
    });
    renderWithProviders(<AdaptSlider />);
    expect(await screen.findByText("Step-by-step")).toBeInTheDocument();
    expect(screen.getByText("Gentle")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("How is the learner doing?"), { target: { value: "90" } });
    expect(await screen.findByText("Short & sharp", {}, { timeout: 2000 })).toBeInTheDocument();
    expect(levels).toContain(90);
  });

  it("shows a friendly error when the API is unreachable", async () => {
    mockFetch(() => ({ status: 503, body: {} }));
    renderWithProviders(<AdaptSlider />);
    expect(await screen.findByText(/isn't reachable/i)).toBeInTheDocument();
  });
});

describe("auth", () => {
  it("shows the server's message when sign-in fails", async () => {
    mockFetch(() => ({ status: 401, body: { detail: "Email or password is not correct." } }));
    renderWithProviders(<LoginPage />, { route: "/login" });
    await userEvent.type(screen.getByLabelText("Email"), "kid@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrongpass1");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Email or password is not correct."));
  });
});
