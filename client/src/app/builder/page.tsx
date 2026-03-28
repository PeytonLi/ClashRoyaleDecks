import Link from 'next/link';
import Navbar from '../../components/Navbar';
import { Layers } from 'lucide-react';

export default function BuilderPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="grow flex items-center justify-center py-16 px-4">
        <div className="text-center max-w-lg animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface-card border border-border-subtle mb-6">
            <Layers className="h-8 w-8 text-text-secondary" />
          </div>

          <h1 className="text-3xl font-bold text-text-primary mb-3">
            Deck Builder &mdash; Coming Soon
          </h1>

          <p className="text-text-secondary mb-8 leading-relaxed">
            We&apos;re building an interactive deck builder that lets you select
            cards and get ML-powered recommendations. For now, use the
            player-tag-based recommendations.
          </p>

          <Link href="/recommend" className="btn-primary text-lg py-3.5! px-10!">
            Get Recommendations
          </Link>

          <div className="mt-4">
            <Link
              href="/"
              className="text-sm text-text-muted hover:text-text-secondary transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
