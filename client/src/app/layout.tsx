import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CR Deck Lab - AI Clash Royale Deck Recommendations",
  description:
    "Get personalized Clash Royale deck recommendations powered by machine learning. Enter your player tag and receive 3 optimized decks based on your card levels, trophy range, and archetype preferences.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
