'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Navbar from '../../components/Navbar';
import DeckCard from '../../components/DeckCard';
import PlayerCard from '../../components/PlayerCard';
import { AlertCircle, ArrowLeft, Loader2, RefreshCw } from 'lucide-react';

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
  required_cards?: string[];
}

function ResultsLoading() {
  return (
    <div className="page-frame flex grow items-center justify-center py-12">
      <div className="w-full max-w-3xl text-center">
        <div className="mx-auto mb-6 grid h-16 w-16 place-items-center rounded-[8px] bg-gradient-hero">
          <Loader2 className="h-8 w-8 animate-spin text-brand-ink" />
        </div>
        <h2 className="font-display text-3xl font-bold text-text-primary">Scoring deck candidates</h2>
        <p className="mt-2 text-text-secondary">Comparing your profile against current meta patterns.</p>

        <div className="mt-10 grid gap-4">
          <div className="h-32 rounded-[8px] border border-border-subtle animate-shimmer" />
          <div className="h-32 rounded-[8px] border border-border-subtle animate-shimmer" />
          <div className="h-32 rounded-[8px] border border-border-subtle animate-shimmer" />
        </div>
      </div>
    </div>
  );
}

function EmptyState({ title, message, payment }: { title: string; message: string; payment?: boolean }) {
  return (
    <div className="page-frame flex grow items-center justify-center py-12">
      <div className="arena-panel max-w-lg p-6 text-center">
        <div className="mx-auto mb-5 grid h-14 w-14 place-items-center rounded-[8px] border border-border-subtle bg-surface-card">
          <AlertCircle className="h-7 w-7 text-brand-gold" />
        </div>
        <h2 className="font-display text-3xl font-bold text-text-primary">{title}</h2>
        <p className="mt-3 leading-7 text-text-secondary">{message}</p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Link href="/recommend" className="btn-primary px-5">
            <RefreshCw className="h-4 w-4" />
            New scan
          </Link>
          {payment ? (
            <Link href="/payment" className="btn-secondary px-5">
              View premium
            </Link>
          ) : (
            <Link href="/" className="btn-secondary px-5">
              Home
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultsContent() {
  const searchParams = useSearchParams();
  const tag = searchParams.get('tag') || '';
  const archetype = searchParams.get('archetype') || '';
  const requiredCard = searchParams.get('required_card') || '';

  const [data, setData] = useState<RecommendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!tag) {
      setError('No player tag provided.');
      setLoading(false);
      return;
    }

    const fetchRecommendations = async () => {
      try {
        const body: {
          player_tag: string;
          archetype_preference?: string;
          required_cards?: string[];
        } = { player_tag: `#${tag}` };
        if (archetype) body.archetype_preference = archetype;
        if (requiredCard.trim()) body.required_cards = [requiredCard.trim()];

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
        const message = err instanceof Error ? err.message : 'Failed to load recommendations.';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [tag, archetype, requiredCard]);

  if (loading) return <ResultsLoading />;

  if (error === 'FREE_LIMIT_REACHED') {
    return (
      <EmptyState
        title="Free limit reached"
        message="You have used the available free recommendations for this account. Premium access is planned for unlimited scans."
        payment
      />
    );
  }

  if (error) {
    return <EmptyState title="Scan failed" message={error} />;
  }

  if (!data) return null;

  const requiredCards = data.required_cards?.length
    ? data.required_cards
    : requiredCard.trim()
      ? [requiredCard.trim()]
      : [];

  return (
    <main className="grow py-8">
      <div className="page-frame">
        <Link
          href="/recommend"
          className="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-text-muted transition-colors hover:text-text-secondary"
        >
          <ArrowLeft className="h-4 w-4" />
          New scan
        </Link>

        <div className="animate-fade-in-up">
          <PlayerCard player={data.player_summary} tag={tag} />
        </div>

        <div className="my-8 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <div className="eyebrow mb-3">Recommendations</div>
            <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
              Three decks ranked for this profile
            </h1>
          </div>
          <p className="max-w-sm text-sm leading-6 text-text-muted">
            Scores combine collection fit, synergy, ladder performance, and optional preferences.
          </p>
        </div>

        {requiredCards.length > 0 && (
          <div className="mb-5 rounded-[8px] border border-brand-gold/30 bg-brand-gold/10 px-4 py-3 text-sm font-semibold text-text-secondary">
            Every recommendation includes {requiredCards.join(', ')}.
          </div>
        )}

        <div className="grid gap-5">
          {data.recommendations.map((deck, idx) => (
            <div key={`${deck.short_summary}-${idx}`} className={`animate-fade-in-up-delay-${idx + 1}`}>
              <DeckCard deck={deck} rank={idx + 1} requiredCards={requiredCards} />
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

export default function ResultsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <Suspense fallback={<ResultsLoading />}>
        <ResultsContent />
      </Suspense>
    </div>
  );
}
