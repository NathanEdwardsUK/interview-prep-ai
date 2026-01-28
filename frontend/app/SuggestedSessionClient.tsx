"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../lib/api";

export function SuggestedSessionClient() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [suggestion, setSuggestion] = useState<{
    topic_id: number;
    topic_name: string;
    planned_study_time: number;
    reason: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const api = createApiClient(async () => token || null);
        const result = (await api.study.getSuggestedSession()) as {
          topic_id: number;
          topic_name: string;
          planned_study_time: number;
          reason: string;
        };
        if (!cancelled) setSuggestion(result);
      } catch {
        if (!cancelled) setSuggestion(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const handleStartSuggested = async () => {
    if (!suggestion) return;
    setError(null);
    setStarting(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const session = (await api.study.startSession(
        suggestion.topic_id,
        suggestion.planned_study_time,
      )) as { id: number };
      router.push(`/study/session/${session.id}`);
    } catch (e: any) {
      setError(e?.message ?? "Failed to start session");
    } finally {
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="border rounded-lg p-4 bg-slate-50">
        <p className="text-sm text-slate-500">Loading suggestion...</p>
      </div>
    );
  }
  if (!suggestion) {
    return null;
  }

  return (
    <div className="border rounded-lg p-4 bg-blue-50 border-blue-200">
      <h3 className="font-semibold text-slate-800 mb-1">Suggested session</h3>
      <p className="text-sm text-slate-700 mb-2">{suggestion.reason}</p>
      <p className="text-xs text-slate-600 mb-2">
        <span className="font-medium">{suggestion.topic_name}</span> —{" "}
        {suggestion.planned_study_time} min
      </p>
      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
      <button
        type="button"
        onClick={handleStartSuggested}
        disabled={starting}
        className="px-3 py-1.5 rounded-md bg-blue-600 text-white text-sm disabled:opacity-60"
      >
        {starting ? "Starting..." : "Start suggested session"}
      </button>
    </div>
  );
}
