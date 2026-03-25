import Link from "next/link";
import Navbar from "../components/Navbar";
import { Swords, Sparkles, Shield, TrendingUp } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero section */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-hero opacity-20" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(230,57,70,0.15),transparent_60%)]" />

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-36">
          <div className="text-center max-w-3xl mx-auto animate-fade-in-up">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full
              bg-surface-card border border-border-subtle mb-8 text-sm text-text-secondary">
              <Sparkles className="h-4 w-4 text-brand-red" />
              Powered by Machine Learning
            </div>

            <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-6">
              <span className="text-gradient">Smarter Decks.</span>
              <br />
              <span className="text-text-primary">More Wins.</span>
            </h1>

            <p className="text-lg md:text-xl text-text-secondary mb-10 leading-relaxed max-w-2xl mx-auto">
              Enter your Supercell ID and get 3 personalized deck recommendations
              optimized for your card levels, trophy range, and play style.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/recommend" className="btn-primary text-lg !py-3.5 !px-10">
                Get Your Decks — Free
              </Link>
              <Link href="/about" className="btn-secondary text-lg !py-3.5 !px-10">
                How It Works
              </Link>
            </div>

            <p className="mt-5 text-sm text-text-muted">
              3 free recommendations · No login required
            </p>
          </div>
        </div>
      </section>

      {/* Features section */}
      <section className="relative py-24 bg-gradient-subtle">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16 animate-fade-in-up">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              <span className="text-gradient">How It Works</span>
            </h2>
            <p className="text-text-secondary text-lg max-w-xl mx-auto">
              Our hybrid ML model analyzes thousands of top-player matches
              to find the perfect decks for you.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="glass-card p-8 animate-fade-in-up-delay-1">
              <div className="w-12 h-12 rounded-xl bg-gradient-hero flex items-center justify-center mb-5">
                <Swords className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3">
                Enter Your Tag
              </h3>
              <p className="text-text-secondary leading-relaxed">
                Paste your Supercell player tag. We fetch your card levels,
                trophy count, and arena automatically via the official API.
              </p>
            </div>

            {/* Card 2 */}
            <div className="glass-card p-8 animate-fade-in-up-delay-2">
              <div className="w-12 h-12 rounded-xl bg-gradient-hero flex items-center justify-center mb-5">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3">
                AI Analyzes
              </h3>
              <p className="text-text-secondary leading-relaxed">
                Our hybrid model combines collaborative filtering, card synergy
                analysis, and win-rate data from thousands of top-ladder matches.
              </p>
            </div>

            {/* Card 3 */}
            <div className="glass-card p-8 animate-fade-in-up-delay-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-hero flex items-center justify-center mb-5">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-3">
                Get 3 Decks
              </h3>
              <p className="text-text-secondary leading-relaxed">
                Receive 3 optimized decks with detailed explanations — why each
                deck works, key synergies, and level advantage breakdowns.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats section */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="glass-card p-10 md:p-14 bg-gradient-card animate-pulse-glow">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl md:text-4xl font-black text-gradient mb-2">
                  110+
                </div>
                <div className="text-sm text-text-secondary font-medium">Cards Analyzed</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-black text-gradient mb-2">
                  5
                </div>
                <div className="text-sm text-text-secondary font-medium">Deck Archetypes</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-black text-gradient mb-2">
                  1000+
                </div>
                <div className="text-sm text-text-secondary font-medium">Meta Decks</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-black text-gradient mb-2">
                  Weekly
                </div>
                <div className="text-sm text-text-secondary font-medium">Model Updates</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA section */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-text-primary">
            Ready to climb the ladder?
          </h2>
          <p className="text-text-secondary text-lg mb-8 max-w-xl mx-auto">
            Get personalized recommendations tailored to your exact card collection.
          </p>
          <Link href="/recommend" className="btn-primary text-lg !py-3.5 !px-10">
            Get Started
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-subtle py-8 mt-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <Swords className="h-4 w-4 text-brand-red" />
            <span className="text-sm font-semibold text-text-secondary">CR Decks</span>
          </div>
          <p className="text-xs text-text-muted text-center">
            Not affiliated with Supercell. Clash Royale is a trademark of Supercell Oy.
          </p>
          <div className="flex gap-4 text-sm text-text-muted">
            <Link href="/about" className="hover:text-text-secondary transition-colors">About</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
