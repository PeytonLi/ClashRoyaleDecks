import Link from "next/link";
import { auth } from "@/auth";
import Navbar from "../components/Navbar";
import {
  Activity,
  BarChart3,
  ChevronRight,
  Crown,
  Layers3,
  LogIn,
  LogOut,
  UserPlus,
  ShieldCheck,
  Sparkles,
  Swords,
  Trophy,
} from "lucide-react";

const deckCards = [
  "Hog Rider",
  "Musketeer",
  "Ice Spirit",
  "Cannon",
  "Fireball",
  "Log",
  "Skeletons",
  "Knight",
];

const signals = [
  { label: "Collection fit", value: "94%", icon: ShieldCheck },
  { label: "Meta pressure", value: "71%", icon: Activity },
  { label: "Cycle speed", value: "2.8", icon: Layers3 },
];

const features = [
  {
    title: "Player-aware picks",
    copy: "Recommendations are scored against your actual card levels, arena, and trophy range.",
    icon: Crown,
  },
  {
    title: "Synergy scoring",
    copy: "The model weighs winning card pairs and archetype structure instead of only copying top decks.",
    icon: Sparkles,
  },
  {
    title: "Meta refresh",
    copy: "Top-ladder data feeds the recommender so stale decks drift out of the shortlist.",
    icon: BarChart3,
  },
];

export default async function Home() {
  const session = await auth();

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="grow">
        <section className="page-frame grid items-center gap-10 py-12 lg:grid-cols-[0.95fr_1.05fr] lg:py-20">
          <div className="animate-fade-in-up">
            <div className="eyebrow mb-6">
              <Swords className="h-4 w-4" />
              Clash Royale deck intelligence
            </div>

            <h1 className="font-display max-w-3xl text-5xl font-bold leading-[0.95] text-text-primary md:text-7xl">
              CR Deck Lab
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-text-secondary">
              Scan a player profile, compare the card collection against current
              ladder patterns, and get three decks that are actually playable
              for that account.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/recommend" className="btn-primary px-6 text-base">
                Run deck scan
                <ChevronRight className="h-5 w-5" />
              </Link>
              <Link href="/decks" className="btn-secondary px-6 text-base">
                View meta board
              </Link>
            </div>

            {session ? (
              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
                <p className="text-sm font-semibold text-text-secondary">
                  Logged in as{" "}
                  <span className="text-text-primary">
                    {session.user?.email}
                  </span>
                </p>
                <Link
                  href="/api/auth/signout"
                  className="btn-secondary px-6 text-base"
                >
                  <LogOut className="h-5 w-5" />
                  Logout
                </Link>
              </div>
            ) : (
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <Link href="/signup" className="btn-primary px-6 text-base">
                  <UserPlus className="h-5 w-5" />
                  Sign up
                </Link>
                <Link href="/login" className="btn-secondary px-6 text-base">
                  <LogIn className="h-5 w-5" />
                  Sign in
                </Link>
              </div>
            )}

            <div className="mt-8 grid max-w-xl grid-cols-3 gap-3">
              {signals.map((signal) => {
                const Icon = signal.icon;
                return (
                  <div
                    key={signal.label}
                    className="border-l border-border-subtle pl-3"
                  >
                    <Icon className="mb-2 h-4 w-4 text-brand-gold" />
                    <div className="font-display text-2xl font-bold text-text-primary">
                      {signal.value}
                    </div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                      {signal.label}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="arena-panel p-4 sm:p-6 lg:p-8">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="font-display text-sm uppercase tracking-[0.16em] text-brand-gold">
                  Live deck readout
                </div>
                <div className="mt-1 text-sm text-text-secondary">
                  Cycle-control candidate for ladder climb
                </div>
              </div>
              <span className="badge badge-cycle">Cycle</span>
            </div>

            <div className="grid grid-cols-4 gap-2 sm:gap-3">
              {deckCards.map((card) => (
                <div key={card} className="card-token aspect-[1/1.08]">
                  {card}
                </div>
              ))}
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ["Win rate", "58.4%", "58%"],
                ["Level fit", "93%", "93%"],
                ["Overall", "88%", "88%"],
              ].map(([label, value, width]) => (
                <div key={label}>
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-semibold uppercase tracking-wide text-text-muted">
                      {label}
                    </span>
                    <span className="font-display font-bold text-text-primary">
                      {value}
                    </span>
                  </div>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-y border-border-subtle bg-surface-card/40 py-12">
          <div className="page-frame grid gap-4 md:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <article
                  key={feature.title}
                  className={`glass-card p-5 animate-fade-in-up-delay-${index + 1}`}
                >
                  <Icon className="mb-5 h-6 w-6 text-brand-cyan" />
                  <h2 className="font-display text-xl font-bold text-text-primary">
                    {feature.title}
                  </h2>
                  <p className="mt-3 leading-7 text-text-secondary">
                    {feature.copy}
                  </p>
                </article>
              );
            })}
          </div>
        </section>

        <section className="page-frame grid gap-6 py-12 md:grid-cols-[0.75fr_1.25fr]">
          <div>
            <div className="eyebrow mb-4">
              <Trophy className="h-4 w-4" />
              Scoring model
            </div>
            <h2 className="font-display text-3xl font-bold text-text-primary">
              Four signals, one ranked shortlist.
            </h2>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              "Collaborative filtering",
              "Card-pair synergy",
              "Level fitness",
              "Meta win rate",
            ].map((item) => (
              <div
                key={item}
                className="flex items-center gap-3 border-b border-border-subtle py-3"
              >
                <div className="h-2.5 w-2.5 rounded-full bg-brand-gold" />
                <span className="font-semibold text-text-secondary">
                  {item}
                </span>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-border-subtle py-6">
        <div className="page-frame flex flex-col justify-between gap-3 text-sm text-text-muted sm:flex-row">
          <span>CR Deck Lab</span>
          <span>
            Not affiliated with Supercell. Clash Royale is a trademark of
            Supercell Oy.
          </span>
        </div>
      </footer>
    </div>
  );
}
