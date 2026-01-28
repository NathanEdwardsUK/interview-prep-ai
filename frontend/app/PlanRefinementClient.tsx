"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../lib/api";
import type { Plan } from "../lib/types";

interface Props {
  currentPlan: Plan;
}

export function PlanRefinementClient({ currentPlan }: Props) {
  const { getToken } = useAuth();
  const router = useRouter();

  const [userContext, setUserContext] = useState("");
  const [suggestedPlan, setSuggestedPlan] = useState<Plan | null>(null);
  const [loadingSuggest, setLoadingSuggest] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [canRefine, setCanRefine] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const api = createApiClient(async () => token || null);
        const result = (await api.plan.canRefine()) as { can_refine: boolean };
        if (!cancelled) setCanRefine(result.can_refine);
      } catch {
        if (!cancelled) setCanRefine(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  // Build progress data from current plan
  const currentProgress = currentPlan.plan_topics
    .filter((t) => t.progress)
    .map((t) => ({
      topic_name: t.name,
      strength_rating: t.progress?.strength_rating ?? null,
      total_time_spent: t.progress?.total_time_spent ?? 0,
    }));

  const handleSuggestChanges = async () => {
    setError(null);
    setSuggestedPlan(null);
    setLoadingSuggest(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const plan = (await api.plan.suggestChanges(
        currentPlan,
        userContext || "No additional context provided.",
        currentProgress.length > 0 ? { topics: currentProgress } : undefined,
        undefined
      )) as Plan;
      setSuggestedPlan(plan);
    } catch (e: any) {
      setError(e?.message ?? "Failed to generate plan changes");
      if (e?.message?.includes("once per day")) setCanRefine(false);
    } finally {
      setLoadingSuggest(false);
    }
  };

  const handleApprove = async () => {
    if (!suggestedPlan) return;
    setError(null);
    setApproving(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      await api.plan.approvePlan({ plan: suggestedPlan });
      router.refresh();
    } catch (e: any) {
      setError(e?.message ?? "Failed to approve plan");
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm space-y-4">
      <h2 className="text-2xl font-semibold mb-2">Review & adjust plan</h2>
      <p className="text-sm text-slate-600">
        Based on your progress, we can suggest adjustments to your study plan.
        Tell us how things are going or what you&apos;d like to change.
      </p>

      {currentProgress.length > 0 && (
        <div className="bg-slate-50 rounded-md p-3 text-sm">
          <p className="font-medium mb-1">Your progress so far:</p>
          <ul className="list-disc list-inside text-slate-700 space-y-1">
            {currentPlan.plan_topics
              .filter((t) => t.progress)
              .map((t) => (
                <li key={t.topic_id}>
                  <span className="font-medium">{t.name}:</span>{" "}
                  {t.progress?.strength_rating
                    ? `Strength ${t.progress.strength_rating}/10`
                    : "Not assessed"}{" "}
                  · {t.progress?.total_time_spent ?? 0} min practiced
                </li>
              ))}
          </ul>
        </div>
      )}

      {!canRefine && (
        <p className="text-sm text-amber-700">
          You&apos;ve already refined your plan today. Check back tomorrow.
        </p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">
          Additional context or feedback (optional)
        </label>
        <textarea
          value={userContext}
          onChange={(e) => setUserContext(e.target.value)}
          placeholder="E.g., 'I'm struggling with system design', 'I want to focus more on algorithms'..."
          className="w-full border rounded-md px-3 py-2 text-sm min-h-[80px] bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/60 focus:border-slate-500"
        />
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleSuggestChanges}
          disabled={loadingSuggest || !canRefine}
          className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm disabled:opacity-60"
        >
          {loadingSuggest ? "Analyzing..." : "Suggest plan changes"}
        </button>
      </div>

      {suggestedPlan && (
        <div className="mt-4 border-t pt-4 space-y-4">
          <h3 className="text-lg font-semibold">Suggested plan changes</h3>
          <div className="text-sm text-slate-700">
            <p>
              <span className="font-medium">Target role:</span>{" "}
              {suggestedPlan.plan_overview.target_role}
            </p>
            <p>
              <span className="font-medium">Total daily minutes:</span>{" "}
              {suggestedPlan.plan_overview.total_daily_minutes}
            </p>
            <p>
              <span className="font-medium">Time horizon:</span>{" "}
              {suggestedPlan.plan_overview.time_horizon_weeks} weeks
            </p>
            <p className="mt-1">{suggestedPlan.plan_overview.rationale}</p>
          </div>

          <div className="space-y-3">
            {suggestedPlan.plan_topics.map((topic, idx) => {
              const currentTopic = currentPlan.plan_topics.find(
                (t) => t.name === topic.name
              );
              const minutesChanged =
                currentTopic &&
                currentTopic.daily_study_minutes !== topic.daily_study_minutes;
              const priorityChanged =
                currentTopic && currentTopic.priority !== topic.priority;

              return (
                <div
                  key={`${topic.name}-${idx}`}
                  className={`border rounded-md p-3 flex flex-col gap-1 ${minutesChanged || priorityChanged
                    ? "bg-amber-50 border-amber-200"
                    : ""
                    }`}
                >
                  <div className="flex items-baseline justify-between gap-4">
                    <h4 className="text-sm font-semibold">{topic.name}</h4>
                    <span className="text-xs text-slate-600">
                      Priority {topic.priority} · {topic.daily_study_minutes}{" "}
                      min/day
                      {minutesChanged && currentTopic && (
                        <span className="ml-1 text-amber-700">
                          (was {currentTopic.daily_study_minutes} min)
                        </span>
                      )}
                    </span>
                  </div>
                  {topic.description && (
                    <p className="text-xs text-slate-700">{topic.description}</p>
                  )}
                  {topic.expected_outcome && (
                    <p className="text-[11px] text-slate-500">
                      Expected outcome: {topic.expected_outcome}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setSuggestedPlan(null)}
              disabled={approving}
              className="px-3 py-1.5 rounded-md border text-sm"
            >
              Discard
            </button>
            <button
              type="button"
              onClick={handleApprove}
              disabled={approving}
              className="px-4 py-1.5 rounded-md bg-green-600 text-white text-sm disabled:opacity-60"
            >
              {approving ? "Saving..." : "Approve updated plan"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
