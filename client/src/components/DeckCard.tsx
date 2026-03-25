'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, TrendingUp, Shield, Sparkles } from 'lucide-react';

interface DeckRecommendation {
  cards: string[];
  archetype: string;
  win_rate: number;
  level_fit_score: number;
  overall_score: number;
  explanation: string;
  short_summary: string;
}

interface DeckCardProps {
  deck: DeckRecommendation;
  rank: number;
}

export default function DeckCard({ deck, rank }: DeckCardProps) {
  const [expanded, setExpanded] = useState(false);

  const winPct = (deck.win_rate * 100).toFixed(1);
  const levelPct = (deck.level_fit_score * 100).toFixed(0);
  const overallPct = (deck.overall_score * 100).toFixed(0);

  const archetypeClass = `badge badge-${deck.archetype.replace('_', '-')}`;

  return (
    <div className="glass-card overflow-hidden">
      {/* Header bar */}
      <div className="bg-gradient-card px-6 py-4 flex items-center justify-between border-b border-border-subtle">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-hero flex items-center justify-center text-sm font-bold text-white">
            {rank}
          </div>
          <div>
            <div className="font-bold text-text-primary">{deck.short_summary}</div>
          </div>
        </div>
        <span className={archetypeClass}>
          {deck.archetype.replace('_', ' ')}
        </span>
      </div>

      {/* Cards grid */}
      <div className="px-6 py-5">
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
          {deck.cards.map((card, idx) => (
            <div
              key={idx}
              className="flex flex-col items-center gap-1.5"
            >
              <div className="w-full aspect-square rounded-xl bg-surface-elevated border border-border-subtle
                flex items-center justify-center text-xs text-text-secondary font-medium
                hover:border-brand-red/30 hover:bg-surface-card-hover transition-all duration-200 cursor-default">
                <span className="text-center leading-tight px-1 text-[0.65rem]">
                  {card}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Score bars */}
      <div className="px-6 pb-5 grid grid-cols-3 gap-4">
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-text-muted flex items-center gap-1">
              <TrendingUp className="h-3 w-3" /> Win Rate
            </span>
            <span className="text-xs font-bold text-accent-green">{winPct}%</span>
          </div>
          <div className="score-bar">
            <div className="score-bar-fill" style={{ width: `${winPct}%` }} />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-text-muted flex items-center gap-1">
              <Shield className="h-3 w-3" /> Level Fit
            </span>
            <span className="text-xs font-bold text-brand-blue">{levelPct}%</span>
          </div>
          <div className="score-bar">
            <div className="score-bar-fill" style={{ width: `${levelPct}%` }} />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-text-muted flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> Overall
            </span>
            <span className="text-xs font-bold text-gradient">{overallPct}%</span>
          </div>
          <div className="score-bar">
            <div className="score-bar-fill" style={{ width: `${overallPct}%` }} />
          </div>
        </div>
      </div>

      {/* Expandable explanation */}
      <div className="border-t border-border-subtle">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-6 py-3 flex items-center justify-between text-sm text-text-secondary
            hover:bg-surface-card-hover transition-colors cursor-pointer"
        >
          <span className="font-medium">
            {expanded ? 'Hide Details' : 'Why this deck?'}
          </span>
          {expanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>

        {expanded && (
          <div className="px-6 pb-5 animate-fade-in-up">
            <p className="text-sm text-text-secondary leading-relaxed">
              {deck.explanation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
