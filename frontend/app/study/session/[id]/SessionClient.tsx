"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../../../../lib/api";
import type { Question, EvaluateAnswerResponse } from "../../../../lib/types";

interface Props {
  sessionId: number;
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
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
  const [skippedIndices, setSkippedIndices] = useState<Set<number>>(new Set());
  // Story structure: map question text -> { questionId, storyId }; current story text and ids
  const [storyMap, setStoryMap] = useState<Record<string, { questionId: number; storyId: number }>>({});
  const [storyText, setStoryText] = useState("");
  const [storyId, setStoryId] = useState<number | null>(null);
  const [loadingStory, setLoadingStory] = useState(false);
  const [savingStory, setSavingStory] = useState(false);

  // Session timer: start_time and planned_duration from API
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null);
  const [plannedDurationMinutes, setPlannedDurationMinutes] = useState<number | null>(null);
  const [sessionElapsedSeconds, setSessionElapsedSeconds] = useState(0);
  const sessionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Per-question timer
  const [questionStartTime, setQuestionStartTime] = useState<number | null>(null);
  const [questionElapsedSeconds, setQuestionElapsedSeconds] = useState(0);
  const questionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const api = createApiClient(async () => token || null);
        const session = (await api.study.getSession(sessionId)) as {
          start_time: string;
          planned_duration: number;
          end_time?: string | null;
        };
        if (cancelled) return;
        setSessionStartTime(new Date(session.start_time));
        setPlannedDurationMinutes(session.planned_duration);
        if (session.end_time) setEnded(true);
      } catch {
        if (!cancelled) setSessionStartTime(new Date());
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId, getToken]);

  useEffect(() => {
    if (!sessionStartTime || ended) return;
    const tick = () => {
      setSessionElapsedSeconds(Math.floor((Date.now() - sessionStartTime.getTime()) / 1000));
    };
    tick();
    sessionTimerRef.current = setInterval(tick, 1000);
    return () => {
      if (sessionTimerRef.current) clearInterval(sessionTimerRef.current);
    };
  }, [sessionStartTime, ended]);

  useEffect(() => {
    if (selectedIndex == null) {
      setQuestionStartTime(null);
      setQuestionElapsedSeconds(0);
      if (questionTimerRef.current) {
        clearInterval(questionTimerRef.current);
        questionTimerRef.current = null;
      }
      return;
    }
    const start = Date.now();
    setQuestionStartTime(start);
    setQuestionElapsedSeconds(0);
    const id = setInterval(() => {
      setQuestionElapsedSeconds(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    questionTimerRef.current = id;
    return () => {
      clearInterval(id);
      questionTimerRef.current = null;
    };
  }, [selectedIndex]);

  useEffect(() => {
    if (selectedIndex == null || !questions[selectedIndex]) return;
    const q = questions[selectedIndex];
    const meta = storyMap[q.question];
    if (!meta || storyText !== "") return;
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const api = createApiClient(async () => token || null);
        const result = (await api.study.getStory(meta.questionId)) as { structure_text: string };
        if (!cancelled) setStoryText(result.structure_text);
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedIndex, questions, storyMap, storyText]);

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
      setSkippedIndices(new Set());
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
    const answerTimeSeconds = questionStartTime != null ? Math.floor((Date.now() - questionStartTime) / 1000) : undefined;
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const question = questions[selectedIndex];
      const payload = {
        question: question.question,
        raw_answer: answer,
        answer_time_seconds: answerTimeSeconds,
      };
      const result = await api.study.evaluateAnswer(sessionId, payload);
      setEvaluation(result as EvaluateAnswerResponse);
    } catch (e: any) {
      setError(e?.message ?? "Failed to evaluate answer");
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateStory = async () => {
    if (selectedIndex == null || !questions[selectedIndex]) return;
    const q = questions[selectedIndex];
    setError(null);
    setLoadingStory(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const result = (await api.study.generateStory(sessionId, q.question)) as {
        question_id: number;
        story_id: number;
        structure_text: string;
      };
      setStoryMap((prev) => ({
        ...prev,
        [q.question]: { questionId: result.question_id, storyId: result.story_id },
      }));
      setStoryText(result.structure_text);
      setStoryId(result.story_id);
    } catch (e: any) {
      setError(e?.message ?? "Failed to generate story");
    } finally {
      setLoadingStory(false);
    }
  };

  const handleLoadStory = async () => {
    if (selectedIndex == null || !questions[selectedIndex]) return;
    const q = questions[selectedIndex];
    const meta = storyMap[q.question];
    if (!meta) return;
    setError(null);
    setLoadingStory(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      const result = (await api.study.getStory(meta.questionId)) as { structure_text: string; id: number };
      setStoryText(result.structure_text);
      setStoryId(result.id);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load story");
    } finally {
      setLoadingStory(false);
    }
  };

  const handleSaveStory = async () => {
    if (storyId == null) return;
    setError(null);
    setSavingStory(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      await api.study.updateStory(storyId, storyText);
    } catch (e: any) {
      setError(e?.message ?? "Failed to save story");
    } finally {
      setSavingStory(false);
    }
  };

  const handleSkipQuestion = (idx: number) => {
    setSkippedIndices((prev) => new Set(prev).add(idx));
    if (selectedIndex === idx) {
      setSelectedIndex(null);
      setAnswer("");
      setEvaluation(null);
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Study session #{sessionId}</h1>
        <div className="flex items-center gap-4">
          {sessionStartTime != null && (
            <div className="text-sm text-slate-600">
              <span className="font-medium">Session:</span> {formatElapsed(sessionElapsedSeconds)}
              {plannedDurationMinutes != null && (
                <span className="ml-1 text-slate-500">
                  / {plannedDurationMinutes} min
                </span>
              )}
            </div>
          )}
          {selectedIndex != null && (
            <div className="text-sm text-slate-600">
              <span className="font-medium">Answer time:</span> {formatElapsed(questionElapsedSeconds)}
            </div>
          )}
        </div>
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
              {questions.map((q, idx) => {
                const isSkipped = skippedIndices.has(idx);
                return (
                  <li key={idx} className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedIndex(idx);
                        setEvaluation(null);
                        const q = questions[idx];
                        const meta = storyMap[q?.question ?? ""];
                        if (meta) {
                          setStoryId(meta.storyId);
                          setStoryText(""); // will be loaded when user clicks Load or we load below
                        } else {
                          setStoryId(null);
                          setStoryText("");
                        }
                      }}
                      className={`flex-1 text-left text-xs border rounded-md px-2 py-1 ${selectedIndex === idx
                        ? "border-blue-600 bg-blue-50"
                        : isSkipped
                          ? "border-gray-200 bg-gray-100 text-gray-500"
                          : "border-gray-200 hover:bg-gray-50"
                        }`}
                    >
                      <div className="font-medium">{q.question}</div>
                      <div className="text-[10px] text-gray-500">
                        {q.difficulty} · {q.status}
                        {q.redo_reason ? ` · ${q.redo_reason}` : ""}
                        {isSkipped && " · Skipped"}
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSkipQuestion(idx)}
                      disabled={ended}
                      className="shrink-0 px-2 py-1 text-xs rounded border border-slate-300 text-slate-600 hover:bg-slate-100 disabled:opacity-50"
                    >
                      Skip
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="md:col-span-2 space-y-4">
          <div className="border rounded-lg p-3 bg-white shadow-sm">
            <h2 className="font-semibold mb-2 text-sm">Story structure</h2>
            {selectedIndex == null ? (
              <p className="text-xs text-gray-500">
                Select a question to generate or edit a story outline.
              </p>
            ) : (
              <>
                <div className="flex flex-wrap gap-2 mb-2">
                  <button
                    type="button"
                    onClick={handleGenerateStory}
                    disabled={loadingStory || ended}
                    className="px-2 py-1 rounded border border-slate-300 text-xs hover:bg-slate-100 disabled:opacity-50"
                  >
                    {loadingStory ? "Generating..." : "Generate story structure"}
                  </button>
                  {storyMap[questions[selectedIndex]?.question ?? ""] && (
                    <button
                      type="button"
                      onClick={handleLoadStory}
                      disabled={loadingStory || ended}
                      className="px-2 py-1 rounded border border-slate-300 text-xs hover:bg-slate-100 disabled:opacity-50"
                    >
                      Load saved
                    </button>
                  )}
                  {storyId != null && (
                    <button
                      type="button"
                      onClick={handleSaveStory}
                      disabled={savingStory || ended}
                      className="px-2 py-1 rounded bg-green-600 text-white text-xs disabled:opacity-50"
                    >
                      {savingStory ? "Saving..." : "Save story"}
                    </button>
                  )}
                </div>
                {storyText && (
                  <textarea
                    className="w-full border rounded-md p-2 text-sm min-h-[120px] bg-white text-slate-900"
                    value={storyText}
                    onChange={(e) => setStoryText(e.target.value)}
                    placeholder="Story outline will appear here..."
                  />
                )}
              </>
            )}
          </div>

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

