"use client";

import { useState, useEffect, useRef } from "react";

const SpeechRecognitionConstructor =
  typeof window !== "undefined"
    ? window.SpeechRecognition ?? window.webkitSpeechRecognition
    : null;

export interface DictationButtonProps {
  onResult: (text: string, isFinal: boolean) => void;
  disabled?: boolean;
  lang?: string;
}

export default function DictationButton({
  onResult,
  disabled = false,
  lang = "en-US",
}: DictationButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const onResultRef = useRef(onResult);
  onResultRef.current = onResult;

  const supported = SpeechRecognitionConstructor != null;

  useEffect(() => {
    if (!supported) return;

    const Recognition = SpeechRecognitionConstructor!;
    const recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    const handleResult = (event: SpeechRecognitionEvent) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const text = (result[0]?.transcript ?? "").trim();
        if (text) {
          onResultRef.current(text, result.isFinal);
        }
      }
    };

    const handleEnd = () => {
      setIsListening(false);
    };

    const handleError = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === "not-allowed" || event.error === "no-speech") {
        setIsListening(false);
      }
    };

    recognition.onresult = handleResult;
    recognition.onend = handleEnd;
    recognition.onerror = handleError;

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore if already stopped
        }
        recognitionRef.current = null;
      }
      setIsListening(false);
    };
  }, [supported, lang]);

  const toggleListening = () => {
    if (!supported || !recognitionRef.current) return;
    if (isListening) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        setIsListening(false);
      }
    }
  };

  if (!supported) {
    return (
      <button
        type="button"
        disabled
        className="px-3 py-1.5 rounded-md bg-gray-300 text-gray-500 text-sm cursor-not-allowed"
        title="Dictation not supported in this browser"
      >
        Dictation not supported
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      disabled={disabled}
      aria-label={isListening ? "Stop dictation" : "Start dictation"}
      className={`px-3 py-1.5 rounded-md text-sm disabled:opacity-60 ${isListening
          ? "bg-red-600 text-white"
          : "bg-slate-200 text-slate-800 hover:bg-slate-300"
        }`}
    >
      {isListening ? "Stop dictation" : "Start dictation"}
    </button>
  );
}
