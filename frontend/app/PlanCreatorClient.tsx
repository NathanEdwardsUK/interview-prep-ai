"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../lib/api";
import type { Plan } from "../lib/types";

export function PlanCreatorClient() {
  const { getToken } = useAuth();
  const router = useRouter();

  const [role, setRole] = useState("");
  const [context, setContext] = useState("");
  const [timeAvailable, setTimeAvailable] = useState<number | "">("");
  const [weakAreas, setWeakAreas] = useState("");
  const [motivationLevel, setMotivationLevel] = useState("");
  const [suggestedPlan, setSuggestedPlan] = useState<Plan | null>(null);
  const [loadingSuggest, setLoadingSuggest] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSuggest = async () => {
    setError(null);
    setSuggestedPlan(null);
    setLoadingSuggest(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const plan = (await api.plan.suggestNew(role, context, {
        time_available_minutes: timeAvailable === "" ? undefined : Number(timeAvailable),
        weak_areas: weakAreas.trim() ? weakAreas.split(/[,;]/).map((s) => s.trim()).filter(Boolean) : undefined,
        motivation_level: motivationLevel.trim() || undefined,
      })) as Plan;
      setSuggestedPlan(plan);
    } catch (e: any) {
      setError(e?.message ?? "Failed to generate plan");
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
      // Reload to fetch saved plan from /plan/view
      router.refresh();
    } catch (e: any) {
      setError(e?.message ?? "Failed to approve plan");
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm space-y-4">
      <h2 className="text-2xl font-semibold mb-2">Create your study plan</h2>
      <p className="text-sm text-gray-600">
        Tell the coach what role you&apos;re targeting and a bit about your
        experience. We&apos;ll suggest a structured plan you can review and
        approve.
      </p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Target role
        </label>
        <input
          type="text"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="e.g. Senior Backend Engineer"
          className="w-full border rounded-md px-3 py-2 text-sm bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/60 focus:border-slate-500"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Time available per day (minutes)
        </label>
        <input
          type="number"
          min={5}
          max={240}
          value={timeAvailable === "" ? "" : timeAvailable}
          onChange={(e) => setTimeAvailable(e.target.value === "" ? "" : parseInt(e.target.value, 10) || "")}
          placeholder="e.g. 60"
          className="w-full border rounded-md px-3 py-2 text-sm bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/60 focus:border-slate-500"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Areas of weakness (comma-separated)
        </label>
        <input
          type="text"
          value={weakAreas}
          onChange={(e) => setWeakAreas(e.target.value)}
          placeholder="e.g. system design, behavioral"
          className="w-full border rounded-md px-3 py-2 text-sm bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/60 focus:border-slate-500"
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Motivation level
        </label>
        <select
          value={motivationLevel}
          onChange={(e) => setMotivationLevel(e.target.value)}
          className="w-full border rounded-md px-3 py-2 text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-500/60 focus:border-slate-500"
        >
          <option value="">Select...</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Your background & goals
        </label>
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Describe your experience, strengths, and what you want to work on..."
          className="w-full border rounded-md px-3 py-2 text-sm min-h-[120px] bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/60 focus:border-slate-500"
        />
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleSuggest}
          disabled={loadingSuggest || !role.trim() || !context.trim()}
          className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm disabled:opacity-60"
        >
          {loadingSuggest ? "Generating plan..." : "Generate plan"}
        </button>
      </div>

      {suggestedPlan && (
        <div className="mt-4 border-t pt-4 space-y-4">
          <h3 className="text-lg font-semibold">Suggested plan</h3>
          <div className="text-sm text-gray-700">
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
            <p className="mt-1">
              {suggestedPlan.plan_overview.rationale}
            </p>
          </div>

          <div className="space-y-3">
            {suggestedPlan.plan_topics.map((topic, idx) => (
              <div
                key={`${topic.name}-${idx}`}
                className="border rounded-md p-3 flex flex-col gap-1"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <h4 className="text-sm font-semibold">{topic.name}</h4>
                  <span className="text-xs text-gray-600">
                    Priority {topic.priority} · {topic.daily_study_minutes}{" "}
                    min/day
                  </span>
                </div>
                {topic.description && (
                  <p className="text-xs text-gray-700">{topic.description}</p>
                )}
                {topic.expected_outcome && (
                  <p className="text-[11px] text-gray-500">
                    Expected outcome: {topic.expected_outcome}
                  </p>
                )}
              </div>
            ))}
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
              {approving ? "Saving..." : "Approve & save plan"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

