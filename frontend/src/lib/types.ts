export type Difficulty = "easy" | "medium" | "hard";
export type Style = "step_by_step" | "worked_example" | "guided_discovery" | "concise";
export type Level = "low" | "medium" | "high";
export type Band = "high_support" | "guided" | "balanced" | "stretch";
export type Stage = "discover" | "practice" | "understand" | "master";

export interface Preferences {
  explanation_length: "short" | "medium" | "detailed";
  prefers_visuals: boolean;
  prefers_examples: boolean;
  pace: "relaxed" | "steady" | "quick";
  read_aloud: boolean;
  readable_font: boolean;
  text_scale: number;
  line_spacing: number;
  reduced_motion: boolean;
  focus_mode: boolean;
  high_contrast: boolean;
}

export interface User {
  id: number;
  email: string;
  display_name: string;
  role: string;
  avatar: string;
  grade_band: string | null;
  favorite_subject_id: number | null;
  weekly_goal_days: number;
  preferences: Preferences;
}

export interface TokenResponse {
  access_token: string;
  user: User;
}

export interface FactorContribution {
  family: string;
  need: number;
  weight: number;
  note: string;
}

export interface TeachingStrategy {
  difficulty: Difficulty;
  explanation_style: Style;
  content_density: Level;
  hint_level: "none" | "light" | "guided" | "full";
  example_count: number;
  review_required: boolean;
  pacing: "slow" | "steady" | "brisk";
  visual_support: Level;
  option_count: number;
  question_count: number;
  suggest_break: boolean;
  read_aloud_suggested: boolean;
  tone: "gentle" | "warm" | "celebratory";
  support_score: number;
  data_confidence: number;
  band: Band;
  rationale: string[];
  learner_message: string;
  factors?: FactorContribution[];
  engine_version?: string;
}

export interface TopicCard {
  id: number;
  slug: string;
  title: string;
  summary: string;
  icon: string;
  subject: { id: number; slug: string; name: string; icon: string };
  mastery: number;
  attempts: number;
  stage: Stage;
  lesson_id: number | null;
  lesson_title: string | null;
  prerequisite_topic_id: number | null;
}

export interface SubjectSummary {
  id: number;
  slug: string;
  name: string;
  description?: string;
  icon: string;
  topic_count: number;
  progress: number;
  practiced_topics: number;
  next_topic: TopicCard | null;
  topics?: TopicCard[];
}

export interface Achievement {
  key: string;
  title: string;
  description: string;
  icon: string;
  progress: number;
  target: number;
  earned: boolean;
}

export interface Dashboard {
  greeting: string;
  display_name: string;
  is_demo_account: boolean;
  today: { id: number; kind: string; reason: string; topic: TopicCard | null; lesson_id: number | null } | null;
  recommendations: { id: number; kind: string; reason: string; topic: TopicCard | null; lesson_id: number | null }[];
  progress: {
    topics_total: number;
    topics_practiced: number;
    topics_mastered: number;
    average_mastery: number;
    questions_answered: number;
    correct_answers: number;
  };
  week: { date: string; label: string; learned: boolean }[];
  weekly_goal_days: number;
  learning_days_in_a_row: number;
  subjects: SubjectSummary[];
  topic_mastery: TopicCard[];
  recent_activity: { type: string; text: string; at: string; score?: number | null }[];
  goals: { id: number; title: string; topic_id: number | null; due_date: string | null; target: number | null; current: number | null }[];
  achievements: Achievement[];
  journey: { stages: string[]; current: string; index: number };
  insight: { title: string; detail: string };
  growth: { date: string; mastery: number | null }[];
}

export interface LessonSection {
  key: string;
  title: string;
  kind: "text" | "steps" | "list" | "vocabulary";
  content: string | string[] | { term: string; meaning: string }[];
  shown: boolean;
}

export interface LessonView {
  id: number;
  title: string;
  estimated_minutes: number;
  topic: TopicCard;
  sections: LessonSection[];
  strategy: {
    difficulty: Difficulty;
    explanation_style: Style;
    content_density: Level;
    pacing: string;
    visual_support: Level;
    read_aloud_suggested: boolean;
    suggest_break: boolean;
    learner_message: string;
    band: Band;
  };
}

