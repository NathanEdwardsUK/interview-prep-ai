import type { Metadata } from "next";
import { Inter } from "next/font/google";
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Interview Prep AI",
  description: "AI-powered interview preparation platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className + " bg-slate-50 text-slate-900"}>
          <header className="w-full border-b border-slate-200 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-slate-50 shadow-sm">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-slate-700 text-xs font-bold">
                  IP
                </span>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold tracking-wide">
                    Interview Prep AI
                  </span>
                  <span className="text-[11px] text-slate-300">
                    Practice plans, questions & feedback
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <SignedOut>
                  <SignInButton mode="modal">
                    <button className="rounded-full bg-slate-50 px-4 py-1.5 text-xs font-medium text-slate-900 shadow-sm hover:bg-white">
                      Sign in
                    </button>
                  </SignInButton>
                </SignedOut>
                <SignedIn>
                  <UserButton afterSignOutUrl="/" />
                </SignedIn>
              </div>
            </div>
          </header>
          <main className="min-h-screen">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
