"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { createApiClient } from "../lib/api";

export function UserContextClient() {
  const { getToken } = useAuth();
  const [contextText, setContextText] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const api = createApiClient(async () => token || null);
        const result = (await api.plan.getUserContext()) as { context_text: string };
        if (!cancelled) setContextText(result.context_text ?? "");
      } catch {
        if (!cancelled) setContextText("");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const handleSave = async () => {
    setError(null);
    setMessage(null);
    setSaving(true);
    try {
      const token = await getToken();
      const api = createApiClient(async () => token || null);
      await api.plan.updateUserContext(contextText);
      setMessage("Context saved.");
    } catch (e: any) {
      setError(e?.message ?? "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="border rounded-lg p-6 bg-white shadow-sm">
        <h2 className="text-xl font-semibold mb-2">Your context</h2>
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-2">View / edit context</h2>
      <p className="text-sm text-slate-600 mb-2">
        Your background, goals, and experience. Used to personalize plan suggestions.
      </p>
      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
      {message && <p className="text-sm text-green-700 mb-2">{message}</p>}
      <textarea
        className="w-full border rounded-md px-3 py-2 text-sm min-h-[120px] bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/60"
        value={contextText}
        onChange={(e) => setContextText(e.target.value)}
        placeholder="E.g. 5 years in backend, targeting senior roles..."
      />
      <div className="mt-2 flex justify-end">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 rounded-md bg-slate-700 text-white text-sm disabled:opacity-60"
        >
          {saving ? "Saving..." : "Save context"}
        </button>
      </div>
    </div>
  );
}
