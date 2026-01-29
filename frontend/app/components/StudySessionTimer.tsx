"use client";

import { useState, useEffect, useRef } from "react";

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface StudySessionTimerProps {
  sessionStartTime: Date | null;
  plannedDurationMinutes: number | null;
  ended: boolean;
  selectedIndex: number | null;
}

export default function StudySessionTimer({
  sessionStartTime,
  plannedDurationMinutes,
  ended,
  selectedIndex,
}: StudySessionTimerProps) {
  const [sessionElapsedSeconds, setSessionElapsedSeconds] = useState(0);
  const [questionElapsedSeconds, setQuestionElapsedSeconds] = useState(0);
  const sessionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const questionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!sessionStartTime || ended) return;
    const tick = () => {
      setSessionElapsedSeconds(
        Math.floor((Date.now() - sessionStartTime.getTime()) / 1000),
      );
    };
    tick();
    sessionTimerRef.current = setInterval(tick, 1000);
    return () => {
      if (sessionTimerRef.current) clearInterval(sessionTimerRef.current);
    };
  }, [sessionStartTime, ended]);

  useEffect(() => {
    if (selectedIndex == null) {
      setQuestionElapsedSeconds(0);
      if (questionTimerRef.current) {
        clearInterval(questionTimerRef.current);
        questionTimerRef.current = null;
      }
      return;
    }
    const start = Date.now();
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

  return (
    <div className="flex items-center gap-4">
      {sessionStartTime != null && (
        <div className="text-sm text-slate-600">
          <span className="font-medium">Session:</span>{" "}
          {formatElapsed(sessionElapsedSeconds)}
          {plannedDurationMinutes != null && (
            <span className="ml-1 text-slate-500">
              / {plannedDurationMinutes} min
            </span>
          )}
        </div>
      )}
      {selectedIndex != null && (
        <div className="text-sm text-slate-600">
          <span className="font-medium">Answer time:</span>{" "}
          {formatElapsed(questionElapsedSeconds)}
        </div>
      )}
    </div>
  );
}
