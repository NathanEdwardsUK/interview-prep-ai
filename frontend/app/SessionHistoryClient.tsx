"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../lib/api";

interface SessionRow {
  id: number;
  topic_id: number;
  topic_name: string;
  start_time: string;
  end_time: string | null;
  planned_duration: number;
  questions_answered: number;
  average_score: number | null;
}

export function SessionHistoryClient() {
  const { getToken } = useAuth();
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const api = createApiClient(async () => token || null);
        const result = (await api.study.getSessions({ limit: 30 })) as {
          sessions: SessionRow[];
        };
        if (!cancelled) setSessions(result.sessions ?? []);
      } catch {
        if (!cancelled) setSessions([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  if (loading) {
    return (
      <div className="border rounded-lg p-6 bg-white shadow-sm">
        <h2 className="text-xl font-semibold mb-4">Session history</h2>
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  const byTopic = sessions.reduce<Record<string, { total: number; scores: number[]; count: number }>>((acc, s) => {
    const name = s.topic_name;
    if (!acc[name]) acc[name] = { total: 0, scores: [], count: 0 };
    acc[name].total += s.planned_duration;
    acc[name].count += 1;
    if (s.average_score != null) acc[name].scores.push(s.average_score);
    return acc;
  }, {});

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm space-y-6">
      <h2 className="text-xl font-semibold">Session history</h2>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {Object.keys(byTopic).length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 mb-2">Time & score by topic</h3>
          <div className="space-y-2">
            {Object.entries(byTopic).map(([name, data]) => {
              const avgScore = data.scores.length ? (data.scores.reduce((a, b) => a + b, 0) / data.scores.length).toFixed(1) : "—";
              const maxMinutes = Math.max(...Object.values(byTopic).map((d) => d.total), 1);
              const width = (data.total / maxMinutes) * 100;
              return (
                <div key={name} className="flex items-center gap-3">
                  <span className="w-32 text-sm font-medium text-slate-700 truncate" title={name}>
                    {name}
                  </span>
                  <div className="flex-1 h-5 bg-slate-100 rounded overflow-hidden">
                    <div
                      className="h-full bg-slate-500 rounded"
                      style={{ width: `${Math.min(width, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-600 w-16">
                    {data.total} min · avg {avgScore}/10
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {sessions.length === 0 ? (
        <p className="text-sm text-slate-500">No sessions yet. Start a session from your plan.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-600">
                <th className="py-2 pr-4">Topic</th>
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Duration</th>
                <th className="py-2 pr-4">Questions</th>
                <th className="py-2">Avg score</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => {
                const start = s.start_time ? new Date(s.start_time).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "—";
                return (
                  <tr key={s.id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 font-medium text-slate-800">{s.topic_name}</td>
                    <td className="py-2 pr-4 text-slate-600">{start}</td>
                    <td className="py-2 pr-4 text-slate-600">{s.planned_duration} min</td>
                    <td className="py-2 pr-4 text-slate-600">{s.questions_answered}</td>
                    <td className="py-2 text-slate-600">{s.average_score != null ? `${s.average_score}/10` : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
