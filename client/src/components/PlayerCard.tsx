'use client';

import { Trophy, Crown, Layers } from 'lucide-react';

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
  return (
    <div className="glass-card p-6 bg-gradient-card">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {/* Avatar placeholder */}
          <div className="w-14 h-14 rounded-xl bg-gradient-hero flex items-center justify-center shrink-0">
            <Crown className="h-7 w-7 text-white" />
          </div>

          <div>
            <h2 className="text-xl font-bold text-text-primary">{player.name}</h2>
            <p className="text-sm text-text-muted font-mono">#{tag}</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Trophy className="h-4 w-4 text-accent-yellow" />
            <div>
              <div className="text-lg font-bold text-text-primary">{player.trophies.toLocaleString()}</div>
              <div className="text-xs text-text-muted">Trophies</div>
            </div>
          </div>

          <div className="w-px h-10 bg-border-subtle" />

          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-brand-blue" />
            <div>
              <div className="text-lg font-bold text-text-primary">{player.arena_name}</div>
              <div className="text-xs text-text-muted">
                Avg Lv{player.avg_card_level} · Max Lv{player.max_card_level}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