export interface QuizQuestion {
  id: number;
  prompt: string;
  options: string[];
  difficulty: number;
  source: string;
}

export interface Quiz {
  attempt_id: number;
  topic: { id: number; title: string };
  difficulty: Difficulty;
  strategy: {
    difficulty: Difficulty;
    hint_level: string;
    option_count: number;
    question_count: number;
    learner_message: string;
    tone: string;
    read_aloud_suggested: boolean;
    suggest_break: boolean;
  };
  questions: QuizQuestion[];
}

export interface QuizResult {
  attempt_id: number;
  topic: { id: number; title: string };
  score: number;
  correct: number;
  total: number;
  headline: string;
  celebrate: boolean;
  mastery_before: number;
  mastery_after: number;
  stage: Stage;
  results: {
    question_id: number;
    prompt: string;
    your_answer: string | null;
    correct_answer: string;
    is_correct: boolean;
    skipped: boolean;
    feedback: string;
    explanation: string;
  }[];
  mistakes: QuizResult["results"];
  next_difficulty: Difficulty;
  next_message: string;
  revision: { needed: boolean; lesson_id: number | null; lesson_title: string | null; tutor_prompt: string; tips: string[] };
}

export interface Source {
  n: number;
  document_id: number;
  title: string;
  section: string | null;
  excerpt: string;
  score: number;
  used: boolean;
  source: string;
}

export interface TutorPayload {
  message: string;
  steps: string[];
  examples: string[];
  check_question: string | null;
  encouragement: string;
  follow_ups: string[];
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  intent: string | null;
  payload: Partial<TutorPayload>;
  sources: Source[];
  strategy: Partial<TeachingStrategy> | null;
  provider: string | null;
  is_demo: boolean;
  feedback: string | null;
  created_at: string | null;
}

export interface ChatResponse {
  conversation_id: number;
  topic_id: number | null;
  user_message: ChatMessage;
  message: ChatMessage;
  strategy: TeachingStrategy | null;
  notice: string | null;
}

export interface DocumentItem {
  id: number;
  title: string;
  filename: string | null;
  content_type: string;
  source: "system" | "upload";
  status: "uploaded" | "ingested" | "failed";
  char_count: number;
  chunk_count: number;
  error: string | null;
  topic_id: number | null;
  owned: boolean;
  created_at: string | null;
  ingested_at: string | null;
  preview?: string;
  chunks?: { index: number; section: string | null; words: number; text: string }[];
}

export interface Analytics {
  period_days: number;
  summary: {
    sessions: number;
    minutes: number;
    questions_answered: number;
    accuracy: number | null;
    topics_practiced: number;
    average_mastery: number | null;
    hint_rate: number;
    trend: string;
  };
  accuracy_trend: { date: string; accuracy: number | null; answered: number }[];
  engagement_trend: { date: string; minutes: number; sessions: number; events: number }[];
  mastery_trend: ({ date: string; average_mastery: number | null } & Record<string, number | string | null>)[];
  mastery_topics: Record<string, string>;
  topic_performance: {
    topic_id: number;
    topic: string;
    answered: number;
    accuracy: number;
    mastery: number | null;
    avg_response_seconds: number;
    hints_per_question: number;
    skip_rate: number;
  }[];
  difficulty_mix: { difficulty: string; answered: number; accuracy: number }[];
  strategy_history: { at: string; context: string; topic: string | null; support_score: number; band: Band; difficulty: Difficulty; explanation_style: Style }[];
  current_strategy: TeachingStrategy;
  ml: {
    struggle_probability: number;
    struggle_source: string;
    struggle_version: string;
    engagement_probability: number;
    engagement_source: string;
    struggle_series: { at: string; value: number }[];
    learner_profile: { key: string; name: string; description: string; confidence: number; source: string; version: string } | null;
    model_card: {
      data_provenance: Record<string, string> | null;
      note: string | null;
      struggle_roc_auc: number | null;
      engagement_roc_auc: number | null;
      trained_at: string | null;
    };
  };
  safety: { redirected_or_supported_messages: number };
}

export interface Goal {
  id: number;
  title: string;
  topic_id: number | null;
  target_mastery: number | null;
  current_mastery: number | null;
  due_date: string | null;
  status: "active" | "completed" | "archived";
  reached: boolean;
}
