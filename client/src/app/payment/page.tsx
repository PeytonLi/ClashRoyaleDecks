import Link from 'next/link';
import Navbar from '../../components/Navbar';
import { Check, CreditCard, ShieldCheck } from 'lucide-react';

const perks = [
  'Unlimited deck recommendations',
  'All archetype filters',
  'Card-level explanations',
  'Weekly meta-updated model',
];

export default function PaymentPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="page-frame grid grow items-center gap-8 py-12 lg:grid-cols-[0.85fr_1.15fr]">
        <section>
          <div className="eyebrow mb-5">
            <CreditCard className="h-4 w-4" />
            Premium access
          </div>
          <h1 className="font-display text-4xl font-bold leading-tight text-text-primary md:text-6xl">
            Unlimited recommendations are planned for launch.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-text-secondary">
            The Stripe checkout flow is not active yet. Free beta scans remain available while premium billing is finished.
          </p>
          <Link href="/recommend" className="btn-primary mt-8 px-5">
            Keep scanning
          </Link>
        </section>

        <section className="arena-panel p-5 sm:p-7">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <p className="font-display text-sm uppercase tracking-[0.16em] text-brand-gold">Lifetime plan</p>
              <div className="mt-2 flex items-end gap-2">
                <span className="font-display text-5xl font-bold text-gradient">$4.99</span>
                <span className="pb-2 text-sm text-text-muted">one-time</span>
              </div>
            </div>
            <ShieldCheck className="h-9 w-9 text-brand-cyan" />
          </div>

          <div className="grid gap-3">
            {perks.map((perk) => (
              <div key={perk} className="flex items-center gap-3 border-b border-border-subtle py-3">
                <Check className="h-4 w-4 text-accent-green" />
                <span className="font-semibold text-text-secondary">{perk}</span>
              </div>
            ))}
          </div>

          <button type="button" className="btn-secondary mt-7 min-h-12 w-full px-5" disabled>
            Stripe integration pending
          </button>
        </section>
      </main>
    </div>
  );
}
