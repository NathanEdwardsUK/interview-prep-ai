import SessionClient from "./SessionClient";

export default function SessionPage({
  params,
}: {
  params: { id: string };
}) {
  const sessionId = Number(params.id);
  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-8">
      <div className="w-full max-w-4xl">
        <SessionClient sessionId={sessionId} />
      </div>
    </main>
  );
}

