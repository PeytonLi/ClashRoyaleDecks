'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Swords, Menu, X } from 'lucide-react';

const Navbar = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/recommend', label: 'Get Decks' },
    { href: '/about', label: 'About' },
  ];

  return (
    <nav className="bg-gradient-navbar border-b border-border-subtle sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="p-1.5 rounded-lg bg-gradient-hero">
              <Swords className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-gradient">CR Decks</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary
                  hover:text-text-primary hover:bg-surface-card-hover transition-all duration-200"
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="/recommend"
              className="ml-3 btn-primary text-sm !py-2 !px-5"
            >
              Try Free
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary
              hover:bg-surface-card-hover transition-colors"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 border-t border-border-subtle mt-2 pt-3 animate-fade-in-up">
            <div className="flex flex-col gap-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-4 py-2.5 rounded-lg text-sm font-medium text-text-secondary
                    hover:text-text-primary hover:bg-surface-card-hover transition-all duration-200"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/recommend"
                onClick={() => setMobileOpen(false)}
                className="btn-primary text-sm text-center mt-2 !py-2.5"
              >
                Try Free
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;