'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '../../components/Navbar';
import { Activity, ChevronRight, Loader2, Search, SlidersHorizontal, Trophy } from 'lucide-react';

const ARCHETYPES = [
  { value: '', label: 'Any', badge: 'badge-control' },
  { value: 'cycle', label: 'Cycle', badge: 'badge-cycle' },
  { value: 'beatdown', label: 'Beatdown', badge: 'badge-beatdown' },
  { value: 'bridge_spam', label: 'Bridge Spam', badge: 'badge-bridge-spam' },
  { value: 'control', label: 'Control', badge: 'badge-control' },
  { value: 'bait', label: 'Bait', badge: 'badge-bait' },
];

export default function RecommendPage() {
  const router = useRouter();
  const [playerTag, setPlayerTag] = useState('');
  const [archetype, setArchetype] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setError('');

    const cleanTag = playerTag.trim().replace(/^#/, '');
    if (!cleanTag) {
      setError('Please enter a player tag.');
      return;
    }

    setLoading(true);

    try {
      const playerRes = await fetch(`/api/player/${encodeURIComponent(cleanTag)}`);
      if (!playerRes.ok) {
        const data = await playerRes.json().catch(() => ({}));
        throw new Error(data.error || `Player not found (${playerRes.status})`);
      }

      const playerData = await playerRes.json();
      const resolvedTag = String(playerData.tag || `#${cleanTag}`).replace(/^#/, '');
      const params = new URLSearchParams({ tag: resolvedTag });
      if (archetype) params.set('archetype', archetype);
      router.push(`/results?${params.toString()}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setError(message);
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="page-frame grid grow items-center gap-8 py-10 lg:grid-cols-[0.78fr_1.22fr] lg:py-16">
        <section className="animate-fade-in-up">
          <div className="eyebrow mb-5">
            <Activity className="h-4 w-4" />
            Deck scan
          </div>
          <h1 className="font-display text-4xl font-bold leading-tight text-text-primary md:text-6xl">
            Find the deck your collection can actually support.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-text-secondary">
            The scan checks your profile first, then scores recommendation candidates against card levels, archetype preference, and current meta pressure.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {[
              ['1', 'Fetch profile', 'Card levels, trophies, and arena.'],
              ['2', 'Score decks', 'Meta, synergy, and level fit.'],
              ['3', 'Explain picks', 'Three ranked recommendations.'],
            ].map(([step, title, copy]) => (
              <div key={step} className="flex gap-3 border-l border-border-subtle pl-4">
                <span className="font-display text-xl font-bold text-brand-gold">{step}</span>
                <div>
                  <div className="font-semibold text-text-primary">{title}</div>
                  <div className="text-sm text-text-muted">{copy}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="arena-panel p-4 sm:p-6 lg:p-8">
          <div className="mb-6 flex items-center justify-between gap-4">
            <div>
              <div className="font-display text-sm uppercase tracking-[0.16em] text-brand-gold">
                Player input
              </div>
              <p className="mt-1 text-sm text-text-secondary">Paste the tag shown on your Clash Royale profile.</p>
            </div>
            <Trophy className="hidden h-8 w-8 text-brand-gold sm:block" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="player-tag" className="mb-2 block text-sm font-bold text-text-secondary">
                Player Tag
              </label>
              <div className="relative">
                <span className="font-display absolute left-4 top-1/2 -translate-y-1/2 text-lg font-bold text-brand-gold">
                  #
                </span>
                <input
                  id="player-tag"
                  type="text"
                  value={playerTag}
                  onChange={(e) => setPlayerTag(e.target.value.toUpperCase())}
                  placeholder="ABC123XY"
                  className="input-field pl-9 pr-12 font-display uppercase tracking-[0.12em]"
                  maxLength={15}
                  autoComplete="off"
                  autoFocus
                />
                <Search className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-text-muted" />
              </div>
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between gap-3">
                <label className="text-sm font-bold text-text-secondary">Archetype Preference</label>
                <SlidersHorizontal className="h-4 w-4 text-text-muted" />
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {ARCHETYPES.map((arch) => {
                  const selected = archetype === arch.value;
                  return (
                    <button
                      key={arch.value}
                      type="button"
                      onClick={() => setArchetype(arch.value)}
                      className={`min-h-11 rounded-[8px] border px-3 text-sm font-bold transition-colors ${
                        selected
                          ? 'border-brand-gold/60 bg-brand-gold/10 text-text-primary'
                          : 'border-border-subtle bg-surface-card text-text-secondary hover:bg-surface-card-hover hover:text-text-primary'
                      }`}
                    >
                      {arch.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {error && (
              <div className="rounded-[8px] border border-border-accent bg-brand-red/10 px-4 py-3 text-sm font-semibold text-[#ff9c9c]">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary min-h-14 w-full px-5 text-base disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Checking profile
                </>
              ) : (
                <>
                  Get recommendations
                  <ChevronRight className="h-5 w-5" />
                </>
              )}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
