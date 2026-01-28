"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../lib/api";
import type { PlanTopic, StudySession } from "../lib/types";

interface Props {
  topics: PlanTopic[];
}

export function PlanTopicsClient({ topics }: Props) {
  const router = useRouter();
  const { getToken } = useAuth();
  const [loadingTopicId, setLoadingTopicId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStartSession = async (topic: PlanTopic) => {
    if (!topic.topic_id) {
      setError("This topic is missing an id; try refreshing the page.");
      return;
    }
    setError(null);
    setLoadingTopicId(topic.topic_id);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const session = (await api.study.startSession(
        topic.topic_id,
        topic.daily_study_minutes,
      )) as StudySession;
      router.push(`/study/session/${session.id}`);
    } catch (e: any) {
      setError(e?.message ?? "Failed to start session");
    } finally {
      setLoadingTopicId(null);
    }
  };

  return (
    <div className="space-y-3">
      {error && (
        <p className="text-sm text-red-600 mb-2">
          {error}
        </p>
      )}
      {topics.map((topic) => (
        <div
          key={topic.topic_id ?? topic.name}
          className="border rounded-md p-4 flex flex-col gap-2"
        >
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold">{topic.name}</h3>
              {topic.description && (
                <p className="text-gray-700 text-sm">{topic.description}</p>
              )}
            </div>
            <span className="text-sm text-gray-600">
              Priority {topic.priority} · {topic.daily_study_minutes} min/day
            </span>
          </div>
          {topic.expected_outcome && (
            <p className="text-gray-500 text-xs">
              Expected outcome: {topic.expected_outcome}
            </p>
          )}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => handleStartSession(topic)}
              disabled={loadingTopicId === topic.topic_id}
              className="px-3 py-1.5 rounded-md bg-blue-600 text-white text-sm disabled:opacity-60"
            >
              {loadingTopicId === topic.topic_id
                ? "Starting..."
                : "Start session"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

