'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Activity, Menu, Swords, X } from 'lucide-react';

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/recommend', label: 'Scan' },
  { href: '/decks', label: 'Meta' },
  { href: '/about', label: 'Model' },
];

const Navbar = () => {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="bg-gradient-navbar sticky top-0 z-50 border-b border-border-subtle">
      <div className="page-frame">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="group flex items-center gap-3" onClick={() => setMobileOpen(false)}>
            <div className="grid h-9 w-9 place-items-center rounded-[8px] border border-brand-gold/30 bg-gradient-card">
              <Swords className="h-5 w-5 text-brand-gold transition-transform group-hover:rotate-[-10deg]" />
            </div>
            <div className="leading-none">
              <div className="font-display text-lg font-bold text-text-primary">CR Deck Lab</div>
              <div className="font-display text-[0.63rem] uppercase tracking-[0.18em] text-text-muted">
                Meta intelligence
              </div>
            </div>
          </Link>

          <div className="hidden items-center gap-1 md:flex">
            {navLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-[8px] px-3.5 py-2 text-sm font-medium transition-colors ${
                    active
                      ? 'bg-surface-elevated text-text-primary'
                      : 'text-text-secondary hover:bg-surface-card-hover hover:text-text-primary'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
            <Link href="/recommend" className="btn-primary ml-3 px-4 text-sm">
              <Activity className="h-4 w-4" />
              Run Scan
            </Link>
          </div>

          <button
            type="button"
            onClick={() => setMobileOpen((open) => !open)}
            className="grid h-10 w-10 place-items-center rounded-[8px] border border-border-subtle text-text-secondary transition-colors hover:bg-surface-card-hover hover:text-text-primary md:hidden"
            aria-label="Toggle navigation"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="border-t border-border-subtle py-3 md:hidden">
            <div className="grid gap-1">
              {navLinks.map((link) => {
                const active = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`rounded-[8px] px-3 py-2.5 text-sm font-semibold transition-colors ${
                      active
                        ? 'bg-surface-elevated text-text-primary'
                        : 'text-text-secondary hover:bg-surface-card-hover hover:text-text-primary'
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
              <Link
                href="/recommend"
                onClick={() => setMobileOpen(false)}
                className="btn-primary mt-2 px-4 text-sm"
              >
                <Activity className="h-4 w-4" />
                Run Scan
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
