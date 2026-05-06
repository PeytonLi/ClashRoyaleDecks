'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Shield, Sparkles, TrendingUp } from 'lucide-react';

interface DeckSlot {
  card: string;
  card_key: string;
  form: 'base' | 'evolution' | 'hero' | 'champion';
  slot_type: 'normal' | 'evolution' | 'hero' | 'wild';
}

interface DeckRecommendation {
  cards: string[];
  slots?: DeckSlot[];
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
  requiredCards?: string[];
}

function pct(value: number, digits = 0) {
  return Math.max(0, Math.min(100, value * 100)).toFixed(digits);
}

function slotBadge(slot: DeckSlot) {
  if (slot.form === 'base') return null;

  const label = {
    evolution: 'Evo',
    hero: 'Hero',
    champion: 'Champ',
  }[slot.form];

  const color = {
    evolution: 'bg-brand-cyan text-brand-ink',
    hero: 'bg-brand-gold text-brand-ink',
    champion: 'bg-brand-red text-text-primary',
  }[slot.form];

  return (
    <div className="absolute right-1 top-1 flex flex-col items-end gap-1">
      <span className={`rounded px-1.5 py-0.5 text-[0.56rem] font-black uppercase leading-none ${color}`}>
        {label}
      </span>
      {slot.slot_type === 'wild' && (
        <span className="rounded border border-border-subtle bg-surface-primary/90 px-1.5 py-0.5 text-[0.52rem] font-black uppercase leading-none text-text-secondary">
          Wild
        </span>
      )}
    </div>
  );
}

export default function DeckCard({ deck, rank, requiredCards = [] }: DeckCardProps) {
  const [expanded, setExpanded] = useState(false);

  const winPct = pct(deck.win_rate, 1);
  const levelPct = pct(deck.level_fit_score);
  const overallPct = pct(deck.overall_score);
  const archetypeClass = `badge badge-${deck.archetype.replace('_', '-')}`;
  const requiredCardSet = new Set(
    requiredCards.flatMap((card) => {
      const lower = card.toLowerCase();
      return [lower, lower.replace(/^(evolution|evo|hero|champion|champ)\s+/, '')];
    }),
  );
  const displaySlots = deck.slots?.length
    ? deck.slots
    : deck.cards.map((card) => ({
        card,
        card_key: card.toLowerCase().replace(/\s+/g, '-'),
        form: 'base' as const,
        slot_type: 'normal' as const,
      }));

  const metrics = [
    { label: 'Win rate', value: `${winPct}%`, width: `${winPct}%`, icon: TrendingUp },
    { label: 'Level fit', value: `${levelPct}%`, width: `${levelPct}%`, icon: Shield },
    { label: 'Overall', value: `${overallPct}%`, width: `${overallPct}%`, icon: Sparkles },
  ];

  return (
    <article className="glass-card overflow-hidden">
      <div className="grid gap-5 p-4 sm:p-5 lg:grid-cols-[1fr_280px]">
        <div>
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div className="flex min-w-0 items-start gap-3">
              <div className="font-display grid h-10 w-10 shrink-0 place-items-center rounded-[8px] bg-gradient-hero text-base font-bold text-brand-ink">
                {rank}
              </div>
              <div className="min-w-0">
                <h3 className="font-display text-xl font-bold leading-tight text-text-primary">
                  {deck.short_summary}
                </h3>
                <p className="mt-1 text-sm text-text-muted">Ranked recommendation</p>
              </div>
            </div>
            <span className={archetypeClass}>{deck.archetype.replace('_', ' ')}</span>
          </div>

          <div className="grid grid-cols-4 gap-2 sm:grid-cols-8">
            {displaySlots.map((slot, idx) => (
              <div
                key={`${slot.card_key}-${slot.form}-${idx}`}
                className={`card-token relative aspect-square ${
                  requiredCardSet.has(slot.card.toLowerCase()) ? 'border-brand-gold/70 bg-brand-gold/15' : ''
                }`}
              >
                {slotBadge(slot)}
                <span className={slot.form === 'base' ? '' : 'pt-5'}>{slot.card}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid content-between gap-4 border-t border-border-subtle pt-4 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0">
          <div className="space-y-4">
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div key={metric.label}>
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-text-muted">
                      <Icon className="h-3.5 w-3.5" />
                      {metric.label}
                    </span>
                    <span className="font-display text-sm font-bold text-text-primary">{metric.value}</span>
                  </div>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: metric.width }} />
                  </div>
                </div>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => setExpanded((open) => !open)}
            className="btn-secondary min-h-11 w-full px-4 text-sm"
            aria-expanded={expanded}
          >
            {expanded ? 'Hide explanation' : 'Why this deck?'}
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-border-subtle bg-surface-card/50 px-4 py-4 sm:px-5">
          <p className="max-w-4xl text-sm leading-7 text-text-secondary">{deck.explanation}</p>
        </div>
      )}
    </article>
  );
}
