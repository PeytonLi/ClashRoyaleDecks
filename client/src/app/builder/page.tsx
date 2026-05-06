import Link from 'next/link';
import Navbar from '../../components/Navbar';
import { ChevronRight, Hammer, Layers3 } from 'lucide-react';

export default function BuilderPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="page-frame grid grow items-center gap-8 py-12 lg:grid-cols-[0.9fr_1.1fr]">
        <section>
          <div className="eyebrow mb-5">
            <Hammer className="h-4 w-4" />
            Builder preview
          </div>
          <h1 className="font-display text-4xl font-bold leading-tight text-text-primary md:text-6xl">
            Manual deck builder is on the roadmap.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-text-secondary">
            The current workflow starts from your player tag so the model can score real card levels. Manual card selection will build on the same scoring engine.
          </p>
          <Link href="/recommend" className="btn-primary mt-8 px-5">
            Use profile scan
            <ChevronRight className="h-5 w-5" />
          </Link>
        </section>

        <section className="arena-panel p-5">
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-[8px] bg-gradient-card">
              <Layers3 className="h-5 w-5 text-brand-gold" />
            </div>
            <div>
              <h2 className="font-display text-2xl font-bold text-text-primary">Builder module</h2>
              <p className="text-sm text-text-muted">Planned controls</p>
            </div>
          </div>

          <div className="grid gap-3">
            {['Card picker', 'Elixir curve', 'Archetype classification', 'Weakness analysis'].map((item) => (
              <div key={item} className="flex items-center justify-between border-b border-border-subtle py-3">
                <span className="font-semibold text-text-secondary">{item}</span>
                <span className="badge badge-control">Queued</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
