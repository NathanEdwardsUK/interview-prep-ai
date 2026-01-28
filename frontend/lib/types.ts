/**
 * TypeScript types for API responses
 * These should ideally be generated from OpenAPI schema
 */

export interface PlanOverview {
  target_role: string;
  total_daily_minutes: number;
  time_horizon_weeks: number;
  rationale: string;
}

export interface PlanTopic {
  name: string;
  description: string;
  priority: number;
  daily_study_minutes: number;
  expected_outcome: string;
}

export interface Plan {
  plan_overview: PlanOverview;
  plan_topics: PlanTopic[];
}

export interface Question {
  question: string;
  status: "new" | "redo";
  redo_reason?: "weak_answer" | "incomplete" | "time_pressure" | "high_value";
  difficulty: "easy" | "medium" | "hard";
}

export interface EvaluateAnswerResponse {
  score: number;
  positive_feedback: string[];
  improvement_areas: string[];
  anchors: Array<{
    name: string;
    anchor: string;
  }>;
}

export interface StudySession {
  id: number;
  topic_id: number;
  planned_duration: number;
  start_time: string;
  last_interaction_time: string;
  end_time?: string;
}
