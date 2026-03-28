'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '../../components/Navbar';
import { Search, ChevronRight, Loader2 } from 'lucide-react';

const ARCHETYPES = [
  { value: '', label: 'Any Archetype', color: 'text-text-secondary' },
  { value: 'cycle', label: 'Cycle', color: 'text-[#4ade80]' },
  { value: 'beatdown', label: 'Beatdown', color: 'text-[#fb923c]' },
  { value: 'bridge_spam', label: 'Bridge Spam', color: 'text-[#facc15]' },
  { value: 'control', label: 'Control', color: 'text-[#7dd3fc]' },
  { value: 'bait', label: 'Bait', color: 'text-[#c084fc]' },
];

export default function RecommendPage() {
  const router = useRouter();
  const [playerTag, setPlayerTag] = useState('');
  const [archetype, setArchetype] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit: React.SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setError('');

    const cleanTag = playerTag.trim().replace(/^#/, '');
    if (!cleanTag) {
      setError('Please enter a player tag');
      return;
    }

    setLoading(true);

    try {
      // Step 1: Fetch and cache the player's data
      const playerRes = await fetch(`/api/player/${encodeURIComponent(cleanTag)}`);
      if (!playerRes.ok) {
        const data = await playerRes.json().catch(() => ({}));
        throw new Error(data.error || `Player not found (${playerRes.status})`);
      }
      const playerData = await playerRes.json();
      const resolvedTag = String(playerData.tag || `#${cleanTag}`).replace(/^#/, '');

      // Step 2: Navigate to results with query params
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
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="grow flex items-center justify-center py-16 px-4">
        <div className="w-full max-w-lg animate-fade-in-up">
          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-4xl md:text-5xl font-black mb-3">
              <span className="text-gradient">Get Your Decks</span>
            </h1>
            <p className="text-text-secondary text-lg">
              Enter your player tag to receive AI-powered recommendations
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Player tag input */}
            <div>
              <label htmlFor="player-tag" className="block text-sm font-medium text-text-secondary mb-2">
                Player Tag
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted font-bold text-lg">
                  #
                </span>
                <input
                  id="player-tag"
                  type="text"
                  value={playerTag}
                  onChange={(e) => setPlayerTag(e.target.value.toUpperCase())}
                  placeholder="ABC123XY"
                  className="input-field pl-9! uppercase tracking-wider font-mono"
                  maxLength={15}
                  autoComplete="off"
                  autoFocus
                />
                <Search className="absolute right-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-muted" />
              </div>
              <p className="mt-1.5 text-xs text-text-muted">
                Find your tag at Settings, then Player Tag in Clash Royale. Use 0, not O.
              </p>
            </div>

            {/* Archetype selector */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Archetype Preference
                <span className="text-text-muted font-normal ml-1">(optional)</span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                {ARCHETYPES.map((arch) => (
                  <button
                    key={arch.value}
                    type="button"
                    onClick={() => setArchetype(arch.value)}
                    className={`
                      py-2.5 px-3 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer
                      border
                      ${archetype === arch.value
                        ? 'bg-surface-elevated border-brand-red text-text-primary shadow-[0_0_12px_rgba(230,57,70,0.15)]'
                        : 'bg-surface-card border-border-subtle text-text-secondary hover:bg-surface-card-hover hover:border-border-accent'
                      }
                    `}
                  >
                    {arch.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-4 rounded-xl bg-[rgba(230,57,70,0.1)] border border-border-accent text-sm text-brand-red">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full text-lg py-4! flex items-center justify-center gap-2
                disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Get Recommendations
                  <ChevronRight className="h-5 w-5" />
                </>
              )}
            </button>
          </form>

          {/* Usage info */}
          <div className="mt-8 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-card border border-border-subtle">
              <div className="w-2 h-2 rounded-full bg-accent-green" />
              <span className="text-xs text-text-secondary">Free during beta</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
