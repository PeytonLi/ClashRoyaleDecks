'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Navbar from '../../components/Navbar';
import DeckCard from '../../components/DeckCard';
import PlayerCard from '../../components/PlayerCard';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';

interface DeckRecommendation {
  cards: string[];
  archetype: string;
  win_rate: number;
  level_fit_score: number;
  overall_score: number;
  explanation: string;
  short_summary: string;
}

interface PlayerSummary {
  name: string;
  trophies: number;
  arena_name: string;
  max_card_level: number;
  avg_card_level: number;
}

interface RecommendResponse {
  recommendations: DeckRecommendation[];
  player_summary: PlayerSummary;
}

function ResultsContent() {
  const searchParams = useSearchParams();
  const tag = searchParams.get('tag') || '';
  const archetype = searchParams.get('archetype') || '';

  const [data, setData] = useState<RecommendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!tag) {
      setError('No player tag provided');
      setLoading(false);
      return;
    }

    const fetchRecommendations = async () => {
      try {
        const body: Record<string, string> = { player_tag: `#${tag}` };
        if (archetype) body.archetype_preference = archetype;

        const res = await fetch('/api/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          if (res.status === 402) {
            throw new Error('FREE_LIMIT_REACHED');
          }
          throw new Error(errData.error || `Error ${res.status}`);
        }

        const result = await res.json();
        setData(result);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load recommendations';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [tag, archetype]);

  if (loading) {
    return (
      <div className="grow flex items-center justify-center">
        <div className="text-center animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-hero mb-6">
            <Loader2 className="h-8 w-8 text-white animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">Analyzing your profile...</h2>
          <p className="text-text-secondary">Running ML model against top meta decks</p>

          {/* Shimmer skeleton */}
          <div className="mt-10 max-w-md mx-auto space-y-4">
            <div className="h-40 rounded-xl bg-surface-card animate-shimmer" />
            <div className="h-40 rounded-xl bg-surface-card animate-shimmer" />
            <div className="h-40 rounded-xl bg-surface-card animate-shimmer" />
          </div>
        </div>
      </div>
    );
  }

  if (error === 'FREE_LIMIT_REACHED') {
    return (
      <div className="grow flex items-center justify-center px-4">
        <div className="text-center max-w-md animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface-card border border-border-subtle mb-6">
            <AlertCircle className="h-8 w-8 text-accent-yellow" />
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">Free Limit Reached</h2>
          <p className="text-text-secondary mb-8">
            You&apos;ve used all 3 free recommendations. Upgrade to unlock unlimited access.
          </p>
          <Link href="/payment" className="btn-primary text-lg !py-3.5 !px-10">
            Upgrade Now
          </Link>
          <div className="mt-4">
            <Link href="/" className="text-sm text-text-muted hover:text-text-secondary transition-colors">
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="grow flex items-center justify-center px-4">
        <div className="text-center max-w-md animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[rgba(230,57,70,0.1)] mb-6">
            <AlertCircle className="h-8 w-8 text-brand-red" />
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">Something went wrong</h2>
          <p className="text-text-secondary mb-8">{error}</p>
          <Link href="/recommend" className="btn-primary">
            Try Again
          </Link>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <main className="grow py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Back link */}
        <Link
          href="/recommend"
          className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-secondary transition-colors mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          New search
        </Link>

        {/* Player summary */}
        <div className="animate-fade-in-up mb-8">
          <PlayerCard player={data.player_summary} tag={tag} />
        </div>

        {/* Recommendations */}
        <div className="mb-6 animate-fade-in-up">
          <h2 className="text-2xl font-bold text-text-primary">
            Your Recommendations
          </h2>
          <p className="text-text-secondary mt-1">
            3 decks optimized for your card levels and preferences
          </p>
        </div>

        <div className="space-y-6">
          {data.recommendations.map((deck, idx) => (
            <div
              key={idx}
              className={`animate-fade-in-up-delay-${idx + 1}`}
            >
              <DeckCard deck={deck} rank={idx + 1} />
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

export default function ResultsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <Suspense fallback={
        <div className="grow flex items-center justify-center">
          <Loader2 className="h-8 w-8 text-brand-red animate-spin" />
        </div>
      }>
        <ResultsContent />
      </Suspense>
    </div>
  );
}
