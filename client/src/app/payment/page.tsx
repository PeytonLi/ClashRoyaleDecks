import Link from 'next/link';
import Navbar from '../../components/Navbar';
import { CreditCard } from 'lucide-react';

export default function PaymentPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="grow flex items-center justify-center py-16 px-4">
        <div className="text-center max-w-lg animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-hero mb-6">
            <CreditCard className="h-8 w-8 text-white" />
          </div>

          <h1 className="text-3xl font-bold text-text-primary mb-3">
            Unlock Unlimited Recommendations
          </h1>

          <div className="mb-6 px-4 py-3 rounded-xl bg-surface-card border border-border-subtle text-sm text-text-secondary">
            We&apos;re in beta &mdash; payment integration is coming soon.
            Free usage is available while we finalize premium features.
          </div>

          <p className="text-text-secondary mb-8 leading-relaxed">
            Get unlimited AI-powered deck recommendations, priority meta updates,
            and archetype analysis.
          </p>

          {/* Pricing card */}
          <div className="glass-card p-8 mb-6 bg-gradient-card animate-pulse-glow">
            <div className="text-4xl font-black text-gradient mb-1">
              $4.99
            </div>
            <div className="text-text-muted text-sm mb-6">One-time payment · Lifetime access</div>

            <ul className="space-y-3 text-left text-sm text-text-secondary mb-8">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-green" />
                Unlimited deck recommendations
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-green" />
                All 5 archetype filters
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-green" />
                Detailed card-level explanations
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-green" />
                Weekly meta-updated model
              </li>
            </ul>

            <button
              className="btn-primary w-full text-lg !py-3.5"
              disabled
            >
              Coming Soon — Stripe Integration
            </button>
          </div>

          <Link
            href="/"
            className="text-sm text-text-muted hover:text-text-secondary transition-colors"
          >
            Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
}
