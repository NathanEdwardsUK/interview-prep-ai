/**
 * API Client for backend communication
 * Automatically injects Clerk authentication tokens
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthToken(): Promise<string | null> {
  // This function should be called from a component that has access to useAuth()
  // For now, we'll export a version that accepts a token parameter
  // Components should use: const { getToken } = useAuth(); const token = await getToken();
  return null;
}

export async function getAuthTokenFromClerk(): Promise<string | null> {
  // This will be used in components with useAuth hook
  if (typeof window !== "undefined") {
    try {
      // @ts-ignore - Clerk will be available at runtime
      const { useAuth } = await import("@clerk/nextjs");
      // Note: This should be called from a React component, not here
      // Components should use: const { getToken } = useAuth();
      return null;
    } catch {
      return null;
    }
  }
  return null;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const authToken = token || (await getAuthToken());

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ message: "An error occurred" }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Helper to create API functions that accept a token
export function createApiClient(getToken: () => Promise<string | null>) {
  return {
    plan: {
      suggestNew: async (role: string, userContext: string) => {
        const token = await getToken();
        return apiRequest(
          "/api/v1/plan/suggest_new",
          {
            method: "POST",
            body: JSON.stringify({ role, raw_user_context: userContext }),
          },
          token,
        );
      },

      suggestChanges: async (
        currentPlan: any,
        userContext: string,
        progress?: any,
        feedback?: any[],
      ) => {
        const token = await getToken();
        return apiRequest(
          "/api/v1/plan/suggest_changes",
          {
            method: "POST",
            body: JSON.stringify({
              current_plan: currentPlan,
              raw_user_context: userContext,
              current_progress: progress,
              user_feedback: feedback,
            }),
          },
          token,
        );
      },

      approvePlan: async (plan: any) => {
        const token = await getToken();
        return apiRequest(
          "/api/v1/plan/approve_plan",
          {
            method: "POST",
            body: JSON.stringify(plan),
          },
          token,
        );
      },

      viewPlan: async () => {
        const token = await getToken();
        return apiRequest(
          "/api/v1/plan/view",
          {
            method: "GET",
          },
          token,
        );
      },
    },

    study: {
      startSession: async (topicId: number, plannedStudyTime: number) => {
        const token = await getToken();
        return apiRequest(
          "/api/v1/study/start_session",
          {
            method: "POST",
            body: JSON.stringify({
              topic_id: topicId,
              planned_study_time: plannedStudyTime,
            }),
          },
          token,
        );
      },

      endSession: async (sessionId: number) => {
        const token = await getToken();
        return apiRequest(
          `/api/v1/study/end_session/${sessionId}`,
          {
            method: "PUT",
          },
          token,
        );
      },

      generateQuestions: async (sessionId: number) => {
        const token = await getToken();
        return apiRequest(
          `/api/v1/study/generate_questions/${sessionId}`,
          {
            method: "POST",
          },
          token,
        );
      },

      evaluateAnswer: async (sessionId: number, questionAttempt: any) => {
        const token = await getToken();
        return apiRequest(
          `/api/v1/study/evaluate_answer/${sessionId}`,
          {
            method: "POST",
            body: JSON.stringify(questionAttempt),
          },
          token,
        );
      },
    },
  };
}

// Legacy API functions (for backward compatibility)
// In components, use createApiClient with useAuth hook instead:
// const { getToken } = useAuth();
// const api = createApiClient(getToken);
// await api.plan.suggestNew(...);

export const planApi = {
  suggestNew: async (
    role: string,
    userContext: string,
    token?: string | null,
  ) => {
    return apiRequest(
      "/api/v1/plan/suggest_new",
      {
        method: "POST",
        body: JSON.stringify({ role, raw_user_context: userContext }),
      },
      token,
    );
  },

  suggestChanges: async (
    currentPlan: any,
    userContext: string,
    progress?: any,
    feedback?: any[],
    token?: string | null,
  ) => {
    return apiRequest(
      "/api/v1/plan/suggest_changes",
      {
        method: "POST",
        body: JSON.stringify({
          current_plan: currentPlan,
          raw_user_context: userContext,
          current_progress: progress,
          user_feedback: feedback,
        }),
      },
      token,
    );
  },

  approvePlan: async (plan: any, token?: string | null) => {
    return apiRequest(
      "/api/v1/plan/approve_plan",
      {
        method: "POST",
        body: JSON.stringify(plan),
      },
      token,
    );
  },

  viewPlan: async (token?: string | null) => {
    return apiRequest(
      "/api/v1/plan/view",
      {
        method: "GET",
      },
      token,
    );
  },
};

export const studyApi = {
  startSession: async (
    topicId: number,
    plannedStudyTime: number,
    token?: string | null,
  ) => {
    return apiRequest(
      "/api/v1/study/start_session",
      {
        method: "POST",
        body: JSON.stringify({
          topic_id: topicId,
          planned_study_time: plannedStudyTime,
        }),
      },
      token,
    );
  },

  endSession: async (sessionId: number, token?: string | null) => {
    return apiRequest(
      `/api/v1/study/end_session/${sessionId}`,
      {
        method: "PUT",
      },
      token,
    );
  },

  generateQuestions: async (sessionId: number, token?: string | null) => {
    return apiRequest(
      `/api/v1/study/generate_questions/${sessionId}`,
      {
        method: "POST",
      },
      token,
    );
  },

  evaluateAnswer: async (
    sessionId: number,
    questionAttempt: any,
    token?: string | null,
  ) => {
    return apiRequest(
      `/api/v1/study/evaluate_answer/${sessionId}`,
      {
        method: "POST",
        body: JSON.stringify(questionAttempt),
      },
      token,
    );
  },
};
