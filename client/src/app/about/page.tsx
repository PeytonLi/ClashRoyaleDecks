import Link from "next/link";
import Navbar from "../../components/Navbar";
import { Bot, Database, LineChart, ShieldCheck, Sparkles } from "lucide-react";

const modelSignals = [
  {
    title: "Collaborative filtering",
    copy: "Finds decks that successful players with similar collections are already using.",
    icon: Bot,
  },
  {
    title: "Synergy matrix",
    copy: "Rewards card pairs that repeatedly appear together in winning battle logs.",
    icon: Sparkles,
  },
  {
    title: "Level fitness",
    copy: "Penalizes cards that are too low level for a player's current ladder range.",
    icon: ShieldCheck,
  },
  {
    title: "Meta win rate",
    copy: "Keeps recommendations anchored to real top-ladder performance.",
    icon: LineChart,
  },
];

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="page-frame grow py-12">
        <section className="arena-panel p-6 md:p-8">
          <div className="max-w-3xl">
            <div className="eyebrow mb-5">
              <Database className="h-4 w-4" />
              Model pipeline
            </div>
            <h1 className="font-display text-4xl font-bold leading-tight text-text-primary md:text-6xl">
              Recommendations built from player context, not generic tier lists.
            </h1>
            <p className="mt-5 text-lg leading-8 text-text-secondary">
              CR Deck Lab fetches a player profile, scores candidate decks with a hybrid model, and returns a short ranked set with an explanation for each pick.
            </p>
            <Link href="/recommend" className="btn-primary mt-8 px-5">
              Run deck scan
            </Link>
          </div>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-2">
          {modelSignals.map((signal, index) => {
            const Icon = signal.icon;
            return (
              <article key={signal.title} className={`glass-card p-5 animate-fade-in-up-delay-${index + 1}`}>
                <Icon className="mb-5 h-6 w-6 text-brand-cyan" />
                <h2 className="font-display text-xl font-bold text-text-primary">{signal.title}</h2>
                <p className="mt-3 leading-7 text-text-secondary">{signal.copy}</p>
              </article>
            );
          })}
        </section>
      </main>
    </div>
  );
}
