import { auth } from "@clerk/nextjs/server";
import { planApi } from "../lib/api";
import type { Plan } from "../lib/types";
import { PlanTopicsClient } from "./PlanTopicsClient";
import { PlanCreatorClient } from "./PlanCreatorClient";
import { PlanRefinementClient } from "./PlanRefinementClient";
import { UserContextClient } from "./UserContextClient";
import { SuggestedSessionClient } from "./SuggestedSessionClient";
import { SessionHistoryClient } from "./SessionHistoryClient";

async function fetchPlan(token: string | null): Promise<Plan | null> {
  if (!token) return null;
  try {
    const data = (await planApi.viewPlan(token)) as Plan;
    return data;
  } catch {
    return null;
  }
}

export default async function Home() {
  const { getToken } = auth();
  const token = await getToken();
  const plan = await fetchPlan(token);

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-8">
      <div className="w-full max-w-4xl">
        <h1 className="text-4xl font-bold text-center mb-4">
          Interview Prep AI
        </h1>
        <p className="text-center text-lg mb-8">
          AI-powered interview preparation platform
        </p>

        {!token && (
          <div className="border border-dashed border-gray-300 rounded-lg p-6 text-center">
            <p className="text-gray-600 mb-2">
              Please sign in to view and manage your study plan.
            </p>
          </div>
        )}

        {token && !plan && <PlanCreatorClient />}

        {token && plan && (
          <div className="space-y-6">
            <section className="border rounded-lg p-6 bg-white shadow-sm">
              <SuggestedSessionClient />
            </section>
            <section className="border rounded-lg p-6 bg-white shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-semibold">Plan overview</h2>
              </div>
              <p className="text-gray-700">
                <span className="font-medium">Target role:</span>{" "}
                {plan.plan_overview.target_role}
              </p>
              <p className="text-gray-700">
                <span className="font-medium">Total daily minutes:</span>{" "}
                {plan.plan_overview.total_daily_minutes}
              </p>
              <p className="text-gray-700">
                <span className="font-medium">Time horizon:</span>{" "}
                {plan.plan_overview.time_horizon_weeks} weeks
              </p>
              <p className="text-gray-700 mt-2">
                {plan.plan_overview.rationale}
              </p>
            </section>

            <section className="border rounded-lg p-6 bg-white shadow-sm">
              <h2 className="text-2xl font-semibold mb-4">
                Topics &amp; sessions
              </h2>
              <PlanTopicsClient topics={plan.plan_topics} />
            </section>

            <section className="border rounded-lg p-6 bg-white shadow-sm">
              <PlanRefinementClient currentPlan={plan} />
            </section>

            <section className="border rounded-lg p-6 bg-white shadow-sm">
              <UserContextClient />
            </section>

            <section className="border rounded-lg p-6 bg-white shadow-sm">
              <SessionHistoryClient />
            </section>
          </div>
        )}

        {token && !plan && (
          <section className="mt-6 border rounded-lg p-6 bg-white shadow-sm">
            <UserContextClient />
          </section>
        )}
      </div>
    </main>
  );
}
