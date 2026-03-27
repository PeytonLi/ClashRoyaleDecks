import { CopySlash } from "lucide-react";
import Navbar from "../../components/Navbar";

export default function DecksPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="grow p-8">
        <h1 className="text-3xl font-bold mb-4">Popular Decks</h1>
        <p>Explore popular Clash Royale deck builds here!</p>
      </main>
    </div>
  )
}