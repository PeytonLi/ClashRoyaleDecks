"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { signIn } from "next-auth/react";
import {
  ChevronRight,
  Loader2,
  Lock,
  Mail,
  ShieldCheck,
  User,
} from "lucide-react";

type AuthMode = "signin" | "signup";

export default function UnifiedAuthForm({
  callbackUrl,
  googleEnabled,
}: {
  callbackUrl: string;
  googleEnabled: boolean;
}) {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isSignIn = mode === "signin";

  const toggleMode = () => {
    setMode(isSignIn ? "signup" : "signin");
    setError("");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    if (!isSignIn) {
      const response = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(data.error || "Could not create account.");
        setLoading(false);
        return;
      }
    }

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
      callbackUrl,
    });

    setLoading(false);

    if (result?.error) {
      setError(
        isSignIn
          ? "Invalid email or password."
          : "Account created but sign-in failed. Please try logging in.",
      );
      return;
    }

    router.push(callbackUrl);
    router.refresh();
  };

  const handleGoogleSignIn = () => {
    signIn("google", { callbackUrl });
  };

  return (
    <section className="arena-panel w-full max-w-md p-6 sm:p-8">
      <div className="mb-7 text-center">
        <div className="mx-auto mb-5 grid h-12 w-12 place-items-center rounded-xl border border-border-subtle bg-surface-card">
          <ShieldCheck className="h-6 w-6 text-brand-gold" />
        </div>
        <h1 className="font-display text-2xl font-bold text-text-primary sm:text-3xl">
          {isSignIn ? "Welcome back" : "Create your account"}
        </h1>
        <p className="mt-2 text-sm leading-6 text-text-secondary">
          {isSignIn
            ? "Sign in to access your decks, quota, and linked profiles."
            : "Save your recommendations and link player profiles to your account."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {!isSignIn && (
          <div>
            <label
              htmlFor="name"
              className="mb-2 block text-sm font-bold text-text-secondary"
            >
              Name
            </label>
            <div className="relative">
              <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field pl-10"
                autoComplete="name"
                placeholder="Your name"
              />
            </div>
          </div>
        )}

        <div>
          <label
            htmlFor="email"
            className="mb-2 block text-sm font-bold text-text-secondary"
          >
            Email
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field pl-10"
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="password"
            className="mb-2 block text-sm font-bold text-text-secondary"
          >
            Password
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field pl-10"
              autoComplete={isSignIn ? "current-password" : "new-password"}
              placeholder={isSignIn ? "Your password" : "At least 8 characters"}
              minLength={isSignIn ? undefined : 8}
              required
            />
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-border-accent bg-brand-red/10 px-4 py-3 text-sm font-semibold text-[#ff9c9c]">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-primary min-h-12 w-full px-5 text-sm disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              {isSignIn ? "Signing in" : "Creating account"}
            </>
          ) : (
            <>
              {isSignIn ? "Sign in" : "Create account"}
              <ChevronRight className="h-5 w-5" />
            </>
          )}
        </button>
      </form>

      {googleEnabled && (
        <>
          <div className="my-6 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.14em] text-text-muted">
            <span className="h-px flex-1 bg-border-subtle" />
            or
            <span className="h-px flex-1 bg-border-subtle" />
          </div>

          <button
            type="button"
            onClick={handleGoogleSignIn}
            className="btn-secondary w-full min-h-12 gap-3 px-4 text-sm font-bold"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </button>
        </>
      )}

      <p className="mt-6 text-center text-sm text-text-secondary">
        {isSignIn ? "Don't have an account?" : "Already have an account?"}{" "}
        <button
          type="button"
          onClick={toggleMode}
          className="font-bold text-brand-gold transition-colors hover:text-brand-cyan"
        >
          {isSignIn ? "Sign up" : "Sign in"}
        </button>
      </p>

      <p className="mt-3 text-center">
        <Link
          href="/"
          className="text-xs font-medium text-text-muted transition-colors hover:text-text-secondary"
        >
          Back to home
        </Link>
      </p>
    </section>
  );
}
