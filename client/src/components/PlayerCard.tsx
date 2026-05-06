'use client';

import { Crown, Layers3, Trophy } from 'lucide-react';

interface PlayerSummary {
  name: string;
  trophies: number;
  arena_name: string;
  max_card_level: number;
  avg_card_level: number;
}

interface PlayerCardProps {
  player: PlayerSummary;
  tag: string;
}

export default function PlayerCard({ player, tag }: PlayerCardProps) {
  const stats = [
    { label: 'Trophies', value: player.trophies.toLocaleString(), icon: Trophy },
    { label: 'Arena', value: player.arena_name, icon: Crown },
    { label: 'Cards', value: `Avg ${player.avg_card_level} / Max ${player.max_card_level}`, icon: Layers3 },
  ];

  return (
    <section className="arena-panel p-4 sm:p-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex min-w-0 items-center gap-4">
          <div className="grid h-14 w-14 shrink-0 place-items-center rounded-[8px] bg-gradient-hero">
            <Crown className="h-7 w-7 text-brand-ink" />
          </div>

          <div className="min-w-0">
            <p className="font-display text-xs font-bold uppercase tracking-[0.16em] text-brand-gold">Player profile</p>
            <h2 className="truncate font-display text-2xl font-bold text-text-primary">{player.name}</h2>
            <p className="font-display text-sm text-text-muted">#{tag}</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[560px]">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="border-l border-border-subtle pl-3">
                <Icon className="mb-2 h-4 w-4 text-brand-cyan" />
                <div className="truncate font-display text-lg font-bold text-text-primary">{stat.value}</div>
                <div className="text-xs font-bold uppercase tracking-wide text-text-muted">{stat.label}</div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
