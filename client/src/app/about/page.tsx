import { CopySlash } from "lucide-react";
import Navbar from "../../components/Navbar";

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow p-8">
        <h1 className="text-3xl font-bold mb-4">About CR Decks</h1>
        <p>Your ultimate resource for Clash Royale deck building and strategies!</p>
      </main>
    </div>
  )
}