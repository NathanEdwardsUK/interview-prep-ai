"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../../../../lib/api";
import type { Question, EvaluateAnswerResponse } from "../../../../lib/types";

interface Props {
  sessionId: number;
}

export default function SessionClient({ sessionId }: Props) {
  const { getToken } = useAuth();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluateAnswerResponse | null>(
    null,
  );
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [ending, setEnding] = useState(false);
  const [ended, setEnded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQuestions = async () => {
    setError(null);
    setLoadingQuestions(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const result = await api.study.generateQuestions(sessionId);
      const list = (result as { questions?: Question[] }).questions ?? [];
      setQuestions(list);
      setSelectedIndex(null);
      setAnswer("");
      setEvaluation(null);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load questions");
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (selectedIndex == null || !questions[selectedIndex]) return;
    setError(null);
    setSubmitting(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const question = questions[selectedIndex];
      const payload = {
        question_id: selectedIndex, // placeholder id; backend currently uses sample text
        raw_answer: answer,
      };
      const result = await api.study.evaluateAnswer(sessionId, payload);
      setEvaluation(result as EvaluateAnswerResponse);
    } catch (e: any) {
      setError(e?.message ?? "Failed to evaluate answer");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEndSession = async () => {
    setError(null);
    setEnding(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      await api.study.endSession(sessionId);
      setEnded(true);
    } catch (e: any) {
      setError(e?.message ?? "Failed to end session");
    } finally {
      setEnding(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Study session #{sessionId}</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={loadQuestions}
            disabled={loadingQuestions || ended}
            className="px-3 py-1.5 rounded-md bg-blue-600 text-white text-sm disabled:opacity-60"
          >
            {loadingQuestions ? "Generating..." : "Generate questions"}
          </button>
          <button
            type="button"
            onClick={handleEndSession}
            disabled={ending || ended}
            className="px-3 py-1.5 rounded-md bg-gray-800 text-white text-sm disabled:opacity-60"
          >
            {ended ? "Session ended" : ending ? "Ending..." : "End session"}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {ended && !error && (
        <p className="text-sm text-green-700">
          Session ended. Your progress for this topic has been updated.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-1 border rounded-lg p-3 bg-white shadow-sm">
          <h2 className="font-semibold mb-2 text-sm">Questions</h2>
          {questions.length === 0 ? (
            <p className="text-xs text-gray-500">
              No questions yet. Click &quot;Generate questions&quot; to start.
            </p>
          ) : (
            <ul className="space-y-2">
              {questions.map((q, idx) => (
                <li key={idx}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedIndex(idx);
                      setEvaluation(null);
                    }}
                    className={`w-full text-left text-xs border rounded-md px-2 py-1 ${selectedIndex === idx
                      ? "border-blue-600 bg-blue-50"
                      : "border-gray-200 hover:bg-gray-50"
                      }`}
                  >
                    <div className="font-medium">{q.question}</div>
                    <div className="text-[10px] text-gray-500">
                      {q.difficulty} · {q.status}
                      {q.redo_reason ? ` · ${q.redo_reason}` : ""}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="md:col-span-2 space-y-4">
          <div className="border rounded-lg p-3 bg-white shadow-sm">
            <h2 className="font-semibold mb-2 text-sm">Your answer</h2>
            {selectedIndex == null ? (
              <p className="text-xs text-gray-500">
                Select a question first to start answering.
              </p>
            ) : (
              <>
                <p className="text-xs text-gray-700 mb-2">
                  {questions[selectedIndex]?.question}
                </p>
                <textarea
                  className="w-full border rounded-md p-2 text-sm min-h-[120px]"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer here..."
                />
                <div className="flex justify-end mt-2">
                  <button
                    type="button"
                    onClick={handleSubmitAnswer}
                    disabled={submitting || !answer.trim()}
                    className="px-3 py-1.5 rounded-md bg-green-600 text-white text-sm disabled:opacity-60"
                  >
                    {submitting ? "Evaluating..." : "Submit for evaluation"}
                  </button>
                </div>
              </>
            )}
          </div>

          {evaluation && (
            <div className="border rounded-lg p-3 bg-white shadow-sm">
              <h2 className="font-semibold mb-2 text-sm">Feedback</h2>
              <p className="text-sm mb-2">
                <span className="font-medium">Score:</span> {evaluation.score} /
                10
              </p>
              {evaluation.positive_feedback.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs font-medium text-green-700">
                    What went well
                  </p>
                  <ul className="list-disc list-inside text-xs text-gray-700">
                    {evaluation.positive_feedback.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {evaluation.improvement_areas.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs font-medium text-amber-700">
                    Improvement areas
                  </p>
                  <ul className="list-disc list-inside text-xs text-gray-700">
                    {evaluation.improvement_areas.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {evaluation.anchors.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-blue-700">
                    Anchors to remember
                  </p>
                  <ul className="list-disc list-inside text-xs text-gray-700">
                    {evaluation.anchors.map((anchor, idx) => (
                      <li key={idx}>
                        <span className="font-semibold">{anchor.name}:</span>{" "}
                        {anchor.anchor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

