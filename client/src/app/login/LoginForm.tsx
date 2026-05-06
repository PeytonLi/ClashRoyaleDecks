'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { signIn } from 'next-auth/react';
import { ChevronRight, Loader2, Mail, ShieldCheck } from 'lucide-react';

export default function LoginForm({
  callbackUrl,
  googleEnabled,
}: {
  callbackUrl: string;
  googleEnabled: boolean;
}) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    const result = await signIn('credentials', {
      email,
      password,
      redirect: false,
      callbackUrl,
    });

    setLoading(false);

    if (result?.error) {
      setError('Invalid email or password.');
      return;
    }

    router.push(callbackUrl);
    router.refresh();
  };

  return (
    <section className="arena-panel w-full max-w-md p-5 sm:p-7">
      <div className="mb-6">
        <div className="mb-4 grid h-12 w-12 place-items-center rounded-[8px] border border-border-subtle bg-surface-card">
          <ShieldCheck className="h-6 w-6 text-brand-gold" />
        </div>
        <h1 className="font-display text-3xl font-bold text-text-primary">Log in</h1>
        <p className="mt-2 text-sm leading-6 text-text-secondary">
          Keep scans, quota, and linked player profiles scoped to your account.
        </p>
      </div>

      {googleEnabled && (
        <>
          <button
            type="button"
            onClick={() => signIn('google', { callbackUrl })}
            className="btn-secondary w-full px-4"
          >
            <Mail className="h-4 w-4" />
            Continue with Google
          </button>

          <div className="my-5 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.14em] text-text-muted">
            <span className="h-px flex-1 bg-border-subtle" />
            or
            <span className="h-px flex-1 bg-border-subtle" />
          </div>
        </>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="mb-2 block text-sm font-bold text-text-secondary">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="input-field"
            autoComplete="email"
            required
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-2 block text-sm font-bold text-text-secondary">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="input-field"
            autoComplete="current-password"
            required
          />
        </div>

        {error && (
          <div className="rounded-[8px] border border-border-accent bg-brand-red/10 px-4 py-3 text-sm font-semibold text-[#ff9c9c]">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-primary min-h-12 w-full px-5 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Signing in
            </>
          ) : (
            <>
              Log in
              <ChevronRight className="h-5 w-5" />
            </>
          )}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-text-secondary">
        New here?{' '}
        <Link href={`/signup?callbackUrl=${encodeURIComponent(callbackUrl)}`} className="font-bold text-brand-gold">
          Create an account
        </Link>
      </p>
    </section>
  );
}
