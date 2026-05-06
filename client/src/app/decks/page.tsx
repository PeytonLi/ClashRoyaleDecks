import Link from "next/link";
import Navbar from "../../components/Navbar";
import { BarChart3, Crown, Flame, Zap } from "lucide-react";

const decks = [
  {
    name: "Hog EQ Cycle",
    archetype: "cycle",
    cards: ["Hog", "Earthquake", "Firecracker", "Cannon", "Log", "Skeletons", "Ice Spirit", "Knight"],
    score: "88",
    icon: Zap,
  },
  {
    name: "Lava Miner",
    archetype: "beatdown",
    cards: ["Lava", "Balloon", "Miner", "Mega Minion", "Tombstone", "Arrows", "Fireball", "Guards"],
    score: "84",
    icon: Flame,
  },
  {
    name: "Royal Recruits Bait",
    archetype: "bait",
    cards: ["Recruits", "Hogs", "Flying Machine", "Zappies", "Goblin Cage", "Arrows", "Barbarian Barrel", "Fireball"],
    score: "81",
    icon: Crown,
  },
];

export default function DecksPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="page-frame grow py-12">
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="eyebrow mb-4">
              <BarChart3 className="h-4 w-4" />
              Meta board
            </div>
            <h1 className="font-display text-4xl font-bold text-text-primary md:text-5xl">Popular deck structures</h1>
            <p className="mt-3 max-w-2xl leading-7 text-text-secondary">
              Static examples of the archetypes the recommender currently scores. Personalized scans use your player data.
            </p>
          </div>
          <Link href="/recommend" className="btn-primary px-5">
            Scan my profile
          </Link>
        </div>

        <section className="grid gap-5">
          {decks.map((deck, index) => {
            const Icon = deck.icon;
            return (
              <article key={deck.name} className={`glass-card p-5 animate-fade-in-up-delay-${index + 1}`}>
                <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-11 w-11 place-items-center rounded-[8px] bg-gradient-card">
                      <Icon className="h-5 w-5 text-brand-gold" />
                    </div>
                    <div>
                      <h2 className="font-display text-2xl font-bold text-text-primary">{deck.name}</h2>
                      <span className={`badge badge-${deck.archetype}`}>{deck.archetype}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-display text-3xl font-bold text-gradient">{deck.score}</div>
                    <div className="text-xs font-bold uppercase tracking-wide text-text-muted">Meta score</div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-2 sm:grid-cols-8">
                  {deck.cards.map((card) => (
                    <div key={card} className="card-token aspect-square">
                      {card}
                    </div>
                  ))}
                </div>
              </article>
            );
          })}
        </section>
      </main>
    </div>
  );
}
